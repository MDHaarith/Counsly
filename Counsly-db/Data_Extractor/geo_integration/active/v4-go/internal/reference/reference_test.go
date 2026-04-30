package reference

import (
	"testing"

	"college_locator_v4go/internal/config"
	"college_locator_v4go/internal/normalize"
	"college_locator_v4go/internal/types"
)

func testNormalizer() *normalize.Normalizer {
	return normalize.New(&config.NormalizationConfig{
		Abbreviations: map[string]string{
			"engg": "engineering",
			"inst": "institute",
			"arch": "architecture",
		},
		AliasReplacements: map[string]string{
			"&":            "and",
			"autonomous":   "",
			"(autonomous)": "",
		},
		TokenNoise: []string{"the", "of", "and", "for", "at", "by", "campus", "block", "division"},
		ManualQueryExpansions: map[string]string{
			"sap": "school of architecture and planning",
			"ceg": "college of engineering guindy",
		},
	})
}

func TestMatcherPrefersExactReferenceRecord(t *testing.T) {
	matcher := NewMatcher(testNormalizer(), []types.ReferenceCollege{
		{
			CollegeCode: "1",
			CollegeName: "University Departments of Anna University, Chennai - CEG Campus, Sardar Patel Road, Guindy, Chennai 600 025 1 2 2 University Departments of Anna University, Chennai - ACT Campus, Sardar Patel Road, Guindy, Chennai 600 025",
			Address:     "SARDAR PATEL ROAD, GUINDY, CHENNAI-600025",
			Pincode:     "600025",
			Website:     "https://ceg.annauniv.edu/",
			Suspect:     true,
		},
		{
			CollegeCode: "2",
			CollegeName: "University Departments of Anna University, Chennai - ACT Campus, Sardar Patel Road, Guindy, Chennai 600 025",
			Address:     "ALAGAPPA COLLEGE OF TECHNOLOGY, ANNA UNIVERSITY, SARDAR PATEL ROAD, GUINDY, CHENNAI",
			Pincode:     "600025",
			Website:     "https://www.annauniv.edu/act/",
		},
	})

	ref, match := matcher.Match(types.InputItem{
		Original: "University Departments of Anna University, Chennai - ACT Campus, Sardar Patel Road, Guindy, Chennai 600 025",
		Query:    "University Departments of Anna University, Chennai - ACT Campus, Sardar Patel Road, Guindy, Chennai 600 025",
	})

	if ref == nil {
		t.Fatal("expected an exact reference match")
	}
	if ref.CollegeCode != "2" {
		t.Fatalf("expected ACT record, got code %s", ref.CollegeCode)
	}
	if match == nil || match.Strategy != "exact" {
		t.Fatalf("expected exact strategy, got %#v", match)
	}
}

func TestMatcherRecoversSuspectConcatenatedReferenceRow(t *testing.T) {
	matcher := NewMatcher(testNormalizer(), []types.ReferenceCollege{
		{
			CollegeCode: "1",
			CollegeName: "University Departments of Anna University, Chennai - CEG Campus, Sardar Patel Road, Guindy, Chennai 600 025 1 2 2 University Departments of Anna University, Chennai - ACT Campus, Sardar Patel Road, Guindy, Chennai 600 025",
			Address:     "SARDAR PATEL ROAD, GUINDY, CHENNAI-600025",
			Pincode:     "600025",
			Website:     "https://ceg.annauniv.edu/",
			Suspect:     true,
		},
		{
			CollegeCode: "2",
			CollegeName: "University Departments of Anna University, Chennai - ACT Campus, Sardar Patel Road, Guindy, Chennai 600 025",
			Address:     "ALAGAPPA COLLEGE OF TECHNOLOGY, ANNA UNIVERSITY, SARDAR PATEL ROAD, GUINDY, CHENNAI",
			Pincode:     "600025",
			Website:     "https://www.annauniv.edu/act/",
		},
	})

	ref, match := matcher.Match(types.InputItem{
		Original: "University Departments of Anna University, Chennai - CEG Campus, Sardar Patel Road, Guindy, Chennai 600 025",
		Query:    "University Departments of Anna University, Chennai - CEG Campus, Sardar Patel Road, Guindy, Chennai 600 025",
	})

	if ref == nil {
		t.Fatal("expected a fuzzy reference match for the concatenated CEG row")
	}
	if ref.CollegeCode != "1" {
		t.Fatalf("expected CEG record, got code %s", ref.CollegeCode)
	}
	if match == nil || match.Score < 0.8 {
		t.Fatalf("expected a strong fuzzy match, got %#v", match)
	}
}
