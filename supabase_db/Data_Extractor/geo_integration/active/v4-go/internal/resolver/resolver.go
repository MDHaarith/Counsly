package resolver

import (
	"context"
	"fmt"
	"net/url"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	"college_locator_v4go/internal/config"
	"college_locator_v4go/internal/normalize"
	"college_locator_v4go/internal/scraper"
	"college_locator_v4go/internal/types"
)

var (
	districtRe = regexp.MustCompile(`(?i)([A-Za-z][A-Za-z .'-]{1,40}?)\s+District\b`)
	talukRe    = regexp.MustCompile(`(?i)([A-Za-z][A-Za-z .'-]{1,40}?)\s+Taluk\b`)
	pincodeRe  = regexp.MustCompile(`\b\d{3}\s?\d{3}\b`)
)

var locationNoise = map[string]struct{}{
	"iaf": {}, "nh": {}, "rs": {}, "bag": {}, "po": {}, "so": {}, "via": {}, "road": {}, "highway": {},
	"campus": {}, "village": {}, "post": {}, "district": {}, "taluk": {}, "near": {}, "opp": {}, "opposite": {},
}

var localityKeywordNoise = map[string]struct{}{
	"road": {}, "rd": {}, "highway": {}, "trunk": {}, "street": {}, "st": {}, "lane": {}, "nagar": {}, "temple": {},
	"junction": {}, "signal": {}, "campus": {}, "gate": {}, "building": {}, "block": {}, "phase": {}, "floor": {},
}

var entityNoise = map[string]struct{}{
	"college": {}, "colleges": {}, "school": {}, "schools": {}, "engineering": {}, "technology": {}, "technologies": {},
	"polytechnic": {}, "architecture": {}, "planning": {}, "academy": {}, "university": {}, "universities": {}, "institute": {},
	"institutions": {}, "institution": {}, "department": {}, "departments": {}, "faculty": {}, "campus": {}, "group": {},
	"groups": {}, "educational": {}, "trust": {}, "trusts": {}, "autonomous": {},
}

type locationHints struct {
	Cities       []string
	Districts    []string
	Taluks       []string
	Pincodes     []string
	LocalityText string
}

type CandidateReview struct {
	Candidate   scraper.Result
	Score       float64
	ExactMatch  bool
	Signals     map[string]any
	Reasons     []string
	Rejected    bool
	RejectCause string
}

type cacheReview struct {
	Key     string
	Entry   config.OverrideEntry
	Score   float64
	Signals map[string]any
	Reasons []string
}

type Resolver struct {
	normalizer  *normalize.Normalizer
	manual      map[string]config.OverrideEntry
	cache       map[string]config.OverrideEntry
	parents     []config.ParentCampus
	minScore    float64
	minMargin   float64
	maxVariants int
}

func New(
	normalizer *normalize.Normalizer,
	manual map[string]config.OverrideEntry,
	cache map[string]config.OverrideEntry,
	parents []config.ParentCampus,
	minScore float64,
	minMargin float64,
	maxVariants int,
) *Resolver {
	if minScore <= 0 {
		minScore = 0.62
	}
	if minMargin <= 0 {
		minMargin = 0.06
	}
	if maxVariants <= 0 {
		maxVariants = 8
	}
	return &Resolver{
		normalizer:  normalizer,
		manual:      manual,
		cache:       cache,
		parents:     parents,
		minScore:    minScore,
		minMargin:   minMargin,
		maxVariants: maxVariants,
	}
}

func (r *Resolver) Resolve(
	ctx context.Context,
	item types.InputItem,
	run func(context.Context, []string) ([]scraper.Result, error),
	timeout time.Duration,
) types.Result {
	if hit := r.lookupExact(item, r.manual, "manual_override", "manual"); hit != nil {
		return *hit
	}
	if hit := r.lookupExact(item, r.cache, "cached", "cache"); hit != nil {
		return *hit
	}
	if hit := r.lookupFuzzyCache(item); hit != nil {
		return *hit
	}

	queries := r.BuildQueries(item)
	if len(queries) == 0 {
		msg := "no query variants generated"
		return r.unresolvedResult(item, msg, nil, nil)
	}

	callCtx := ctx
	var cancel context.CancelFunc
	if timeout > 0 {
		callCtx, cancel = context.WithTimeout(ctx, timeout)
		defer cancel()
	}

	candidates, providerErr := run(callCtx, queries)
	reviewed := r.reviewCandidates(item, candidates)
	if chosen, accepted := r.pickBest(reviewed); accepted {
		return r.acceptedResult(item, chosen, providerErr)
	}

	if parent := r.parentFallback(item); parent != nil {
		if providerErr != nil && parent.Note == "" {
			parent.Note = fmt.Sprintf("provider error: %v", providerErr)
		}
		return *parent
	}

	msg := "no confident candidate match"
	if providerErr != nil && len(reviewed) == 0 {
		msg = fmt.Sprintf("provider error: %v", providerErr)
	}
	return r.unresolvedResult(item, msg, reviewed, providerErr)
}

