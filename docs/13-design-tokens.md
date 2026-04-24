# Counsly — Design Tokens

**Source:** Populated from `DESIGN.md` and launch mobile rules  
**Last updated:** 24 April 2026

---

## Launch UI Rules

- Mobile only for v1.0. Baseline viewport is `360px`.
- This section is the implementation contract for launch UI. If `DESIGN.md` and this section differ, this section wins for launch build decisions.
- Launch authenticated navigation is `Home`, `Recs`, `Choices`, `Explore`, `Profile`.
- `Chat`, `Rounds`, `Analytics`, `News`, `Compare`, and `Map` are secondary entry points, not primary bottom-nav items in launch.
- One primary CTA per screen. Secondary actions belong in ghost actions, inline links, or an overflow bottom sheet.
- Decision-heavy surfaces use list-first density. Cards are containers, not an excuse for extra scroll.
- No dark mode in v2.0 mobile launch.

## Color Tokens

| Token | Value | Use |
| --- | --- | --- |
| `color.bg.page` | `#f5f4ed` | Main page background |
| `color.bg.card` | `#faf9f5` | Standard card background |
| `color.bg.surface_alt` | `#EEE7DC` | Section divider / alternate surface |
| `color.bg.button_secondary` | `#e8e6dc` | Secondary button and skeleton base |
| `color.bg.white` | `#ffffff` | Inputs and maximum-contrast surfaces |
| `color.text.primary` | `#141413` | Primary text |
| `color.text.secondary` | `#5e5d59` | Body/supporting copy |
| `color.text.tertiary` | `#87867f` | Metadata, footnotes, inactive nav |
| `color.text.emphasis` | `#3d3d3a` | Secondary emphasized text and links |
| `color.brand.primary` | `#c96442` | Only primary CTA background |
| `color.brand.secondary` | `#d97757` | Secondary accent moments only |
| `color.semantic.safe` | `#4E8A62` | Safe label |
| `color.semantic.moderate` | `#C17B4A` | Moderate label |
| `color.semantic.ambitious` | `#B45A52` | Ambitious label |
| `color.semantic.error` | `#b53333` | Error state |
| `color.focus` | `#3898ec` | Input focus ring only |
| `color.border.default` | `#f0eee6` | Default card/input border |
| `color.border.strong` | `#e8e6dc` | Stronger section or card border |
| `color.shadow.ring` | `#d1cfc5` | Ring shadow color |
| `color.shadow.ring_active` | `#c2c0b6` | Active/pressed ring color |

## Typography Tokens

| Token | Font | Mobile size | Weight | Line height | Use |
| --- | --- | --- | --- | --- | --- |
| `font.heading` | `Georgia, 'Times New Roman', serif` | - | `500` max | - | Screen and section titles |
| `font.body` | `Inter, system-ui, -apple-system, sans-serif` | - | `400-500` | - | UI and body copy |
| `font.mono` | `'JetBrains Mono', 'Fira Code', monospace` | - | `500` | - | Ranks, marks, countdowns, tabular values |
| `text.screen_title` | heading | `22px` | `500` | `1.20` | Page title |
| `text.section_header` | heading | `18px` | `500` | `1.20` | Section heading |
| `text.card_title` | heading | `16px` | `500` | `1.20` | College or feature title |
| `text.feature_title` | heading | `14px` | `500` | `1.20` | Small heading |
| `text.body_lg` | body | `16px` | `400` | `1.50` | Intro copy |
| `text.body` | body | `14px` | `400-500` | `1.50` | Standard body |
| `text.body_sm` | body | `13px` | `400-500` | `1.40` | Dense lists |
| `text.caption` | body | `12px` | `400` | `1.40` | Metadata |
| `text.badge` | body | `11px` | `500` | `1.25` | Badges and tags |
| `text.overline` | body | `10px` | `500` | `1.50` | Uppercase helper labels |
| `text.data` | mono | `14px` | `500` | `1.40` | Numeric data |
| `text.cta` | body | `15px` | `500` | `1.00` | Button labels |

## Layout And Spacing Tokens

