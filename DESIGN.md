# Counsly Design System — Mobile-First, Claude-Inspired

**Design principle:** Mobile is the primary surface. Every component, layout, and interaction is designed for a 360px viewport first. Desktop/laptop layouts are additive adaptations built on top of the mobile foundation.

---

## 1. Visual Theme & Atmosphere

Counsly's interface inherits Claude's warm, unhurried aesthetic — a parchment-toned canvas that feels like high-quality paper, not a cold digital surface. The warmth communicates trustworthiness, which is the product's core value: students need to trust the guidance they're given.

Every gray carries a yellow-brown undertone. Borders are cream-tinted. Shadows use warm transparent blacks. The darkest surfaces carry a barely perceptible olive warmth. This chromatic consistency creates a space that feels calm and reliable — essential for students making high-stakes decisions under pressure.

**Key Characteristics:**
- Warm parchment canvas (`#f5f4ed`) — calming, paper-like, not screen-like
- Serif for headings (Georgia), Sans for UI (Inter/system-ui), Mono for data (JetBrains Mono)
- Terracotta brand accent (`#c96442`) for primary CTAs only
- Safe/Moderate/Ambitious semantic colors from PRD
- Ring-based shadow system (`0px 0px 0px 1px`) instead of heavy drop shadows
- Dense-but-calm information hierarchy — max 3 scrolls to any primary action
- No dark mode on mobile in v2.0 — mild light-first only

---

## 2. Color Palette & Roles

### Primary
- **Anthropic Near Black** (`#141413`): Primary text — warm, not pure black
- **Terracotta Brand** (`#c96442`): Primary CTA buttons, highest-signal brand moments only
- **Coral Accent** (`#d97757`): Text accents, secondary emphasis

### Semantic (Counsly-specific)
- **Safe** (`#4E8A62`): Green — student's rank comfortably above cutoff
- **Moderate** (`#C17B4A`): Amber — student's rank within cutoff range
- **Ambitious** (`#B45A52`): Red — student's rank below cutoff, aspirational
- **Error Crimson** (`#b53333`): Error states
- **Focus Blue** (`#3898ec`): Input focus rings only — the only cool color, accessibility only

### Surface & Background
- **Parchment** (`#f5f4ed`): Primary page background
- **Ivory** (`#faf9f5`): Cards, elevated containers
- **Surface Alt** (`#EEE7DC`): Secondary surfaces, section dividers
- **Pure White** (`#ffffff`): Button surfaces, maximum-contrast elements only
- **Warm Sand** (`#e8e6dc`): Secondary button backgrounds, prominent interactive surfaces
- **Dark Surface** (`#30302e`): Dark containers (unused on mobile in v2.0)

### Neutrals & Text
- **Charcoal Warm** (`#4d4c48`): Button text on light surfaces
- **Olive Gray** (`#5e5d59`): Secondary body text
- **Stone Gray** (`#87867f`): Tertiary text, footnotes, metadata
- **Dark Warm** (`#3d3d3a`): Text links, emphasized secondary text

### Borders & Rings
- **Border Cream** (`#f0eee6`): Standard light border — gentlest containment
- **Border Warm** (`#e8e6dc`): Prominent borders, section dividers
- **Ring Warm** (`#d1cfc5`): Button hover/focus ring shadows
- **Ring Deep** (`#c2c0b6`): Active/pressed states

### Unlock Overlay (Free Tier)
- Blurred overlay at 60% opacity on premium content
- "Full Access" label centered with Terracotta CTA
- Background: Parchment at 60% opacity over blurred content

---

## 3. Typography — Mobile-First Scale

### Font Stack
- **Headline**: `Georgia, 'Times New Roman', serif` (Anthropic Serif substitute)
- **Body / UI**: `Inter, system-ui, -apple-system, sans-serif`
- **Numeric Data**: `'JetBrains Mono', 'Fira Code', monospace` (rank numbers, cutoff marks, percentages)

### Mobile-First Hierarchy (360px baseline)

