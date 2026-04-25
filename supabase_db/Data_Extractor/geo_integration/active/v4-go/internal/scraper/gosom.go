package scraper

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
	"time"
)

// Result mirrors key fields we care about from gosom output.
type Result struct {
	InputID         string         `json:"input_id"`
	Title           string         `json:"title"`
	Categories      []string       `json:"categories"`
	Category        string         `json:"category"`
	Address         string         `json:"address"`
	Phone           string         `json:"phone"`
	Website         string         `json:"website"`
	Latitude        float64        `json:"latitude"`
	Longitude       float64        `json:"longitude"`
	PlaceID         string         `json:"place_id"`
	CID             string         `json:"cid"`
	DataID          string         `json:"data_id"`
	ReviewsCount    int            `json:"review_count"`
	ReviewRating    float64        `json:"review_rating"`
	PopularTimes    any            `json:"popular_times"`
	Emails          []string       `json:"emails"`
	UserReviews     any            `json:"user_reviews"`
	UserReviewsExt  any            `json:"user_reviews_extended"`
	OpenHours       any            `json:"open_hours"`
	PriceRange      string         `json:"price_range"`
	Images          any            `json:"images"`
	PlusCode        string         `json:"plus_code"`
	Link            string         `json:"link"`
	Status          string         `json:"status"`
	CompleteAddress map[string]any `json:"complete_address"`
	Raw             map[string]any `json:"-"`
}

type resultJSON struct {
	InputID         string         `json:"input_id"`
	Title           string         `json:"title"`
	Categories      []string       `json:"categories"`
	Category        string         `json:"category"`
	Address         string         `json:"address"`
	Phone           string         `json:"phone"`
	Website         string         `json:"website"`
	WebsiteAlt      string         `json:"web_site"`
	Latitude        float64        `json:"latitude"`
	Longitude       float64        `json:"longitude"`
	LongitudeAlt    float64        `json:"longtitude"`
	PlaceID         string         `json:"place_id"`
	CID             string         `json:"cid"`
	DataID          string         `json:"data_id"`
	ReviewsCount    int            `json:"review_count"`
	ReviewRating    float64        `json:"review_rating"`
	PopularTimes    any            `json:"popular_times"`
	Emails          []string       `json:"emails"`
	UserReviews     any            `json:"user_reviews"`
	UserReviewsExt  any            `json:"user_reviews_extended"`
	OpenHours       any            `json:"open_hours"`
	PriceRange      string         `json:"price_range"`
	Images          any            `json:"images"`
	PlusCode        string         `json:"plus_code"`
	Link            string         `json:"link"`
	Status          string         `json:"status"`
	CompleteAddress map[string]any `json:"complete_address"`
}

func (r *Result) UnmarshalJSON(data []byte) error {
	var aux resultJSON
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}

	r.InputID = aux.InputID
	r.Title = aux.Title
	r.Categories = aux.Categories
	r.Category = aux.Category
	r.Address = aux.Address
	r.Phone = aux.Phone
	r.Website = aux.Website
	if r.Website == "" {
		r.Website = aux.WebsiteAlt
	}
	r.Latitude = aux.Latitude
	r.Longitude = aux.Longitude
	if r.Longitude == 0 && aux.LongitudeAlt != 0 {
		r.Longitude = aux.LongitudeAlt
	}
	r.PlaceID = aux.PlaceID
	r.CID = aux.CID
	r.DataID = aux.DataID
	r.ReviewsCount = aux.ReviewsCount
	r.ReviewRating = aux.ReviewRating
	r.PopularTimes = aux.PopularTimes
	r.Emails = aux.Emails
	r.UserReviews = aux.UserReviews
	r.UserReviewsExt = aux.UserReviewsExt
	r.OpenHours = aux.OpenHours
	r.PriceRange = aux.PriceRange
	r.Images = aux.Images
	r.PlusCode = aux.PlusCode
	r.Link = aux.Link
	r.Status = aux.Status
	r.CompleteAddress = aux.CompleteAddress
	return nil
}

// Runner shells out to the gosom/google-maps-scraper docker image with -json output.
type Runner struct {
	Image string
}

func NewRunner(image string) *Runner {
	if image == "" {
		image = "gosom/google-maps-scraper"
	}
	return &Runner{Image: image}
}

// Run executes the scraper for given queries. extraArgs are passed through to the image.
func (r *Runner) Run(ctx context.Context, queries []string, extraArgs []string) ([]Result, error) {
	if len(queries) == 0 {
		return nil, fmt.Errorf("no queries provided")
	}

	base := []string{"run", "--rm", "-i", r.Image, "sh", "-c", "cat > /queries.txt && google-maps-scraper -input /queries.txt -json " + strings.Join(extraArgs, " ")}
	cmd := exec.CommandContext(ctx, "docker", base...)
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, err
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	cmd.Stderr = cmd.Stdout

	if err := cmd.Start(); err != nil {
		return nil, err
	}

	go func() {
		defer stdin.Close()
		for _, q := range queries {
			_, _ = stdin.Write([]byte(q + "\n"))
		}
	}()

	results := []Result{}
	scanner := bufio.NewScanner(stdout)
	buf := make([]byte, 0, 1024*1024)
	scanner.Buffer(buf, 10*1024*1024)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || !strings.HasPrefix(line, "{") {
			continue
		}

		var res Result
		if err := json.Unmarshal([]byte(line), &res); err != nil {
			continue
		}
		var raw map[string]any
		if err := json.Unmarshal([]byte(line), &raw); err == nil {
			res.Raw = raw
		}
		results = append(results, res)
	}
	if err := scanner.Err(); err != nil {
		return results, err
	}

	waitCh := make(chan error, 1)
	go func() {
		waitCh <- cmd.Wait()
	}()

	select {
	case err := <-waitCh:
		if err != nil {
			return results, err
		}
	case <-ctx.Done():
		_ = cmd.Process.Kill()
		return results, ctx.Err()
	}

	return results, nil
}

// WithTimeout helper
func (r *Runner) RunWithTimeout(ctx context.Context, queries []string, extraArgs []string, timeout time.Duration) ([]Result, error) {
	if timeout <= 0 {
		return r.Run(ctx, queries, extraArgs)
	}
	cctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	return r.Run(cctx, queries, extraArgs)
}