func (r *Resolver) BuildQueries(item types.InputItem) []string {
	reviewQuery := r.reviewQuery(item)
	if reviewQuery == "" {
		return nil
	}

	cleaned := compactSpaces(reviewQuery)
	parts := splitParts(cleaned)
	first := cleaned
	if len(parts) > 0 {
		first = parts[0]
	}

	hints := r.extractLocationHints(item)
	localityParts := make([]string, 0, len(parts))
	for _, part := range parts[1:] {
		if compact := compactLocationPart(r.normalizer, part); compact != "" {
			localityParts = append(localityParts, compact)
		}
	}

	localityChain := strings.TrimSpace(strings.Join(take(localityParts, 4), " "))
	refLocalityChain := r.referenceLocalityChain(item)
	cityChain := strings.TrimSpace(strings.Join(take(hints.Cities, 3), " "))
	district := firstOrEmpty(hints.Districts)
	taluk := firstOrEmpty(hints.Taluks)
	pincode := firstOrEmpty(hints.Pincodes)

	queries := []string{cleaned}
	if len(parts) > 1 {
		queries = append(queries, strings.Join(parts[:min(3, len(parts))], ", "))
	}
	if localityChain != "" {
		queries = append(queries, fmt.Sprintf("%s %s", first, localityChain))
	}
	if refLocalityChain != "" {
		queries = append(queries, fmt.Sprintf("%s %s", first, refLocalityChain))
	}
	if cityChain != "" && pincode != "" {
		queries = append(queries, fmt.Sprintf("%s %s %s", first, cityChain, pincode))
	}
	if cityChain != "" {
		queries = append(queries, fmt.Sprintf("%s %s", first, cityChain))
	}
	if district != "" && pincode != "" {
		queries = append(queries, fmt.Sprintf("%s %s %s", first, district, pincode))
	}
	if district != "" {
		queries = append(queries, fmt.Sprintf("%s %s", first, district))
	}
	if taluk != "" && district != "" {
		queries = append(queries, fmt.Sprintf("%s %s %s", first, taluk, district))
	}
	if pincode != "" {
		queries = append(queries, fmt.Sprintf("%s %s", first, pincode))
	}
	if !strings.Contains(strings.ToLower(cleaned), "tamil nadu") {
		queries = append(queries, cleaned+", Tamil Nadu")
		if cityChain != "" {
			queries = append(queries, fmt.Sprintf("%s %s Tamil Nadu", first, cityChain))
		} else if district != "" {
			queries = append(queries, fmt.Sprintf("%s %s Tamil Nadu", first, district))
		}
	}

	seen := map[string]struct{}{}
	deduped := make([]string, 0, len(queries))
	for _, query := range queries {
		query = compactSpaces(query)
		if query == "" {
			continue
		}
		key := strings.ToLower(query)
		if _, ok := seen[key]; ok {
			continue
		}
		seen[key] = struct{}{}
		deduped = append(deduped, query)
		if len(deduped) >= r.maxVariants {
			break
		}
	}
	return deduped
}

func (r *Resolver) acceptedResult(item types.InputItem, chosen CandidateReview, providerErr error) types.Result {
	lat := chosen.Candidate.Latitude
	lng := chosen.Candidate.Longitude
	reasons := append([]string{}, chosen.Reasons...)
	if providerErr != nil {
		reasons = append(reasons, "provider_returned_partial_results")
	}
	note := fmt.Sprintf("score=%.3f; reasons=%s", chosen.Score, strings.Join(reasons, ", "))
	extras := map[string]any{
		"candidate": chosen.Candidate.Raw,
		"match": map[string]any{
			"score":       chosen.Score,
			"exact_match": chosen.ExactMatch,
			"reasons":     chosen.Reasons,
			"signals":     chosen.Signals,
		},
	}
	if ref := referencePayload(item); ref != nil {
		extras["reference"] = ref
	}
	return types.Result{
		Index:     item.Index,
		Original:  item.Original,
		Query:     r.reviewQuery(item),
		Latitude:  &lat,
		Longitude: &lng,
		MapsURL:   chosen.Candidate.Link,
		Status:    "ok",
		PlaceID:   chosen.Candidate.PlaceID,
		Source:    "gosom",
		Note:      note,
		Extras:    extras,
	}
}

func (r *Resolver) unresolvedResult(item types.InputItem, message string, reviewed []CandidateReview, providerErr error) types.Result {
	note := message
	if providerErr != nil && !strings.Contains(note, "provider error") {
		note = note + "; provider error: " + providerErr.Error()
	}

	extras := map[string]any{}
	if len(reviewed) > 0 {
		top := make([]map[string]any, 0, min(3, len(reviewed)))
		for _, candidate := range reviewed[:min(3, len(reviewed))] {
			top = append(top, map[string]any{
				"title":        candidate.Candidate.Title,
				"category":     candidate.Candidate.Category,
				"address":      candidate.Candidate.Address,
				"place_id":     candidate.Candidate.PlaceID,
				"maps_url":     candidate.Candidate.Link,
				"latitude":     candidate.Candidate.Latitude,
				"longitude":    candidate.Candidate.Longitude,
				"score":        candidate.Score,
				"reasons":      candidate.Reasons,
				"signals":      candidate.Signals,
				"rejected":     candidate.Rejected,
				"reject_cause": candidate.RejectCause,
			})
		}
		extras["candidates"] = top
	}
	if ref := referencePayload(item); ref != nil {
		extras["reference"] = ref
	}

	errMsg := note
	return types.Result{
		Index:    item.Index,
		Original: item.Original,
		Query:    r.reviewQuery(item),
		MapsURL:  "",
		Status:   "unresolved",
		Error:    &errMsg,
		Source:   "gosom",
		Note:     note,
		Extras:   extras,
	}
}

func (r *Resolver) lookupExact(item types.InputItem, source map[string]config.OverrideEntry, status string, resultSource string) *types.Result {
	for _, key := range r.lookupKeys(item) {
		entry, ok := source[key]
		if !ok || entry.Disabled {
			continue
		}
		lat := entry.Latitude
		lng := entry.Longitude
		note := entry.Note
		if note == "" {
			note = status
		}
		return &types.Result{
			Index:     item.Index,
			Original:  item.Original,
			Query:     entry.Query,
			Latitude:  &lat,
			Longitude: &lng,
			MapsURL:   entry.MapsURL,
			Status:    status,
			PlaceID:   entry.PlaceID,
			Source:    resultSource,
			Note:      note,
		}
	}
	return nil
}