| Role | Font | Mobile Size | Desktop Size | Weight | Line Height | Notes |
|------|------|-------------|--------------|--------|-------------|-------|
| Screen Title | Georgia | 22px (1.375rem) | 32px (2rem) | 500 | 1.20 | Page title, e.g. "Rank Guidance" |
| Section Header | Georgia | 18px (1.125rem) | 24px (1.5rem) | 500 | 1.20 | Section dividers, card group titles |
| Card Title | Georgia | 16px (1rem) | 20px (1.25rem) | 500 | 1.20 | College name, feature name |
| Feature Title | Georgia | 14px (0.875rem) | 16px (1rem) | 500 | 1.20 | Small headings inside cards |
| Body Large | Sans | 16px (1rem) | 18px (1.125rem) | 400 | 1.50 | Intro paragraphs, important copy |
| Body Standard | Sans | 14px (0.875rem) | 16px (1rem) | 400–500 | 1.50 | Standard body text |
| Body Small | Sans | 13px (0.8125rem) | 14px (0.875rem) | 400–500 | 1.40 | Compact body, list items |
| Caption | Sans | 12px (0.75rem) | 13px (0.8125rem) | 400 | 1.40 | Metadata, descriptions, timestamps |
| Label / Badge | Sans | 11px (0.6875rem) | 12px (0.75rem) | 500 | 1.25 | Badges, tags, community labels |
| Overline | Sans | 10px (0.625rem) | 10px (0.625rem) | 500 | 1.50 | Uppercase category labels |
| Numeric Data | Mono | 14px (0.875rem) | 15px (0.9375rem) | 500 | 1.40 | Ranks, marks, percentages, countdown |
| CTA Text | Sans | 15px (0.9375rem) | 16px (1rem) | 500 | 1.00 | Button text, nav active labels |

### Principles
- **Single-column hierarchy**: On mobile, there is no room for complex heading tiers. Screen Title → Section Header → Card Title is sufficient.
- **Georgia weight 500 max**: No bold on serifs — consistent editorial voice.
- **Line-height 1.50 for body**: Slightly tighter than Claude's 1.60 to fit more information in limited vertical space.
- **JetBrains Mono for data**: All rank numbers, cutoff marks, and percentages use monospace — scannable, data-like, trustworthy.

---

## 4. Component Stylings

### Buttons (Mobile-First)

**Primary CTA — Terracotta**
- Background: Terracotta (`#c96442`)
- Text: Ivory (`#faf9f5`), 15px, weight 500
- Height: 48px (exceeds 44px touch target)
- Padding: 0 20px
- Radius: 12px
- Width: full-width on mobile, auto on desktop
- Shadow: ring-based (`0px 0px 0px 1px #c96442`)
- Only one primary CTA visible per screen on mobile

**Secondary — Warm Sand**
- Background: Warm Sand (`#e8e6dc`)
- Text: Charcoal Warm (`#4d4c48`), 15px, weight 500
- Height: 48px
- Padding: 0 16px
- Radius: 12px
- Shadow: ring-based (`0px 0px 0px 1px #d1cfc5`)

**Ghost / Text Button**
- Background: transparent
- Text: Dark Warm (`#3d3d3a`), 14px, weight 500
- Height: 44px
- Padding: 0 12px
- Border: none
- Active state: Warm Sand background appears

**Destructive**
- Text: Error Crimson (`#b53333`), 14px, weight 500
- Same height and padding as Ghost

### Cards & Containers (Mobile-First)

**Standard Card**
- Background: Ivory (`#faf9f5`)
- Border: `1px solid #f0eee6`
- Radius: 12px
- Padding: 16px
- Margin bottom: 12px
- Full-width on mobile (no horizontal card scroll unless explicitly designed)

**Featured Card**
- Background: Ivory (`#faf9f5`)
- Border: `1px solid #e8e6dc`
- Radius: 16px
- Padding: 20px
- Shadow: whisper (`rgba(0,0,0,0.05) 0px 4px 24px`)

**Interactive Card (tappable)**
- Inherits Standard Card
- Active/pressed: `inset 0px 0px 0px 1px` at 15% opacity
- Touch feedback: subtle scale (0.98) on press, 150ms transition

**List Item Separator**
- `border-top: 1px solid #f0eee6`
- No bottom border on last item

**Unlock Overlay (Free Tier)**
- Position: absolute over premium card content
- Background: `rgba(245, 244, 237, 0.6)` + `backdrop-filter: blur(8px)`
- Center: "Full Access" label + Terracotta CTA
- Border-radius: inherits parent card radius

### Inputs & Forms (Mobile-First)

**Text Input / Select**
- Text: Near Black (`#141413`), 16px (prevents iOS zoom)
- Height: 48px
- Padding: 0 16px
- Border: `1px solid #e8e6dc`
- Radius: 12px
- Background: Pure White (`#ffffff`)
- Focus: `1px solid #3898ec` + ring `0px 0px 0px 3px rgba(56, 152, 236, 0.15)`
- Label: 12px Sans weight 500, Dark Warm (`#3d3d3a`), positioned above input

**Numeric Input (marks, rank)**
- Same as Text Input
- Font: JetBrains Mono, 16px
- Input mode: numeric (mobile keyboard shows number pad)

**Consent Checkbox**
- Size: 20x20px tap area (visual 16x16px, padding extends touch area)
- Border: `1px solid #e8e6dc`, radius 4px
- Checked: Terracotta (`#c96442`) fill, white checkmark
- Label: 13px Sans, Olive Gray (`#5e5d59`)

### Bottom Tab Bar (Mobile Navigation)

