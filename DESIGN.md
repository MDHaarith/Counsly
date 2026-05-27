# Counsly — Design System Specification

## Vision
Counsly is a humanist, warm-canvas editorial workspace designed for the 2027 TNEA cycle. It explicitly rejects typical tech tropes (cool neon glows, stark blue-and-slate dashboards, and fake AI-prediction charts) in favor of a calm, authoritative, and data-driven workspace. 

Our interface mirrors the tactile feel of physical brochures and official advisory bulletins, while utilizing modern web layouts, fluid spacing, and subtle interactive micro-animations.

---

## 1. Color Palette

Our brand colors are derived from warm organic materials (tinted creams, soft corals, deep slate-navy chrome, and pine greens). This establishes a high-trust, editorial atmosphere.

| Token | HSL / Hex | Usage |
|---|---|---|
| `counsly-canvas` | `hsl(43, 20%, 97%)` / `#faf9f5` | Main warm body canvas background |
| `counsly-soft` | `hsl(41, 23%, 94%)` / `#f5f0e8` | Section backgrounds, inputs, and container surfaces |
| `counsly-line` | `hsl(38, 16%, 88%)` / `#e6dfd8` | Subtle borders, table dividers, and structural hairlines |
| `counsly-ink` | `hsl(60, 4%, 8%)` / `#141413` | Canonical primary headings and strong titles |
| `counsly-body` | `hsl(60, 3%, 24%)` / `#3d3d3a` | Readable secondary copy and descriptive body text |
| `counsly-muted` | `hsl(48, 5%, 41%)` / `#6c6a64` | Helper text, secondary captions, and inactive elements |
| `counsly-coral` | `hsl(15, 52%, 58%)` / `#cc785c` | Brand primary accent: buttons, highlights, active selections |
| `counsly-teal` | `hsl(169, 39%, 54%)` / `#5db8a6` | Success badges, verified states, and high-intake capacity metrics |
| `counsly-card` | `hsl(39, 21%, 91%)` / `#efe9de` | Static card surfaces and elevated panel backgrounds |
| `counsly-dark` | `hsl(24, 9%, 8%)` / `#181715` | Elevated dark contrast modes (navigation chrome, footer, select code blocks) |

---

## 2. Typography

We pair a literary editorial display serif for headline copy with an elegant, highly-readable geometric sans-serif for numbers and action surfaces.

### Display Serif (Copernicus / Tiempos Headline / Georgia fallback)
Used to convey authority, focus, and deliberate rhythm.
* **Header 1 (`text-6xl md:text-7xl`)**: `font-family: Copernicus, Georgia, serif; font-weight: 400; letter-spacing: -0.02em; line-height: 1.05;`
* **Header 2 (`text-4xl md:text-5xl`)**: `font-family: Copernicus, Georgia, serif; font-weight: 400; letter-spacing: -0.01em; line-height: 1.15;`
* **Header 3 (`text-2xl md:text-3xl`)**: `font-family: Copernicus, Georgia, serif; font-weight: 400; line-height: 1.25;`

### Humanist Sans-Serif (Styrene B / Inter / system-ui fallback)
Used for highly-readable tabular numbers, form controls, and body paragraphs.
* **Body Text (`text-base`)**: `font-family: Inter, sans-serif; font-weight: 400; line-height: 1.55; text-color: #3d3d3a;`
* **Tabular/Mono Figures (`font-mono`)**: `font-family: monospace; letter-spacing: -0.02em;`

---

## 3. UI Component Tokens

### Buttons

* **Primary Button (`button-primary`)**
  * **Default State**: Background `#cc785c` (`counsly-coral`), Text white, Border none, rounded-xl (12px), transition duration 200ms.
  * **Hover State**: Background `#b86448`, translate-y(-1px) micro-interaction.
  * **Disabled State**: Background `#e6dfd8` (`counsly-line`), Text `#6c6a64` (`counsly-muted`), cursor-not-allowed.

* **Secondary Button (`button-secondary`)**
  * **Default State**: Background transparent, Border 1px solid `#e6dfd8` (`counsly-line`), Text `#141413` (`counsly-ink`), rounded-xl (12px).
  * **Hover State**: Background `#f5f0e8` (`counsly-soft`), Border color `#cc785c` (`counsly-coral`).

### Filing Drawer Selection Panel
The core workspace component for selecting, organizing, and drag-and-ordering up to 300 choices:
* **Filing Row Container**: Surface background `#faf9f5` (`counsly-canvas`), border 1px solid `#e6dfd8` (`counsly-line`), transition border-color on grab.
* **Category Badges**:
  * **Safe**: Green/Teal highlight representing high historical cutoff compatibility.
  * **Moderate**: Coral accent representing medium cutoff compatibility.
  * **Ambitious**: Amber/Orange representing tight historical bounds.

---

## 4. Layout & Grid Rules

1. **Warm Glowing Blobs**: We place subtle decorative absolute radial gradients in section corners (e.g. `bg-counsly-coral/[0.08] blur-[100px]`) to create depth and custom lighting beneath components without cluttering content.
2. **Double Line Accents**: Major container components use the signature `border border-counsly-line` with a double-rule division where appropriate to ground content.
3. **Display Density**: Dense data rows (financials, seat matrix, cutoff trends) default to high-density layouts (`py-1.5 px-3`) with full horizontal dividers rather than boxes to maximize screen context and ease comparison.