func (r *Resolver) lookupFuzzyCache(item types.InputItem) *types.Result {
	if len(r.cache) == 0 {
		return nil
	}

	reviewed := make([]cacheReview, 0, len(r.cache))
	for key, entry := range r.cache {
		if entry.Disabled {
			continue
		}
		reviewed = append(reviewed, r.scoreCacheEntry(item, key, entry))
	}
	sort.Slice(reviewed, func(i, j int) bool {
		return reviewed[i].Score > reviewed[j].Score
	})
	if len(reviewed) == 0 {
		return nil
	}

	best := reviewed[0]
	margin := best.Score
	if len(reviewed) > 1 {
		margin = best.Score - reviewed[1].Score
	}
	if best.Score < 0.78 || (margin < 0.04 && best.Score < 0.90) {
		return nil
	}

	lat := best.Entry.Latitude
	lng := best.Entry.Longitude
	note := fmt.Sprintf("fuzzy_cache score=%.3f; reasons=%s", best.Score, strings.Join(best.Reasons, ", "))
	return &types.Result{
		Index:     item.Index,
		Original:  item.Original,
		Query:     best.Entry.Query,
		Latitude:  &lat,
		Longitude: &lng,
		MapsURL:   best.Entry.MapsURL,
		Status:    "cached_fuzzy",
		PlaceID:   best.Entry.PlaceID,
		Source:    "cache",
		Note:      note,
		Extras: map[string]any{
			"cache_match": map[string]any{
				"cache_key": best.Key,
				"score":     best.Score,
				"signals":   best.Signals,
				"reasons":   best.Reasons,
			},
			"reference": referencePayload(item),
		},
	}
}

func (r *Resolver) scoreCacheEntry(item types.InputItem, key string, entry config.OverrideEntry) cacheReview {
	cacheText := strings.TrimSpace(entry.Query)
	if cacheText == "" {
		cacheText = key
	}
	nameScore, exactMatch, nameReasons := r.nameScore(item.Original, cacheText)
	locationScore, locationReasons, locationSignals := r.textLocationScore(item, cacheText)
	typeScore, typeReasons, typeSignals := r.typeScoreText(item.Original, cacheText)

	score := clamp(nameScore+locationScore+typeScore, 0, 1)
	if exactMatch {
		score = clamp(score+0.04, 0, 1)
	}

	signals := map[string]any{
		"name_score":     nameScore,
		"location_score": locationScore,
		"type_score":     typeScore,
		"exact_match":    exactMatch,
		"cache_query":    cacheText,
	}
	for k, v := range locationSignals {
		signals[k] = v
	}
	for k, v := range typeSignals {
		signals[k] = v
	}

	reasons := append([]string{}, nameReasons...)
	reasons = append(reasons, locationReasons...)
	reasons = append(reasons, typeReasons...)

	return cacheReview{
		Key:     key,
		Entry:   entry,
		Score:   score,
		Signals: signals,
		Reasons: reasons,
	}
}

func (r *Resolver) parentFallback(item types.InputItem) *types.Result {
	if !isSubcampusLike(item.Original) {
		return nil
	}

	base := baseTokens(r.normalizer, item.Original)
	if len(base) == 0 {
		return nil
	}

	bestScore := 0.0
	var best *config.ParentCampus
	for idx := range r.parents {
		entry := &r.parents[idx]
		aliases := append([]string{entry.Name}, entry.Aliases...)
		for _, alias := range aliases {
			aliasTokens := tokenSet(strings.Fields(r.normalizer.NormalizeKey(alias)))
			overlap := overlapRatio(base, aliasTokens)
			score := overlap
			for _, loc := range entry.Locations {
				if strings.Contains(strings.ToLower(item.Original), strings.ToLower(loc)) {
					score += 0.1
					break
				}
			}
			if score >= 0.6 && score > bestScore {
				bestScore = score
				best = entry
			}
		}
	}

	if best == nil {
		return nil
	}

	lat := best.Latitude
	lng := best.Longitude
	note := best.Notes
	if note == "" {
		note = fmt.Sprintf("parent inferred via alias match score=%.2f", bestScore)
	}

	return &types.Result{
		Index:     item.Index,
		Original:  item.Original,
		Query:     r.reviewQuery(item),
		Latitude:  &lat,
		Longitude: &lng,
		MapsURL:   best.MapsURL,
		Status:    "parent_inferred",
		PlaceID:   best.PlaceID,
		Source:    "parent",
		Note:      note,
	}
}

func (r *Resolver) reviewCandidates(item types.InputItem, candidates []scraper.Result) []CandidateReview {
	deduped := dedupeCandidates(candidates)
	reviewed := make([]CandidateReview, 0, len(deduped))
	for _, candidate := range deduped {
		reviewed = append(reviewed, r.scoreCandidate(item, candidate))
	}
	sort.Slice(reviewed, func(i, j int) bool {
		if reviewed[i].Score == reviewed[j].Score {
			return reviewed[i].Candidate.ReviewsCount > reviewed[j].Candidate.ReviewsCount
		}
		return reviewed[i].Score > reviewed[j].Score
	})
	return reviewed
}

func (r *Resolver) pickBest(reviewed []CandidateReview) (CandidateReview, bool) {
	if len(reviewed) == 0 {
		return CandidateReview{}, false
	}

	best := reviewed[0]
	if best.Rejected {
		return best, false
	}

	margin := best.Score
	if len(reviewed) > 1 {
		margin = best.Score - reviewed[1].Score
	}

	if best.ExactMatch && best.Score >= r.minScore-0.05 {
		return best, true
	}
	if best.Score >= r.minScore && (margin >= r.minMargin || best.Score >= 0.82) {
		return best, true
	}
	return best, false
}