- Position: fixed bottom
- Height: 56px + safe-area-inset-bottom
- Background: Ivory (`#faf9f5`)
- Border-top: `1px solid #e8e6dc`
- 8 tabs: Home, Recs, Choices, Chat, Trends, Rounds, Explore, Profile
- Icon: 24px, inactive Stone Gray (`#87867f`), active Terracotta (`#c96442`)
- Label: 10px Sans weight 500, inactive Stone Gray, active Terracotta
- Active indicator: none — color change is sufficient (no underline, no dot)
- Tap target: each tab >= 44x44px
- Hidden on scroll down, shown on scroll up (optional)

### Sticky Action Areas

Every screen with a primary action has a sticky bottom area:
- Position: fixed bottom (above tab bar on authenticated screens)
- Background: Parchment (`#f5f4ed`) with `backdrop-filter: blur(8px)`
- Border-top: `1px solid #f0eee6`
- Padding: 12px 16px
- Contains: primary CTA (full-width) or action row
- Safe area: accounts for bottom tab bar height + safe-area-inset
- No sticky action area on dashboard (next action card serves this role)

---

## 5. Layout Principles — Mobile-First

### Viewport
- **Primary target**: 360px width (Android mid-range, ₹10k–₹20k)
- **Comfortable target**: 375–414px (standard phones)
- **Extended target**: up to 768px (tablets)
- **Desktop (later)**: 768px+ — progressive enhancement, not redesign

### Spacing System (4px base)

| Token | Value | Use |
|-------|-------|-----|
| xs | 4px | Tight inline gaps |
| sm | 8px | Compact spacing |
| md | 12px | Standard card padding (half) |
| lg | 16px | Standard card padding, screen padding |
| xl | 20px | Featured card padding |
| 2xl | 24px | Section spacing |
| 3xl | 32px | Major section breaks |
| 4xl | 48px | Screen-level vertical rhythm |

### Screen Structure (mobile default)

```
┌─────────────────────────┐
│  Status Bar (system)     │
├─────────────────────────┤
│  Screen Title            │  ← 56px app bar
│  (back arrow if nested)  │
├─────────────────────────┤
│                         │
│  Scrollable Content     │  ← Screen padding: 16px horizontal
│                         │
│  ┌───────────────────┐  │
│  │ Card              │  │  ← Card margin-bottom: 12px
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ Card              │  │
│  └───────────────────┘  │
│                         │
├─────────────────────────┤
│  Sticky Action Area     │  ← Above tab bar, if applicable
├─────────────────────────┤
│  ● ● ● ● ● ● ● ●     │  ← 56px tab bar (authenticated)
└─────────────────────────┘
```

### Low-Scroll Rule
No screen should require more than 3 scrolls to reach the primary action. Information hierarchy must be dense but calm — not cramped, not sparse. If a screen exceeds this, it needs restructuring, not scrolling hints.

### Desktop Adaptation (future)
- Max container width: 1200px, centered
- Cards can sit in 2–3 column grids
- Bottom tab bar → top navigation or sidebar
- Sticky action areas → inline or sidebar-positioned
- Typography scales up per the hierarchy table above
- Touch interactions gain hover states
- All mobile layouts must remain functional on desktop — desktop is enhancement only

---

## 6. Depth & Elevation (Mobile)

| Level | Treatment | Mobile Use |
|-------|-----------|------------|
| Flat (0) | No shadow, no border | Page background, inline text |
| Contained (1) | `1px solid #f0eee6` | Standard cards, list items |
| Ring (2) | `0px 0px 0px 1px #d1cfc5` | Buttons, interactive cards |
| Whisper (3) | `rgba(0,0,0,0.05) 0px 4px 24px` | Featured cards, modals |
| Overlay (4) | `backdrop-filter: blur(8px)` | Paywall overlay, bottom sheet backdrop |

On mobile, elevation is used sparingly. Flat/Contained handles 90% of UI. Whisper is reserved for modals and bottom sheets. Ring shadows provide interactive feedback without visual noise.

---

## 7. Interaction Patterns (Mobile-First)

### Touch Targets
- Minimum: 44x44px for all tappable elements
- Primary CTAs: 48px height, full-width
- List items: full-width tap area, min 48px height
- Tab bar icons: 56px total height per tab

### Gestures
- **Swipe left/right**: Reveal row actions on choice list, compare cards
- **Long-press**: Initiate drag on choice list reorder
- **Pull down**: Refresh recommendations, chat history
- **Bottom sheet**: Compare details, college branch picker, date picker

### Feedback
- Press: `scale(0.98)` at 150ms ease-out on tappable elements
- Active: Inset ring shadow at 15% opacity
- Loading: Skeleton screens (Warm Sand `#e8e6dc` shimmer) — never spinners
- Empty states: Illustration + heading + body + CTA — always actionable
- Error states: Error Crimson icon + message + retry CTA

