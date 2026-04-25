package normalize

import (
	"regexp"
	"strings"

	"college_locator_v4go/internal/config"
)

type Normalizer struct {
	cfg   *config.NormalizationConfig
	noise map[string]struct{}
}

func New(cfg *config.NormalizationConfig) *Normalizer {
	noise := map[string]struct{}{}
	for _, t := range cfg.TokenNoise {
		noise[strings.ToLower(strings.TrimSpace(t))] = struct{}{}
	}
	return &Normalizer{cfg: cfg, noise: noise}
}

var (
	tokenRe = regexp.MustCompile(`[a-z0-9]+`)
)

func (n *Normalizer) Tokenize(text string) []string {
	return tokenRe.FindAllString(strings.ToLower(text), -1)
}

func (n *Normalizer) NormalizeText(text string) string {
	text = strings.ReplaceAll(text, "＜½", " ")
	text = strings.ReplaceAll(text, "&", " and ")
	text = strings.ReplaceAll(text, "/", " ")
	text = strings.ReplaceAll(text, "-", " ")
	text = strings.ReplaceAll(text, "'", " ")
	text = strings.ReplaceAll(text, "’", " ")
	text = strings.ReplaceAll(text, "`", " ")
	text = strings.ReplaceAll(text, "“", " ")
	text = strings.ReplaceAll(text, "”", " ")
	text = strings.ToLower(strings.TrimSpace(text))

	for alias, replacement := range n.cfg.AliasReplacements {
		pattern := regexp.MustCompile(`\b` + regexp.QuoteMeta(strings.ToLower(alias)) + `\b`)
		text = pattern.ReplaceAllString(text, strings.ToLower(replacement))
	}

	tokens := tokenRe.FindAllString(text, -1)
	expanded := make([]string, 0, len(tokens))
	for _, tok := range tokens {
		if rep, ok := n.cfg.ManualQueryExpansions[tok]; ok {
			expanded = append(expanded, tokenRe.FindAllString(strings.ToLower(rep), -1)...)
			continue
		}
		if rep, ok := n.cfg.Abbreviations[tok]; ok {
			expanded = append(expanded, tokenRe.FindAllString(strings.ToLower(rep), -1)...)
			continue
		}
		expanded = append(expanded, tok)
	}

	return strings.Join(expanded, " ")
}

func (n *Normalizer) NormalizeQuery(q string) string {
	clean := make([]string, 0, 16)
	seen := map[string]bool{}
	for _, tok := range strings.Fields(n.NormalizeText(q)) {
		if tok == "" {
			continue
		}
		if _, noisy := n.noise[tok]; noisy {
			continue
		}
		if seen[tok] {
			continue
		}
		seen[tok] = true
		clean = append(clean, tok)
	}
	return strings.Join(clean, " ")
}

func (n *Normalizer) NormalizeKey(text string) string {
	return n.NormalizeQuery(text)
}

func (n *Normalizer) IsNoise(token string) bool {
	_, ok := n.noise[strings.ToLower(strings.TrimSpace(token))]
	return ok
}

// NormalizeLocation joins non-empty location parts while preserving source order.
func (n *Normalizer) NormalizeLocation(parts []string) string {
	seen := map[string]struct{}{}
	uniq := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		lv := strings.ToLower(p)
		if _, ok := seen[lv]; ok {
			continue
		}
		seen[lv] = struct{}{}
		uniq = append(uniq, p)
	}
	return strings.Join(uniq, ", ")
}