func (r *Resolver) scoreCandidate(item types.InputItem, candidate scraper.Result) CandidateReview {
	signals := map[string]any{
		"reviews_count": candidate.ReviewsCount,
		"category":      candidate.Category,
	}
	reasons := []string{}

	if candidate.Latitude == 0 && candidate.Longitude == 0 {
		return CandidateReview{
			Candidate:   candidate,
			Score:       0,
			Signals:     signals,
			Reasons:     append(reasons, "missing_coordinates"),
			Rejected:    true,
			RejectCause: "missing_coordinates",
		}
	}
	if !withinIndia(candidate.Latitude, candidate.Longitude) {
		return CandidateReview{
			Candidate:   candidate,
			Score:       0,
			Signals:     signals,
			Reasons:     append(reasons, "outside_india"),
			Rejected:    true,
			RejectCause: "outside_india",
		}
	}
	if !withinTamilNadu(candidate.Latitude, candidate.Longitude) {
		return CandidateReview{
			Candidate:   candidate,
			Score:       0,
			Signals:     signals,
			Reasons:     append(reasons, "outside_tamil_nadu"),
			Rejected:    true,
			RejectCause: "outside_tamil_nadu",
		}
	}

	nameScore, exactMatch, nameReasons := r.nameScore(item.Original, candidate.Title)
	reasons = append(reasons, nameReasons...)
	signals["name_score"] = nameScore
	signals["exact_match"] = exactMatch

	locationScore, locationReasons, locationSignals := r.locationScore(item, candidate)
	reasons = append(reasons, locationReasons...)
	for k, v := range locationSignals {
		signals[k] = v
	}

	referenceScore, referenceReasons, referenceSignals := r.referenceScore(item, candidate)
	reasons = append(reasons, referenceReasons...)
	for k, v := range referenceSignals {
		signals[k] = v
	}

	typeScore, typeReasons, typeSignals := r.typeScore(item.Original, candidate)
	reasons = append(reasons, typeReasons...)
	for k, v := range typeSignals {
		signals[k] = v
	}

	reviewSignal := 0.0
	if candidate.ReviewsCount >= 100 {
		reviewSignal = 0.02
		reasons = append(reasons, "review_count_bonus")
	}

	total := clamp(nameScore+locationScore+referenceScore+typeScore+reviewSignal, 0, 1)
	return CandidateReview{
		Candidate:  candidate,
		Score:      total,
		ExactMatch: exactMatch,
		Signals:    signals,
		Reasons:    reasons,
	}
}

func (r *Resolver) nameScore(original string, title string) (float64, bool, []string) {
	origTokens := tokenSet(r.normalizer.Tokenize(r.normalizer.NormalizeText(original)))
	titleTokens := tokenSet(r.normalizer.Tokenize(r.normalizer.NormalizeText(title)))
	if len(titleTokens) == 0 {
		return 0, false, []string{"missing_candidate_title"}
	}

	origImportant := importantTokens(origTokens)
	titleImportant := importantTokens(titleTokens)
	if len(origImportant) == 0 {
		origImportant = origTokens
	}
	if len(titleImportant) == 0 {
		titleImportant = titleTokens
	}

	importantOverlap := overlapRatio(origImportant, titleImportant)
	rawOverlap := overlapRatio(origTokens, titleTokens)
	exact := r.normalizer.NormalizeKey(original) == r.normalizer.NormalizeKey(title)
	contains := strings.Contains(r.normalizer.NormalizeKey(title), r.normalizer.NormalizeKey(original))

	score := 0.58*importantOverlap + 0.22*rawOverlap
	reasons := []string{
		fmt.Sprintf("important_overlap=%.2f", importantOverlap),
		fmt.Sprintf("raw_overlap=%.2f", rawOverlap),
	}
	if exact {
		score += 0.18
		reasons = append(reasons, "exact_normalized_match")
	}
	if contains && !exact {
		score += 0.08
		reasons = append(reasons, "title_contains_query")
	}

	return clamp(score, 0, 1), exact, reasons
}

func (r *Resolver) locationScore(item types.InputItem, candidate scraper.Result) (float64, []string, map[string]any) {
	hints := r.extractLocationHints(item)
	addressText := strings.ToLower(candidateAddressText(candidate))
	addressTokens := tokenSet(r.normalizer.Tokenize(r.normalizer.NormalizeText(addressText)))
	candidatePincodes := extractPincodes(addressText)

	score := 0.0
	reasons := []string{}
	signals := map[string]any{}
	matches := 0

	if len(hints.Pincodes) > 0 {
		match := false
		for _, code := range hints.Pincodes {
			if containsValue(candidatePincodes, code) {
				score += 0.18
				match = true
				matches++
				reasons = append(reasons, "pincode_match")
				break
			}
		}
		signals["pincode_match"] = match
	}

	if len(hints.Cities) > 0 {
		for _, city := range hints.Cities {
			if containsNormalizedPhrase(r.normalizer, addressText, city) {
				score += 0.08
				matches++
				reasons = append(reasons, "city_match")
				signals["city_match"] = city
				break
			}
		}
	}

	if len(hints.Districts) > 0 {
		for _, district := range hints.Districts {
			if containsNormalizedPhrase(r.normalizer, addressText, district) {
				score += 0.08
				matches++
				reasons = append(reasons, "district_match")
				signals["district_match"] = district
				break
			}
		}
	}

	if len(hints.Taluks) > 0 {
		for _, taluk := range hints.Taluks {
			if containsNormalizedPhrase(r.normalizer, addressText, taluk) {
				score += 0.05
				matches++
				reasons = append(reasons, "taluk_match")
				signals["taluk_match"] = taluk
				break
			}
		}
	}

	localityTokens := tokenSet(r.normalizer.Tokenize(r.normalizer.NormalizeText(hints.LocalityText)))
	for token := range localityTokens {
		if _, noisy := locationNoise[token]; noisy {
			delete(localityTokens, token)
			continue
		}
		if _, noisy := localityKeywordNoise[token]; noisy {
			delete(localityTokens, token)
			continue
		}
	}
	localityOverlap := overlapRatio(localityTokens, addressTokens)
	if localityOverlap > 0 {
		bonus := minFloat(0.12, 0.12*localityOverlap)
		score += bonus
		reasons = append(reasons, fmt.Sprintf("locality_overlap=%.2f", localityOverlap))
		signals["locality_overlap"] = localityOverlap
		matches++
	}

	if hasAnyLocationHints(hints) && matches == 0 {
		score -= 0.05
		reasons = append(reasons, "no_location_evidence")
	}

	signals["address"] = candidate.Address
	signals["location_score"] = score
	return score, reasons, signals
}

