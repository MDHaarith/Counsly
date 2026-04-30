package config

import (
	"encoding/json"
	"os"
)

// NormalizationConfig mirrors the Python JSON config.
type NormalizationConfig struct {
	Abbreviations         map[string]string `json:"abbreviations"`
	AliasReplacements     map[string]string `json:"alias_replacements"`
	TokenNoise            []string          `json:"token_noise"`
	ManualQueryExpansions map[string]string `json:"manual_query_expansions"`
}

type OverrideEntry struct {
	Original  string  `json:"original"`
	Query     string  `json:"query"`
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	MapsURL   string  `json:"maps_url"`
	PlaceID   string  `json:"place_id"`
	Source    string  `json:"source"`
	Note      string  `json:"note"`
	Disabled  bool    `json:"disabled"`
}

type ParentCampus struct {
	Name      string   `json:"name"`
	Latitude  float64  `json:"latitude"`
	Longitude float64  `json:"longitude"`
	MapsURL   string   `json:"maps_url"`
	PlaceID   string   `json:"place_id"`
	Aliases   []string `json:"aliases"`
	Locations []string `json:"locations"`
	Notes     string   `json:"notes"`
}

func loadJSON(path string, target any) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	dec := json.NewDecoder(f)
	return dec.Decode(target)
}

func LoadNormalizationConfig(path string) (*NormalizationConfig, error) {
	cfg := &NormalizationConfig{}
	if err := loadJSON(path, cfg); err != nil {
		return cfg, err
	}
	return cfg, nil
}

func LoadOverrideEntries(path string) (map[string]OverrideEntry, error) {
	entries := map[string]OverrideEntry{}
	if err := loadJSON(path, &entries); err != nil {
		return entries, err
	}
	return entries, nil
}

func LoadParentCampuses(path string) ([]ParentCampus, error) {
	entries := []ParentCampus{}
	if err := loadJSON(path, &entries); err != nil {
		return entries, err
	}
	return entries, nil
}