### Keyboard Handling (Mobile)
- Input type: numeric for marks/rank fields → shows number pad
- Next/Done: logical tab order through form fields
- Dismiss keyboard: tap outside input or swipe down
- No custom keyboards

---

## 8. Screen-Specific Layouts

### Dashboard (Mobile)
- Next action card: full-width at top, Terracotta accent if urgent
- Shortlist status: compact row
- Recent compares: horizontal scroll, max 2 visible
- Phase alert: slim non-dismissible banner
- News strip: horizontal scroll, latest 3
- No filler cards. Every element is actionable.

### Choices (Mobile)
- Full-screen list, one row active at a time in edit mode
- Swipe left on row: delete, edit notes, change category
- Long-press: initiate drag reorder
- Sticky bottom: Add College + Save Snapshot + Export PDF
- Manual position jump: tap priority number → input field
- Strategy notes: expandable inline per row

### Compare (Mobile)
- Stacked vertical layout (not side-by-side — no room)
- Metric rows: label → college A value → college B value
- Significant differences highlighted with Terracotta accent
- Save session: icon button in app bar

### Rounds Tracker (Mobile)
- Full-screen active round card
- Countdown timer: prominent, top of screen, JetBrains Mono
- Confirmation options: tappable rows (not cards)
- TFC panel: expandable section with address and phone
- Per-round checklist: checkboxes with green tick animation

### College Explorer (Mobile)
- Search bar: sticky top (below app bar)
- Results: vertical card list, ranked by student fit
- Map: full-screen on tap, 466 pins, Near Me filter
- Filters: bottom sheet with multi-select

### College Insight (Mobile)
- Tabs: horizontal scroll (Overview · Cutoffs · Fees · Placements · Nearby)
- Shortlist CTA: sticky bottom (above tab bar)
- Branch-level detail: expandable accordion
- Premium tabs: blurred unlock overlay

### AI Chat (Mobile)
- Thread: scrollable message list
- Composer: sticky bottom, above tab bar
- Input: multiline, max 4 lines auto-expand
- Send button: Terracotta, 44x44px
- Message bubbles: Ivory (assistant), Warm Sand (user)
- No mic, no voice

### Onboarding (Mobile)
- Full-screen steps, one at a time
- Progress indicator: slim bar at top
- Large touch targets for mark inputs
- Empathetic eligibility gate: warm illustration + clear copy + no shame

---

## 9. Do's and Don'ts

### Do
- Design every component for 360px first
- Use Parchment (`#f5f4ed`) as the primary background
- Use Georgia weight 500 for all headings
- Use Terracotta (`#c96442`) only for primary CTAs
- Keep all neutrals warm-toned
- Use ring shadows for interactive states
- Use JetBrains Mono for all numeric data (ranks, marks, percentages)
- Make every card full-width on mobile
- Use sticky bottom actions for primary CTAs
- Keep screens low-scroll (max 3 scrolls to primary action)
- Use skeleton screens for loading, never spinners
- Use Safe/Moderate/Ambitious colors for cutoff context

### Don't
- Don't use cool blue-grays — exclusively warm-toned
- Don't use bold (700+) on Georgia — 500 is the ceiling
- Don't introduce saturated colors beyond Terracotta and semantic colors
- Don't use sharp corners (< 8px radius) on buttons or cards
- Don't use heavy drop shadows on mobile
- Don't use pure white as page background
- Don't design desktop-first and shrink — always start at 360px
- Don't show more than one primary CTA per screen on mobile
- Don't use side-by-side layouts on mobile — stack vertically
- Don't add dark mode on mobile in v2.0
- Don't use spinners or loading dots — skeleton screens only
- Don't show decorative/filler content on the dashboard

---

## 10. Quick Reference for AI Agents

### Color Quick Pick
- Page BG: `#f5f4ed`
- Card BG: `#faf9f5`
- Card Border: `#f0eee6`
- Primary Text: `#141413`
- Secondary Text: `#5e5d59`
- Tertiary Text: `#87867f`
- Primary CTA BG: `#c96442`
- Primary CTA Text: `#faf9f5`
- Safe: `#4E8A62`
- Moderate: `#C17B4A`
- Ambitious: `#B45A52`
- Error: `#b53333`
- Focus Ring: `#3898ec`

### Component Prompt Template
"Build a [component] for a 360px mobile viewport. Background: Parchment (#f5f4ed). Cards on Ivory (#faf9f5) with 12px radius and 1px solid Border Cream (#f0eee6). Heading in Georgia 16px weight 500, body in Inter 14px. Use Terracotta (#c96442) for the primary CTA. Sticky bottom action area with full-width CTA button. [specific requirements]."
