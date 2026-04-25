package resolver

import (
	"testing"

	"college_locator_v4go/internal/config"
	"college_locator_v4go/internal/normalize"
	"college_locator_v4go/internal/scraper"
	"college_locator_v4go/internal/types"
)

func testResolver() *Resolver {
	norm := normalize.New(&config.NormalizationConfig{
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
	return New(norm, nil, nil, []config.ParentCampus{
		{
			Name:      "Anna University, Chennai (Guindy Campus)",
			Latitude:  13.010793,
			Longitude: 80.235231,
			MapsURL:   "https://www.google.com/maps/place/Anna+University/@13.010793,80.235231,17z/",
			Aliases:   []string{"anna university chennai", "college of engineering guindy", "school of architecture and planning", "sap chennai"},
			Locations: []string{"chennai", "guindy"},
			Notes:     "Parent coordinates reused for SAP/CEG sub-entities when Maps is ambiguous.",
		},
	}, 0.62, 0.06, 8)
}

func TestReviewCandidatesPrefersExactEngineeringCollege(t *testing.T) {
	r := testResolver()
	item := types.InputItem{
		Index:    0,
		Original: "Hindusthan College of Engineering and Technology, Coimbatore, Tamil Nadu 641032",
		Query:    "Hindusthan College of Engineering and Technology, Coimbatore, Tamil Nadu 641032",
	}

	candidates := []scraper.Result{
		{
			Title:     "Hindusthan Institute of Technology",
			Category:  "College",
			Address:   "NH 83, Malumichampatti, Tamil Nadu 641032",
			Latitude:  10.8945458,
			Longitude: 76.9970671,
			PlaceID:   "pid-hit",
		},
		{
			Title:     "HINDUSTHAN COLLEGE OF ENGINEERING AND TECHNOLOGY",
			Category:  "Educational institution",
			Address:   "Pollachi Main Rd, Coimbatore, Malumichampatti, Tamil Nadu 641032",
			Latitude:  10.8914786,
			Longitude: 76.9907974,
			PlaceID:   "pid-hcet",
		},
		{
			Title:     "Hindusthan Polytechnic College",
			Category:  "Polytechnic College",
			Address:   "Pollachi Main Rd, Ottakkalmandapam, Malumichampatti, Tamil Nadu 641032",
			Latitude:  10.8914068,
			Longitude: 76.9956858,
			PlaceID:   "pid-poly",
		},
	}

	reviewed := r.reviewCandidates(item, candidates)
	if len(reviewed) != 3 {
		t.Fatalf("expected 3 reviewed candidates, got %d", len(reviewed))
	}
	if reviewed[0].Candidate.PlaceID != "pid-hcet" {
		t.Fatalf("expected engineering college to rank first, got %s", reviewed[0].Candidate.Title)
	}
}

func TestReviewCandidatesPenalizesPolytechnicForEngineeringQuery(t *testing.T) {
	r := testResolver()
	item := types.InputItem{
		Index:    0,
		Original: "Shree Venkateshwara Hi-Tech Engineering College, Gobichettipalayam, Tamil Nadu 638455",
		Query:    "Shree Venkateshwara Hi-Tech Engineering College, Gobichettipalayam, Tamil Nadu 638455",
	}

	candidates := []scraper.Result{
		{
			Title:     "Shree Venkateshwara Hi-Tech Engineering College",
			Category:  "Educational institution",
			Address:   "Gobi Main Rd, Sri Kalaivani Nagar, Tamil Nadu 638455",
			Latitude:  11.4405043,
			Longitude: 77.5050635,
			PlaceID:   "pid-eng",
		},
		{
			Title:     "Shree Venkateshwara Hi-Tech Polytechnic College",
			Category:  "Polytechnic College",
			Address:   "Erode-Gobi Main Road, Tamil Nadu 638455",
			Latitude:  11.4410983,
			Longitude: 77.4986900,
			PlaceID:   "pid-poly",
		},
	}

	reviewed := r.reviewCandidates(item, candidates)
	if reviewed[0].Candidate.PlaceID != "pid-eng" {
		t.Fatalf("expected engineering candidate to rank first, got %s", reviewed[0].Candidate.Title)
	}
	if reviewed[0].Score <= reviewed[1].Score {
		t.Fatalf("expected engineering candidate score %.3f to exceed polytechnic %.3f", reviewed[0].Score, reviewed[1].Score)
	}
}

func TestParentFallbackForAnnaUniversitySubcampus(t *testing.T) {
	r := testResolver()
	item := types.InputItem{
		Index:    0,
		Original: "School of Architecture and Planning, Anna University, Chennai 600025",
		Query:    "School of Architecture and Planning, Anna University, Chennai 600025",
	}

	parent := r.parentFallback(item)
	if parent == nil {
		t.Fatal("expected parent fallback for SAP")
	}
	if parent.Status != "parent_inferred" {
		t.Fatalf("expected parent_inferred status, got %s", parent.Status)
	}
	if parent.Latitude == nil || parent.Longitude == nil {
		t.Fatal("expected parent fallback coordinates")
	}
}

func TestReviewCandidatesUsesReferenceSignalsToBreakDuplicateTie(t *testing.T) {
	r := testResolver()
	item := types.InputItem{
		Index:    0,
		Original: "Prince Shri Venkateshwara Padmavathy Engineering College",
		Query:    "Prince Shri Venkateshwara Padmavathy Engineering College",
		Reference: &types.ReferenceCollege{
			CollegeCode: "1414",
			CollegeName: "Prince Shri Venkateshwara Padmavathy Engineering College, Ponmar, Chennai 600048",
			Address:     "MEDAVAKKAM - MAMBAKKAM ROAD, PONMAR",
			Taluk:       "VANDALUR",
			District:    "CHENGALPATTU",
			Pincode:     "600127",
			Website:     "www.psvpec.in",
		},
		ReferenceMatch: &types.ReferenceMatch{Strategy: "exact", Score: 1},
	}

	candidates := []scraper.Result{
		{
			Title:     "Prince Shri Venkateshwara Padmavathy Engineering College",
			Category:  "Educational institution",
			Address:   "Medavakkam - Mambakkam Rd, Ponmar, Tamil Nadu 600127",
			Website:   "https://www.psvpec.in/",
			Latitude:  12.847564,
			Longitude: 80.172311,
			PlaceID:   "pid-psvpec",
		},
		{
			Title:     "Prince Shri Venkateshwara Padmavathy Engineering College",
			Category:  "Educational institution",
			Address:   "Velachery Main Rd, Chennai, Tamil Nadu 600100",
			Website:   "https://www.princecolleges.net/",
			Latitude:  12.932190,
			Longitude: 80.182701,
			PlaceID:   "pid-wrong-branch",
		},
	}

	reviewed := r.reviewCandidates(item, candidates)
	if reviewed[0].Candidate.PlaceID != "pid-psvpec" {
		t.Fatalf("expected reference-aligned campus to rank first, got %s", reviewed[0].Candidate.PlaceID)
	}
	if reviewed[0].Score <= reviewed[1].Score {
		t.Fatalf("expected reference signals to separate duplicate campus matches: %.3f <= %.3f", reviewed[0].Score, reviewed[1].Score)
	}
}

func TestLookupExactFallsBackToLegacyCacheKey(t *testing.T) {
	r := testResolver()
	cache := map[string]config.OverrideEntry{
		"university departments anna university chennai act sardar patel road guindy chennai 600 025": {
			Query:     "university departments of anna university chennai act campus sardar patel road guindy chennai 600 025",
			Latitude:  13.007925,
			Longitude: 80.2387098,
			MapsURL:   "https://maps.example/act",
			PlaceID:   "pid-act",
		},
	}
	r.cache = cache

	item := types.InputItem{
		Index:    0,
		Original: "University Departments of Anna University, Chennai - ACT Campus, Sardar Patel Road, Guindy, Chennai 600 025",
		Query:    "University Departments of Anna University, Chennai - ACT Campus, Sardar Patel Road, Guindy, Chennai 600 025",
	}

	hit := r.lookupExact(item, r.cache, "cached", "cache")
	if hit == nil {
		t.Fatal("expected legacy cache key fallback to resolve ACT campus")
	}
	if hit.PlaceID != "pid-act" {
		t.Fatalf("expected ACT cache hit, got %s", hit.PlaceID)
	}
}

func TestLookupFuzzyCacheUsesReferenceSignals(t *testing.T) {
	r := testResolver()
	r.cache = map[string]config.OverrideEntry{
		"vel technology multi technology dr rangarajan dr sakunthala engineering college avadi alamathi road chennai 600 062": {
			Query:     "vel technology multi technology dr rangarajan dr sakunthala engineering college avadi alamathi road chennai 600 062",
			Latitude:  13.1913142,
			Longitude: 80.1125469,
			MapsURL:   "https://maps.example/vel-tech-multi",
			PlaceID:   "pid-multi",
		},
		"vel technology high technology dr rangarajan dr sakunthala engineering college avadi alamathi road chennai 600 062": {
			Query:     "vel technology high technology dr rangarajan dr sakunthala engineering college avadi alamathi road chennai 600 062",
			Latitude:  13.1900041,
			Longitude: 80.1139482,
			MapsURL:   "https://maps.example/vel-tech-high",
			PlaceID:   "pid-high",
		},
	}

	item := types.InputItem{
		Index:    0,
		Original: "Vel Tech Multi Tech Dr. Rangarajan Dr. Sakunthala Engineering College (Autonomous), Avadi-Alamathi Road, Chennai 600 062",
		Query:    "Vel Tech Multi Tech Dr. Rangarajan Dr. Sakunthala Engineering College (Autonomous), Avadi-Alamathi Road, Chennai 600 062",
		Reference: &types.ReferenceCollege{
			CollegeCode: "1118",
			CollegeName: "Vel Tech Multi Tech Dr. Rangarajan Dr. Sakunthala Engineering College (Autonomous), Avadi-Alamathi Road, Chennai 600 062",
			Address:     "AVADI - ALAMATHI ROAD",
			District:    "CHENNAI",
			Pincode:     "600062",
		},
		ReferenceMatch: &types.ReferenceMatch{Strategy: "exact", Score: 1},
	}

	hit := r.lookupFuzzyCache(item)
	if hit == nil {
		t.Fatal("expected fuzzy cache hit for Vel Tech Multi Tech")
	}
	if hit.PlaceID != "pid-multi" {
		t.Fatalf("expected multi-tech cache hit, got %s", hit.PlaceID)
	}
}