func (r *Resolver) textLocationScore(item types.InputItem, text string) (float64, []string, map[string]any) {
	hints := r.extractLocationHints(item)
	normalizedText := strings.ToLower(strings.TrimSpace(text))
	textTokens := tokenSet(r.normalizer.Tokenize(r.normalizer.NormalizeText(normalizedText)))
	textPincodes := extractPincodes(normalizedText)

	score := 0.0
	reasons := []string{}
	signals := map[string]any{}
	matches := 0

	if len(hints.Pincodes) > 0 {
		match := false
		for _, code := range hints.Pincodes {
			if containsValue(textPincodes, code) {
				score += 0.18
				match = true
				matches++
				reasons = append(reasons, "pincode_match")
				break
			}
		}
		signals["pincode_match"] = match
	}

	if len(hints.Cities) > 0 {
		for _, city := range hints.Cities {
			if containsNormalizedPhrase(r.normalizer, normalizedText, city) {
				score += 0.08
				matches++
				reasons = append(reasons, "city_match")
				signals["city_match"] = city
				break
			}
		}
	}

	if len(hints.Districts) > 0 {
		for _, district := range hints.Districts {
			if containsNormalizedPhrase(r.normalizer, normalizedText, district) {
				score += 0.08
				matches++
				reasons = append(reasons, "district_match")
				signals["district_match"] = district
				break
			}
		}
	}

	if len(hints.Taluks) > 0 {
		for _, taluk := range hints.Taluks {
			if containsNormalizedPhrase(r.normalizer, normalizedText, taluk) {
				score += 0.05
				matches++
				reasons = append(reasons, "taluk_match")
				signals["taluk_match"] = taluk
				break
			}
		}
	}

	localityTokens := tokenSet(r.normalizer.Tokenize(r.normalizer.NormalizeText(hints.LocalityText)))
	for token := range localityTokens {
		if _, noisy := locationNoise[token]; noisy {
			delete(localityTokens, token)
			continue
		}
		if _, noisy := localityKeywordNoise[token]; noisy {
			delete(localityTokens, token)
			continue
		}
	}
	localityOverlap := overlapRatio(localityTokens, textTokens)
	if localityOverlap > 0 {
		bonus := minFloat(0.12, 0.12*localityOverlap)
		score += bonus
		reasons = append(reasons, fmt.Sprintf("locality_overlap=%.2f", localityOverlap))
		signals["locality_overlap"] = localityOverlap
		matches++
	}

	if hasAnyLocationHints(hints) && matches == 0 {
		score -= 0.05
		reasons = append(reasons, "no_location_evidence")
	}

	signals["location_score"] = score
	return score, reasons, signals
}

func (r *Resolver) referenceScore(item types.InputItem, candidate scraper.Result) (float64, []string, map[string]any) {
	if item.Reference == nil {
		return 0, nil, map[string]any{}
	}

	ref := item.Reference
	addressText := strings.ToLower(candidateAddressText(candidate))
	addressTokens := tokenSet(r.normalizer.Tokenize(r.normalizer.NormalizeText(addressText)))
	refLocality := referenceLocalityTokens(r.normalizer, ref)
	refHost := normalizeWebsiteHost(ref.Website)
	candidateHost := normalizeWebsiteHost(candidate.Website)
	candidatePincodes := extractPincodes(addressText)

	score := 0.0
	reasons := []string{}
	signals := map[string]any{
		"reference_college_code": ref.CollegeCode,
		"reference_name":         ref.CollegeName,
	}
	if item.ReferenceMatch != nil {
		signals["reference_match_strategy"] = item.ReferenceMatch.Strategy
		signals["reference_match_score"] = item.ReferenceMatch.Score
	}

	matchCount := 0

	if ref.Pincode != "" {
		signals["reference_pincode"] = ref.Pincode
		if containsValue(candidatePincodes, ref.Pincode) {
			score += 0.18
			matchCount++
			reasons = append(reasons, "reference_pincode_match")
		} else if len(candidatePincodes) > 0 {
			score -= 0.12
			reasons = append(reasons, "reference_pincode_mismatch")
		}
	}

	if ref.District != "" && containsNormalizedPhrase(r.normalizer, addressText, ref.District) {
		score += 0.10
		matchCount++
		reasons = append(reasons, "reference_district_match")
		signals["reference_district_match"] = ref.District
	}

	if ref.Taluk != "" && containsNormalizedPhrase(r.normalizer, addressText, ref.Taluk) {
		score += 0.07
		matchCount++
		reasons = append(reasons, "reference_taluk_match")
		signals["reference_taluk_match"] = ref.Taluk
	}

	localityOverlap := overlapRatio(refLocality, addressTokens)
	if localityOverlap > 0 {
		score += minFloat(0.16, 0.16*localityOverlap)
		matchCount++
		reasons = append(reasons, fmt.Sprintf("reference_locality_overlap=%.2f", localityOverlap))
		signals["reference_locality_overlap"] = localityOverlap
	} else if len(refLocality) > 0 && len(addressTokens) > 0 {
		score -= 0.05
		reasons = append(reasons, "reference_locality_missing")
	}

	if refHost != "" {
		signals["reference_website_host"] = refHost
		if sameWebsiteHost(refHost, candidateHost) {
			score += 0.10
			matchCount++
			reasons = append(reasons, "reference_website_match")
		} else if candidateHost != "" {
			score -= 0.08
			reasons = append(reasons, "reference_website_mismatch")
			signals["candidate_website_host"] = candidateHost
		}
	}

	if matchCount == 0 && hasReferenceSignals(ref) {
		signals["reference_signal_miss"] = true
	}
	signals["reference_score"] = score
	return score, reasons, signals
}

