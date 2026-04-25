package types

// InputItem mirrors our Python input structure.
type InputItem struct {
	Index          int               `json:"index"`
	Payload        interface{}       `json:"payload,omitempty"`
	Original       string            `json:"original"`
	Query          string            `json:"query"`
	Raw            interface{}       `json:"raw"`
	Reference      *ReferenceCollege `json:"reference,omitempty"`
	ReferenceMatch *ReferenceMatch   `json:"reference_match,omitempty"`
}

// ReferenceCollege is a best-effort enrichment record loaded from College_Info/output.json.
type ReferenceCollege struct {
	CollegeCode string `json:"college_code,omitempty"`
	CollegeName string `json:"college_name,omitempty"`
	Address     string `json:"address,omitempty"`
	Taluk       string `json:"taluk,omitempty"`
	District    string `json:"district,omitempty"`
	Pincode     string `json:"pincode,omitempty"`
	Website     string `json:"website,omitempty"`
	NameKey     string `json:"-"`
	Suspect     bool   `json:"-"`
}

// ReferenceMatch stores how confidently an input row was linked to the reference dataset.
type ReferenceMatch struct {
	Strategy string  `json:"strategy,omitempty"`
	Score    float64 `json:"score,omitempty"`
}

// Result is the clean output schema plus extras.
type Result struct {
	Index     int         `json:"index"`
	Original  string      `json:"original"`
	Query     string      `json:"query"`
	Latitude  *float64    `json:"latitude"`
	Longitude *float64    `json:"longitude"`
	MapsURL   string      `json:"maps_url"`
	Status    string      `json:"status"`
	Error     *string     `json:"error,omitempty"`
	PlaceID   string      `json:"place_id,omitempty"`
	Source    string      `json:"source,omitempty"`
	Note      string      `json:"note,omitempty"`
	Extras    interface{} `json:"extras,omitempty"`
}
