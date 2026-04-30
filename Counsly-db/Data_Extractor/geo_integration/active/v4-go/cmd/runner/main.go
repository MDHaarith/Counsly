package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"college_locator_v4go/internal/config"
	"college_locator_v4go/internal/normalize"
	"college_locator_v4go/internal/reference"
	"college_locator_v4go/internal/resolver"
	"college_locator_v4go/internal/scraper"
	"college_locator_v4go/internal/types"
)

func main() {
	inputPath := flag.String("input", "", "Path to input JSON")
	provider := flag.String("provider", "gosom", "Provider to use: gosom")
	configDir := flag.String("config-dir", "", "Path to config dir (defaults to ./config)")
	outDir := flag.String("out-dir", "", "Output dir (defaults to archive/v4go_intermediate under project root)")
	referencePath := flag.String("reference", "", "Path to reference college JSON (defaults to College_Info/output.json when available)")
	extra := flag.String("extra", "", "Extra args to pass to provider (comma-separated)")
	timeoutSec := flag.Int("timeout", 120, "Per-item timeout seconds for provider run")
	minScore := flag.Float64("min-score", 0.62, "Minimum candidate score to accept")
	minMargin := flag.Float64("min-margin", 0.06, "Minimum score margin over the next-best candidate")
	maxVariants := flag.Int("max-variants", 8, "Maximum query variants to try per input item")
	flag.Parse()

	if *inputPath == "" {
		fmt.Fprintln(os.Stderr, "--input is required")
		os.Exit(1)
	}

	if *provider != "gosom" {
		fmt.Fprintf(os.Stderr, "unknown provider: %s\n", *provider)
		os.Exit(1)
	}

	projectRoot := discoverProjectRoot()

	if *configDir == "" {
		*configDir = filepath.Join(projectRoot, "v4-go", "config")
	}
	if *outDir == "" {
		*outDir = filepath.Join(projectRoot, "archive", "v4go_intermediate")
	}
	if *referencePath == "" {
		*referencePath = defaultReferencePath(projectRoot)
	}
	if err := os.MkdirAll(*outDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "failed to create out dir: %v\n", err)
		os.Exit(1)
	}

	normCfg, err := config.LoadNormalizationConfig(filepath.Join(*configDir, "query_normalization.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to load normalization config: %v\n", err)
		os.Exit(1)
	}
	manualOverrides, err := config.LoadOverrideEntries(filepath.Join(*configDir, "manual_overrides.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to load manual overrides: %v\n", err)
		os.Exit(1)
	}
	placeCache, err := config.LoadOverrideEntries(filepath.Join(*configDir, "place_cache.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to load place cache: %v\n", err)
		os.Exit(1)
	}
	parentCampuses, err := config.LoadParentCampuses(filepath.Join(*configDir, "parent_campuses.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to load parent campuses: %v\n", err)
		os.Exit(1)
	}

	inputBytes, err := os.ReadFile(*inputPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to read input: %v\n", err)
		os.Exit(1)
	}

	var raw any
	if err := json.Unmarshal(inputBytes, &raw); err != nil {
		fmt.Fprintf(os.Stderr, "failed to parse input JSON: %v\n", err)
		os.Exit(1)
	}

	items := parseInput(raw)
	if len(items) == 0 {
		fmt.Fprintln(os.Stderr, "no items found in input")
		os.Exit(1)
	}

	extraArgs := splitExtraArgs(*extra)
	normalizer := normalize.New(normCfg)
	if *referencePath != "" {
		referenceColleges, err := reference.Load(*referencePath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "failed to load reference data: %v\n", err)
			os.Exit(1)
		}
		items = reference.NewMatcher(normalizer, referenceColleges).Attach(items)
	}
	matchResolver := resolver.New(normalizer, manualOverrides, placeCache, parentCampuses, *minScore, *minMargin, *maxVariants)
	runner := scraper.NewRunner("")

	ctx := context.Background()
	clean := make([]types.Result, 0, len(items))
	unresolved := []types.Result{}

	for idx, item := range items {
		fmt.Fprintf(os.Stderr, "[%d/%d] %s\n", idx+1, len(items), item.Original)
		result := matchResolver.Resolve(ctx, item, func(callCtx context.Context, queries []string) ([]scraper.Result, error) {
			return runner.RunWithTimeout(callCtx, queries, extraArgs, time.Duration(*timeoutSec)*time.Second)
		}, time.Duration(*timeoutSec)*time.Second)

		if result.Latitude != nil && result.Longitude != nil {
			clean = append(clean, result)
		} else {
			unresolved = append(unresolved, result)
		}
	}

	base := strings.TrimSuffix(filepath.Base(*inputPath), filepath.Ext(*inputPath))
	cleanPath := filepath.Join(*outDir, base+"_clean_output.json")
	unresolvedPath := filepath.Join(*outDir, base+"_clean_output_unresolved.json")

	if err := writeJSON(cleanPath, clean); err != nil {
		fmt.Fprintf(os.Stderr, "failed to write clean output: %v\n", err)
	}
	if err := writeJSON(unresolvedPath, unresolved); err != nil {
		fmt.Fprintf(os.Stderr, "failed to write unresolved: %v\n", err)
	}

	fmt.Printf("Done. clean=%d unresolved=%d clean_path=%s unresolved_path=%s\n", len(clean), len(unresolved), cleanPath, unresolvedPath)
}