func (r *Resolver) typeScore(original string, candidate scraper.Result) (float64, []string, map[string]any) {
	candidateText := strings.Join([]string{
		candidate.Title,
		candidate.Category,
		strings.Join(candidate.Categories, " "),
		candidate.Address,
	}, " ")
	return r.typeScoreText(original, candidateText)
}

func (r *Resolver) typeScoreText(original string, candidateText string) (float64, []string, map[string]any) {
	originalText := r.normalizer.NormalizeText(original)
	candidateText = r.normalizer.NormalizeText(candidateText)

	score := 0.0
	reasons := []string{}
	signals := map[string]any{"candidate_type_text": candidateText}

	wantsArchitecture := strings.Contains(originalText, "architecture")
	wantsPolytechnic := strings.Contains(originalText, "polytechnic")
	wantsWomen := strings.Contains(originalText, "women")
	wantsEngineering := strings.Contains(originalText, "engineering") || strings.Contains(originalText, "technology")

	if wantsArchitecture {
		if strings.Contains(candidateText, "architecture") {
			score += 0.12
			reasons = append(reasons, "architecture_match")
		} else {
			score -= 0.22
			reasons = append(reasons, "architecture_missing")
		}
	}
	if wantsPolytechnic {
		if strings.Contains(candidateText, "polytechnic") {
			score += 0.12
			reasons = append(reasons, "polytechnic_match")
		} else {
			score -= 0.20
			reasons = append(reasons, "polytechnic_missing")
		}
	} else if strings.Contains(candidateText, "polytechnic") {
		score -= 0.14
		reasons = append(reasons, "unexpected_polytechnic")
	}
	if wantsEngineering {
		if strings.Contains(candidateText, "engineering") || strings.Contains(candidateText, "technology") || strings.Contains(candidateText, "engg") {
			score += 0.08
			reasons = append(reasons, "engineering_match")
		} else {
			score -= 0.16
			reasons = append(reasons, "engineering_missing")
		}
	}
	if strings.Contains(candidateText, "nursing") && !strings.Contains(originalText, "nursing") {
		score -= 0.22
		reasons = append(reasons, "unexpected_nursing")
	}
	if strings.Contains(candidateText, "arts and science") && !strings.Contains(originalText, "arts") {
		score -= 0.18
		reasons = append(reasons, "unexpected_arts_science")
	}
	if strings.Contains(candidateText, "pharmacy") && !strings.Contains(originalText, "pharmacy") {
		score -= 0.18
		reasons = append(reasons, "unexpected_pharmacy")
	}
	if strings.Contains(candidateText, "management") && !strings.Contains(originalText, "management") {
		score -= 0.14
		reasons = append(reasons, "unexpected_management")
	}
	if strings.Contains(candidateText, "hostel") && !strings.Contains(originalText, "hostel") {
		score -= 0.20
		reasons = append(reasons, "unexpected_hostel")
	}
	if strings.Contains(candidateText, "office") && !strings.Contains(originalText, "office") {
		score -= 0.16
		reasons = append(reasons, "unexpected_office")
	}
	if wantsWomen {
		if strings.Contains(candidateText, "women") {
			score += 0.05
			reasons = append(reasons, "women_match")
		}
	} else if strings.Contains(candidateText, "women") {
		score -= 0.12
		reasons = append(reasons, "unexpected_women")
	}

	signals["type_score"] = score
	return score, reasons, signals
}

func (r *Resolver) extractLocationHints(item types.InputItem) locationHints {
	query := r.reviewQuery(item)
	hints := locationHints{}

	for _, match := range districtRe.FindAllStringSubmatch(query, -1) {
		if len(match) > 1 {
			hints.Districts = appendUnique(hints.Districts, compactLocationPart(r.normalizer, match[1]))
		}
	}
	for _, match := range talukRe.FindAllStringSubmatch(query, -1) {
		if len(match) > 1 {
			hints.Taluks = appendUnique(hints.Taluks, compactLocationPart(r.normalizer, match[1]))
		}
	}
	for _, code := range pincodeRe.FindAllString(query, -1) {
		hints.Pincodes = appendUnique(hints.Pincodes, normalizePincode(code))
	}

	for _, part := range splitParts(query) {
		lower := strings.ToLower(part)
		if strings.Contains(lower, "district") || strings.Contains(lower, "taluk") {
			continue
		}
		withoutPin := pincodeRe.ReplaceAllString(part, " ")
		compact := compactLocationPart(r.normalizer, withoutPin)
		if compact != "" && !isBadLocalityFragment(r.normalizer, compact) {
			hints.Cities = appendUnique(hints.Cities, compact)
		}
	}

	if item.Reference != nil {
		if district := compactLocationPart(r.normalizer, item.Reference.District); district != "" {
			hints.Districts = appendUnique(hints.Districts, district)
		}
		if taluk := compactLocationPart(r.normalizer, item.Reference.Taluk); taluk != "" {
			hints.Taluks = appendUnique(hints.Taluks, taluk)
		}
		if code := normalizePincode(item.Reference.Pincode); code != "" {
			hints.Pincodes = appendUnique(hints.Pincodes, code)
		}
		for _, part := range splitParts(item.Reference.Address) {
			withoutPin := pincodeRe.ReplaceAllString(part, " ")
			compact := compactLocationPart(r.normalizer, withoutPin)
			if compact != "" && !isBadLocalityFragment(r.normalizer, compact) {
				hints.Cities = appendUnique(hints.Cities, compact)
			}
		}
		if item.Reference.Address != "" {
			hints.LocalityText = r.normalizer.NormalizeLocation([]string{
				hints.LocalityText,
				item.Reference.Address,
				item.Reference.Taluk,
				item.Reference.District,
				item.Reference.Pincode,
			})
		}
	}

	if hints.LocalityText == "" {
		hints.LocalityText = query
	}
	return hints
}