| Token | Value | Use |
| --- | --- | --- |
| `viewport.base` | `360px` | Primary layout target |
| `layout.page_padding_x` | `16px` | Screen horizontal padding |
| `layout.page_padding_y` | `16px` | Standard vertical inset |
| `layout.app_bar_h` | `56px` | Mobile app bar |
| `layout.tab_bar_h` | `56px` | Bottom nav bar |
| `layout.sticky_action_min_h` | `72px` | Sticky CTA zone including padding |
| `layout.touch_min` | `44px` | Minimum tappable area |
| `layout.button_h` | `48px` | Standard CTA height |
| `layout.input_h` | `48px` | Standard input height |
| `layout.card_gap` | `12px` | Gap between cards |
| `layout.max_scrolls_to_primary` | `3` | Max scroll-depth rule |
| `space.xs` | `4px` | Tight gap |
| `space.sm` | `8px` | Compact gap |
| `space.md` | `12px` | Card internal half-padding / compact section gap |
| `space.lg` | `16px` | Standard padding |
| `space.xl` | `20px` | Featured card padding |
| `space.2xl` | `24px` | Section spacing |
| `space.3xl` | `32px` | Major break |
| `space.4xl` | `48px` | Screen-level rhythm |

## Shape And Elevation Tokens

| Token | Value | Use |
| --- | --- | --- |
| `radius.sm` | `8px` | Small elements |
| `radius.md` | `12px` | Inputs, buttons, cards |
| `radius.lg` | `16px` | Featured cards and modals |
| `border.default` | `1px solid #f0eee6` | Standard card/input border |
| `border.strong` | `1px solid #e8e6dc` | Stronger divider |
| `shadow.ring` | `0 0 0 1px #d1cfc5` | Interactive state |
| `shadow.ring_active` | `0 0 0 1px #c2c0b6` | Pressed state |
| `shadow.whisper` | `rgba(0,0,0,0.05) 0 4px 24px` | Featured cards / modals |
| `overlay.blur` | `8px` | Unlock overlays and bottom sheet backdrop |

## Component Contracts

### Buttons

- Primary button: `48px` high, full width on mobile, `color.brand.primary` background, `color.bg.card` text, `radius.md`.
- Secondary button: `48px` high, `color.bg.button_secondary` background, `color.text.primary` text.
- Ghost button: `44px` high, transparent background, `color.text.emphasis`.
- Do not place two primary buttons in the same sticky action area.

### Cards

- Standard card: `color.bg.card`, `border.default`, `radius.md`, `16px` padding.
- Featured card: `color.bg.card`, `border.strong`, `radius.lg`, `20px` padding, `shadow.whisper`.
- Interactive cards use `shadow.ring` for hover/press feedback instead of heavy drop shadows.

### Inputs

- Text and select inputs: `48px` high, `16px` body text, white background, `border.strong`, `radius.md`.
- Numeric inputs use `font.mono` and must keep `16px` font size to avoid iOS zoom.
- Focus state uses only `color.focus` plus a soft focus ring.

### Unlock Boards

- Locked preview uses blurred content plus one clear value statement and one CTA.
- Use the same unlock pattern across recommendations, compare, insight, analytics, and rounds.
- Do not switch between inline blur, modal trap, and full-page interruption for the same type of entitlement event.

### Bottom Navigation

- Launch nav is 5 tabs only.
- Each tab gets a minimum `44px x 44px` tap target inside a `56px` high bar.
- Active state is color only; no extra underline or dot.

### Sticky Action Areas

- Sticky areas sit above the tab bar.
- They carry one primary CTA.
- If a screen needs more than one secondary action, those actions move into a ghost-action row or overflow bottom sheet.

## Screen Rules For Launch

- Dashboard: topmost full-width next-action card, no filler cards, no more than one horizontal content strip.
- Recommendations: vertical result list first, filters in a sheet, safety labels always visible.
- Choices: one active row at a time, numeric move is the default reorder interaction, `Add College` is the primary sticky CTA, `Save Snapshot` and `Export PDF` move to secondary actions.
- Compare: stacked metric rows only, no side-by-side desktop-style columns on mobile.
- Explore: sticky search, vertical results, map only as a secondary full-screen mode.
- College Insight: shortlist CTA sticky at bottom, premium sections lock inline, not as a route jump.
- Chat: text only, composer max 4 lines, send button `44px`.
- Onboarding: one step at a time, large numeric inputs, resume exactly where the user left off.

## Do Not Break These Rules

- Do not introduce desktop-first layout decisions into mobile launch screens.
- Do not add dark mode in v2.0.
- Do not use cool blue-gray UI chrome outside focus states.
- Do not use heavy shadows when ring borders are enough.
- Do not use more than one primary CTA per screen.
- Do not ship an 8-tab authenticated nav in launch.
- Do not use spinners where a skeleton or optimistic state is possible.