func parseInput(raw any) []types.InputItem {
	items := []types.InputItem{}
	switch values := raw.(type) {
	case []any:
		for index, value := range values {
			item := types.InputItem{Index: index, Raw: value}
			switch typed := value.(type) {
			case map[string]any:
				for _, key := range []string{"query", "title", "name", "college", "institution"} {
					if candidate, ok := typed[key]; ok {
						if text, ok := candidate.(string); ok && strings.TrimSpace(text) != "" {
							item.Query = strings.TrimSpace(text)
							item.Original = item.Query
							break
						}
					}
				}
			default:
				item.Query = strings.TrimSpace(fmt.Sprintf("%v", typed))
				item.Original = item.Query
			}
			if item.Query != "" {
				items = append(items, item)
			}
		}
	}
	return items
}

func splitExtraArgs(raw string) []string {
	if strings.TrimSpace(raw) == "" {
		return nil
	}
	args := strings.Split(raw, ",")
	out := make([]string, 0, len(args))
	for _, arg := range args {
		arg = strings.TrimSpace(arg)
		if arg != "" {
			out = append(out, arg)
		}
	}
	return out
}

func writeJSON(path string, value any) error {
	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	return encoder.Encode(value)
}

func discoverProjectRoot() string {
	candidates := []string{}

	if cwd, err := os.Getwd(); err == nil {
		candidates = append(candidates, cwd)
		candidates = append(candidates, filepath.Join(cwd, "processed", "College_Details"))

		dir := cwd
		for i := 0; i < 6; i++ {
			candidates = append(candidates, dir)
			parent := filepath.Dir(dir)
			if parent == dir {
				break
			}
			dir = parent
		}
	}

	if exe, err := os.Executable(); err == nil {
		dir := filepath.Dir(exe)
		for i := 0; i < 6; i++ {
			candidates = append(candidates, dir)
			parent := filepath.Dir(dir)
			if parent == dir {
				break
			}
			dir = parent
		}
	}

	seen := map[string]struct{}{}
	for _, candidate := range candidates {
		if candidate == "" {
			continue
		}
		candidate = filepath.Clean(candidate)
		if _, ok := seen[candidate]; ok {
			continue
		}
		seen[candidate] = struct{}{}

		if isCollegeDetailsRoot(candidate) {
			return candidate
		}
		if filepath.Base(candidate) == "v4-go" && fileExists(filepath.Join(candidate, "config", "query_normalization.json")) {
			return filepath.Dir(candidate)
		}

		child := filepath.Join(candidate, "processed", "College_Details")
		if isCollegeDetailsRoot(child) {
			return child
		}
	}

	if cwd, err := os.Getwd(); err == nil {
		return cwd
	}
	return "."
}

func defaultReferencePath(projectRoot string) string {
	candidates := []string{
		filepath.Join(projectRoot, "College_Info", "output.json"),
		filepath.Join(projectRoot, "..", "..", "College_Info", "output.json"),
		filepath.Join(projectRoot, "..", "College_Info", "output.json"),
	}
	for _, candidate := range candidates {
		candidate = filepath.Clean(candidate)
		if fileExists(candidate) {
			return candidate
		}
	}
	return ""
}

func isCollegeDetailsRoot(path string) bool {
	return fileExists(filepath.Join(path, "v4-go", "config", "query_normalization.json"))
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