func (r *Resolver) reviewQuery(item types.InputItem) string {
	parts := []string{strings.TrimSpace(item.Query)}
	if item.Original != "" && item.Original != item.Query {
		parts = append(parts, strings.TrimSpace(item.Original))
	}
	if raw, ok := item.Raw.(map[string]any); ok {
		for _, key := range []string{"city", "district", "state", "country", "address", "location", "pincode"} {
			value, ok := raw[key]
			if !ok {
				continue
			}
			switch v := value.(type) {
			case string:
				if strings.TrimSpace(v) != "" {
					parts = append(parts, strings.TrimSpace(v))
				}
			case float64:
				parts = append(parts, strconv.Itoa(int(v)))
			}
		}
	}
	return r.normalizer.NormalizeLocation(parts)
}

func (r *Resolver) lookupKeys(item types.InputItem) []string {
	query := r.reviewQuery(item)
	keys := []string{
		r.normalizer.NormalizeKey(query),
		legacyLookupKey(r.normalizer, query),
	}
	out := make([]string, 0, len(keys))
	seen := map[string]struct{}{}
	for _, key := range keys {
		key = compactSpaces(key)
		if key == "" {
			continue
		}
		if _, ok := seen[key]; ok {
			continue
		}
		seen[key] = struct{}{}
		out = append(out, key)
	}
	return out
}

func dedupeCandidates(candidates []scraper.Result) []scraper.Result {
	seen := map[string]struct{}{}
	deduped := make([]scraper.Result, 0, len(candidates))
	for _, candidate := range candidates {
		key := strings.Join([]string{
			strings.ToLower(strings.TrimSpace(candidate.PlaceID)),
			strings.ToLower(strings.TrimSpace(candidate.Title)),
			strings.ToLower(strings.TrimSpace(candidate.Address)),
			strings.ToLower(strings.TrimSpace(candidate.Phone)),
			strings.ToLower(strings.TrimSpace(candidate.Website)),
		}, "|")
		if key == "||||" {
			key = strings.ToLower(strings.TrimSpace(candidate.Title + "|" + candidate.Address))
		}
		if _, ok := seen[key]; ok {
			continue
		}
		seen[key] = struct{}{}
		deduped = append(deduped, candidate)
	}
	return deduped
}

func splitParts(text string) []string {
	parts := strings.Split(text, ",")
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		part = compactSpaces(part)
		if part != "" {
			out = append(out, part)
		}
	}
	return out
}

func compactSpaces(text string) string {
	return strings.Join(strings.Fields(strings.TrimSpace(text)), " ")
}

func compactLocationPart(normalizer *normalize.Normalizer, part string) string {
	tokens := normalizer.Tokenize(normalizer.NormalizeText(part))
	out := make([]string, 0, len(tokens))
	for _, token := range tokens {
		if _, ok := locationNoise[token]; ok {
			continue
		}
		if _, ok := localityKeywordNoise[token]; ok {
			continue
		}
		out = append(out, token)
	}
	return strings.Join(out, " ")
}

func legacyLookupKey(normalizer *normalize.Normalizer, text string) string {
	tokens := normalizer.Tokenize(normalizer.NormalizeText(text))
	out := make([]string, 0, len(tokens))
	for _, token := range tokens {
		if normalizer.IsNoise(token) {
			continue
		}
		out = append(out, token)
	}
	return strings.Join(out, " ")
}

func importantTokens(tokens map[string]struct{}) map[string]struct{} {
	out := map[string]struct{}{}
	for token := range tokens {
		if len(token) < 2 {
			continue
		}
		if _, noisy := entityNoise[token]; noisy {
			continue
		}
		if _, noisy := locationNoise[token]; noisy {
			continue
		}
		out[token] = struct{}{}
	}
	return out
}

func baseTokens(normalizer *normalize.Normalizer, text string) map[string]struct{} {
	out := map[string]struct{}{}
	for _, token := range normalizer.Tokenize(normalizer.NormalizeText(text)) {
		if len(token) < 3 {
			continue
		}
		if _, noisy := locationNoise[token]; noisy {
			continue
		}
		if _, noisy := localityKeywordNoise[token]; noisy {
			continue
		}
		if _, noisy := entityNoise[token]; noisy {
			continue
		}
		out[token] = struct{}{}
	}
	return out
}

func tokenSet(tokens []string) map[string]struct{} {
	out := make(map[string]struct{}, len(tokens))
	for _, token := range tokens {
		if token != "" {
			out[token] = struct{}{}
		}
	}
	return out
}

func overlapRatio(left map[string]struct{}, right map[string]struct{}) float64 {
	if len(left) == 0 || len(right) == 0 {
		return 0
	}
	common := 0
	for token := range left {
		if _, ok := right[token]; ok {
			common++
		}
	}
	return float64(common) / float64(len(left))
}

func containsNormalizedPhrase(normalizer *normalize.Normalizer, haystack string, needle string) bool {
	haystack = normalizer.NormalizeText(haystack)
	needle = normalizer.NormalizeText(needle)
	if needle == "" {
		return false
	}
	return strings.Contains(haystack, needle)
}

func flattenAddress(value map[string]any) string {
	if len(value) == 0 {
		return ""
	}
	parts := make([]string, 0, len(value))
	for _, key := range []string{"street", "borough", "city", "postal_code", "state", "country"} {
		if raw, ok := value[key]; ok {
			if s, ok := raw.(string); ok && strings.TrimSpace(s) != "" {
				parts = append(parts, s)
			}
		}
	}
	return strings.Join(parts, ", ")
}

