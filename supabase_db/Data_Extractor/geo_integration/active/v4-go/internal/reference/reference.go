package reference

import (
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"

	"college_locator_v4go/internal/normalize"
	"college_locator_v4go/internal/types"
)

var (
	pincodeRe   = regexp.MustCompile(`\b\d{3}\s?\d{3}\b`)
	hasLetterRe = regexp.MustCompile(`[A-Za-z]`)
)

type rawCollege struct {
	CollegeCode any    `json:"College_Code"`
	CollegeName string `json:"College_Name"`
	Address     string `json:"Address"`
	Taluk       string `json:"Taluk"`
	District    string `json:"District"`
	Pincode     any    `json:"Pincode"`
	Website     string `json:"Website"`
}

type Matcher struct {
	normalizer *normalize.Normalizer
	references []types.ReferenceCollege
	exact      map[string][]int
}

func Load(path string) ([]types.ReferenceCollege, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var raw []rawCollege
	if err := json.NewDecoder(file).Decode(&raw); err != nil {
		return nil, err
	}

	references := make([]types.ReferenceCollege, 0, len(raw))
	for _, item := range raw {
		ref := types.ReferenceCollege{
			CollegeCode: compactSpaces(normalizeScalar(item.CollegeCode)),
			CollegeName: compactSpaces(item.CollegeName),
			Address:     compactSpaces(item.Address),
			Taluk:       cleanLocation(item.Taluk),
			District:    cleanLocation(item.District),
			Pincode:     extractPincode(normalizeScalar(item.Pincode), item.Address, item.CollegeName),
			Website:     compactSpaces(item.Website),
		}
		if ref.CollegeName == "" && ref.Address == "" {
			continue
		}
		ref.Suspect = isSuspiciousReference(ref)
		references = append(references, ref)
	}

	return references, nil
}

func NewMatcher(normalizer *normalize.Normalizer, references []types.ReferenceCollege) *Matcher {
	cloned := make([]types.ReferenceCollege, len(references))
	copy(cloned, references)

	exact := map[string][]int{}
	for idx := range cloned {
		cloned[idx].NameKey = normalizer.NormalizeKey(cloned[idx].CollegeName)
		if cloned[idx].NameKey == "" {
			continue
		}
		exact[cloned[idx].NameKey] = append(exact[cloned[idx].NameKey], idx)
	}

	return &Matcher{
		normalizer: normalizer,
		references: cloned,
		exact:      exact,
	}
}

func (m *Matcher) Attach(items []types.InputItem) []types.InputItem {
	out := make([]types.InputItem, len(items))
	copy(out, items)
	for idx := range out {
		ref, match := m.Match(out[idx])
		out[idx].Reference = ref
		out[idx].ReferenceMatch = match
	}
	return out
}

func (m *Matcher) Match(item types.InputItem) (*types.ReferenceCollege, *types.ReferenceMatch) {
	query := strings.TrimSpace(item.Original)
	if query == "" {
		query = strings.TrimSpace(item.Query)
	}
	if query == "" {
		return nil, nil
	}

	key := m.normalizer.NormalizeKey(query)
	if key == "" {
		return nil, nil
	}

	if matches := m.exact[key]; len(matches) > 0 {
		best := matches[0]
		for _, idx := range matches[1:] {
			if referenceQuality(m.references[idx]) > referenceQuality(m.references[best]) {
				best = idx
			}
		}
		ref := m.references[best]
		return &ref, &types.ReferenceMatch{Strategy: "exact", Score: 1}
	}

	queryTokens := tokenSet(m.normalizer.Tokenize(m.normalizer.NormalizeText(query)))
	queryImportant := importantTokens(queryTokens)
	if len(queryImportant) == 0 {
		queryImportant = queryTokens
	}

	bestScore := 0.0
	bestStrategy := ""
	bestIdx := -1

	for idx, ref := range m.references {
		if ref.NameKey == "" {
			continue
		}

		refTokens := tokenSet(m.normalizer.Tokenize(m.normalizer.NormalizeText(ref.CollegeName)))
		refImportant := importantTokens(refTokens)
		if len(refImportant) == 0 {
			refImportant = refTokens
		}

		importantOverlap := overlapRatio(queryImportant, refImportant)
		rawOverlap := overlapRatio(queryTokens, refTokens)
		score := 0.70*importantOverlap + 0.20*rawOverlap
		strategy := "overlap"

		if strings.Contains(ref.NameKey, key) || strings.Contains(key, ref.NameKey) {
			score += 0.10
			strategy = "contains"
		}
		if ref.Pincode != "" && strings.Contains(m.normalizer.NormalizeText(query), ref.Pincode) {
			score += 0.04
			strategy = "pincode_hint"
		}
		if ref.Suspect {
			score -= 0.03
		}

		if score > bestScore || (score == bestScore && bestIdx >= 0 && referenceQuality(ref) > referenceQuality(m.references[bestIdx])) {
			bestScore = score
			bestStrategy = strategy
			bestIdx = idx
		}
	}

	if bestIdx == -1 || bestScore < 0.74 {
		return nil, nil
	}

	ref := m.references[bestIdx]
	return &ref, &types.ReferenceMatch{Strategy: bestStrategy, Score: bestScore}
}

func compactSpaces(text string) string {
	return strings.Join(strings.Fields(strings.TrimSpace(text)), " ")
}

func normalizeScalar(value any) string {
	switch typed := value.(type) {
	case nil:
		return ""
	case string:
		return typed
	case float64:
		if typed == float64(int64(typed)) {
			return strconv.FormatInt(int64(typed), 10)
		}
		return fmt.Sprintf("%v", typed)
	default:
		return fmt.Sprintf("%v", typed)
	}
}

func cleanLocation(text string) string {
	text = compactSpaces(text)
	if text == "" {
		return ""
	}
	if !hasLetterRe.MatchString(text) {
		return ""
	}
	if pincodeRe.MatchString(text) && len(strings.Fields(text)) > 2 {
		return ""
	}
	if len(strings.Fields(text)) > 6 {
		return ""
	}
	return text
}

func extractPincode(values ...string) string {
	for _, value := range values {
		match := pincodeRe.FindString(value)
		if match == "" {
			continue
		}
		return strings.ReplaceAll(match, " ", "")
	}
	return ""
}

func isSuspiciousReference(ref types.ReferenceCollege) bool {
	lowerName := strings.ToLower(ref.CollegeName)
	if len(strings.Fields(ref.CollegeName)) > 40 {
		return true
	}
	if strings.Count(lowerName, " district ") > 1 {
		return true
	}
	if strings.Count(lowerName, " university college of engineering") > 2 {
		return true
	}
	return false
}

func referenceQuality(ref types.ReferenceCollege) int {
	score := 0
	if !ref.Suspect {
		score += 4
	}
	if ref.Address != "" {
		score += 2
	}
	if ref.Pincode != "" {
		score++
	}
	if ref.Website != "" {
		score++
	}
	return score
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

func importantTokens(tokens map[string]struct{}) map[string]struct{} {
	out := map[string]struct{}{}
	for token := range tokens {
		if len(token) < 2 {
			continue
		}
		switch token {
		case "college", "colleges", "school", "schools", "engineering", "technology", "technologies",
			"polytechnic", "architecture", "planning", "academy", "university", "universities",
			"institute", "institution", "institutions", "department", "departments", "faculty", "campus",
			"group", "groups", "educational", "trust", "trusts", "autonomous":
			continue
		}
		out[token] = struct{}{}
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