func candidateAddressText(candidate scraper.Result) string {
	return strings.TrimSpace(strings.Join([]string{
		candidate.Address,
		flattenAddress(candidate.CompleteAddress),
		candidate.PlusCode,
	}, " "))
}

func referenceLocalityTokens(normalizer *normalize.Normalizer, ref *types.ReferenceCollege) map[string]struct{} {
	if ref == nil {
		return nil
	}
	parts := []string{ref.Address, ref.Taluk, ref.District}
	tokens := map[string]struct{}{}
	for _, part := range parts {
		compact := compactLocationPart(normalizer, part)
		for token := range tokenSet(normalizer.Tokenize(compact)) {
			if _, noisy := locationNoise[token]; noisy {
				continue
			}
			if _, noisy := localityKeywordNoise[token]; noisy {
				continue
			}
			tokens[token] = struct{}{}
		}
	}
	return tokens
}

func normalizeWebsiteHost(raw string) string {
	raw = strings.TrimSpace(strings.ToLower(raw))
	if raw == "" {
		return ""
	}
	if !strings.Contains(raw, "://") {
		raw = "https://" + raw
	}
	parsed, err := url.Parse(raw)
	if err != nil {
		return ""
	}
	host := strings.TrimPrefix(strings.ToLower(parsed.Hostname()), "www.")
	return host
}

func sameWebsiteHost(left string, right string) bool {
	if left == "" || right == "" {
		return false
	}
	return left == right || strings.HasSuffix(left, "."+right) || strings.HasSuffix(right, "."+left)
}

func extractPincodes(text string) []string {
	matches := pincodeRe.FindAllString(text, -1)
	out := make([]string, 0, len(matches))
	for _, match := range matches {
		out = appendUnique(out, normalizePincode(match))
	}
	return out
}

func normalizePincode(text string) string {
	return strings.ReplaceAll(compactSpaces(text), " ", "")
}

func containsValue(values []string, target string) bool {
	target = normalizePincode(target)
	for _, value := range values {
		if normalizePincode(value) == target {
			return true
		}
	}
	return false
}

func hasReferenceSignals(ref *types.ReferenceCollege) bool {
	if ref == nil {
		return false
	}
	return ref.Address != "" || ref.Taluk != "" || ref.District != "" || ref.Pincode != "" || ref.Website != ""
}

func referencePayload(item types.InputItem) map[string]any {
	if item.Reference == nil {
		return nil
	}
	payload := map[string]any{
		"college_code": item.Reference.CollegeCode,
		"college_name": item.Reference.CollegeName,
		"address":      item.Reference.Address,
		"taluk":        item.Reference.Taluk,
		"district":     item.Reference.District,
		"pincode":      item.Reference.Pincode,
		"website":      item.Reference.Website,
	}
	if item.ReferenceMatch != nil {
		payload["match_strategy"] = item.ReferenceMatch.Strategy
		payload["match_score"] = item.ReferenceMatch.Score
	}
	return payload
}

func (r *Resolver) referenceLocalityChain(item types.InputItem) string {
	refTokens := referenceLocalityTokens(r.normalizer, item.Reference)
	if len(refTokens) == 0 {
		return ""
	}
	ordered := make([]string, 0, len(refTokens))
	for _, part := range []string{item.Reference.Address, item.Reference.Taluk, item.Reference.District} {
		for _, token := range r.normalizer.Tokenize(compactLocationPart(r.normalizer, part)) {
			if _, ok := refTokens[token]; ok {
				ordered = appendUnique(ordered, token)
			}
		}
	}
	return strings.Join(take(ordered, 6), " ")
}

func hasAnyLocationHints(hints locationHints) bool {
	return len(hints.Cities) > 0 || len(hints.Districts) > 0 || len(hints.Taluks) > 0 || len(hints.Pincodes) > 0
}

func appendUnique(values []string, value string) []string {
	value = compactSpaces(value)
	if value == "" {
		return values
	}
	for _, existing := range values {
		if strings.EqualFold(existing, value) {
			return values
		}
	}
	return append(values, value)
}

func isSubcampusLike(text string) bool {
	lower := strings.ToLower(text)
	for _, hint := range []string{"architecture", "school", "department", "dept", "campus", "regional", "constituent", "extension", "university college", "uce"} {
		if strings.Contains(lower, hint) {
			return true
		}
	}
	return false
}

func isBadLocalityFragment(normalizer *normalize.Normalizer, part string) bool {
	cleaned := compactSpaces(part)
	if cleaned == "" {
		return true
	}
	tokens := normalizer.Tokenize(cleaned)
	if len(tokens) == 0 || len(tokens) > 5 {
		return true
	}
	first := tokens[0]
	if _, noisy := locationNoise[first]; noisy {
		return true
	}
	for _, token := range tokens {
		if _, noisy := localityKeywordNoise[token]; noisy {
			return true
		}
	}
	return false
}

func withinIndia(lat float64, lng float64) bool {
	return lat >= 6.0 && lat <= 38.5 && lng >= 68.0 && lng <= 97.5
}

func withinTamilNadu(lat float64, lng float64) bool {
	return lat >= 7.5 && lat <= 13.75 && lng >= 76.0 && lng <= 80.5
}

func clamp(value float64, minValue float64, maxValue float64) float64 {
	if value < minValue {
		return minValue
	}
	if value > maxValue {
		return maxValue
	}
	return value
}

func min(a int, b int) int {
	if a < b {
		return a
	}
	return b
}

func minFloat(a float64, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func firstOrEmpty(values []string) string {
	if len(values) == 0 {
		return ""
	}
	return values[0]
}

func take(values []string, count int) []string {
	if len(values) <= count {
		return values
	}
	return values[:count]
}
