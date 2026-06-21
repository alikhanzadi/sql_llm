# ATHL Design Language for Analytics Dashboards

This document translates the visual language of the ATHL websites into a transferable brief for another design or coding agent. It is intentionally not a pixel-perfect spec. The goal is to recreate the same feeling for an analytics dashboard: dark, high-contrast, sports-finance, token-market, and athlete-forward.

## Reference Pages

- Public ATHL homepage: https://athl.live/
- Sandbox ATHL homepage: https://sandbox.athl.live/
- Sandbox athlete profile: https://sandbox.athl.live/profile/adrian_peterson

When these references conflict, prefer the sandbox profile for analytics/dashboard surfaces and borrow the public homepage's bold brand typography and orange highlights sparingly.

## Saved Visual Assets

Assets were downloaded individually into `docs/athl_design_language_assets/`.

| Asset | Use |
|---|---|
| `jhenny-andrade-callout.webp` | Public homepage creator card reference |
| `sean-omalley-callout.webp` | Public homepage athlete card reference |
| `alica-schmidt-callout.webp` | Public homepage athlete card reference |
| `athl-footer-crowd.webp` | Large brand/environmental image reference |
| `james-harden-profile-photo.jpg` | Sandbox profile-photo/avatar reference |
| `shaquille-oneal-profile-photo.jpg` | Sandbox profile-photo/avatar reference |
| `bts-profile-photo.jpg` | Sandbox profile-photo/avatar reference |

![Jhenny Andrade callout](athl_design_language_assets/jhenny-andrade-callout.webp)
![Sean O'Malley callout](athl_design_language_assets/sean-omalley-callout.webp)
![Alica Schmidt callout](athl_design_language_assets/alica-schmidt-callout.webp)
![ATHL footer crowd](athl_design_language_assets/athl-footer-crowd.webp)

## Core Brand Feeling

ATHL should feel like a sports-finance terminal with athlete-market energy. It is not a soft SaaS dashboard. It should feel sharp, premium, compressed, numerical, and alive.

Good target words:

- dark
- market-like
- athletic
- high-contrast
- compressed
- premium
- tokenized
- operational
- live

Avoid target words:

- pastel
- corporate
- soft
- spacious marketing SaaS
- generic fintech
- beige
- glassmorphism-heavy
- playful startup

## Visual Foundation

### Backgrounds

Use a black-first interface.

- Main page background: pure black or near-black.
- Dashboard panels: charcoal and dark graphite.
- Card backgrounds: very dark gray with subtle translucent white borders.
- Avoid white page sections.
- Avoid pale dashboard panels.
- Avoid large decorative gradients.

Suggested tokens:

```css
:root {
  --athl-black: #000000;
  --athl-ink: #0d0d0d;
  --athl-panel: #151515;
  --athl-panel-2: #1c1c1c;
  --athl-panel-3: #27272a;
  --athl-line: rgba(255, 255, 255, 0.14);
  --athl-line-soft: rgba(255, 255, 255, 0.08);
}
```

### Color

The palette is minimal and high-contrast.

- White: primary text, primary numeric values, active states.
- Muted gray: labels, captions, table metadata, secondary text.
- Orange: brand accent, primary call to action, primary economic metric.
- Lime green: positive movement, growth, success, upward deltas.
- Electric blue: secondary links, alternate chart series, active navigation accents.

Suggested tokens:

```css
:root {
  --athl-white: #ffffff;
  --athl-muted: rgba(255, 255, 255, 0.62);
  --athl-faint: rgba(255, 255, 255, 0.38);
  --athl-orange: #ff531c;
  --athl-orange-2: #fb5c27;
  --athl-lime: #b3e562;
  --athl-blue: #0085ff;
}
```

### Typography

Use typography to create the ATHL character. The sites lean on uppercase, condensed, technical, and mono-feeling text.

Recommended type roles:

- Display headings: `Chakra Petch`, fallback `Roboto Condensed`, sans-serif.
- Body text: `Roboto Condensed` or `Roboto`.
- Numeric labels and metadata: `DM Mono`, fallback monospace.

Suggested import:

```css
@import url("https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=DM+Mono:wght@400;500&family=Roboto+Condensed:wght@400;500;700&family=Roboto:wght@400;500;700&display=swap");
```

Suggested typography rules:

```css
.display-title {
  font-family: "Chakra Petch", "Roboto Condensed", sans-serif;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0;
  line-height: 0.95;
}

.metric-value {
  font-family: "Chakra Petch", "Roboto Condensed", sans-serif;
  font-weight: 700;
  letter-spacing: 0;
}

.metric-label,
.table-label,
.filter-label {
  font-family: "DM Mono", monospace;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0;
}
```

## Dashboard Layout Guidance

### First View

Do not build a marketing landing page. The first viewport should immediately show the usable dashboard.

Recommended first viewport:

1. Slim dark header with ATHL mark/name, dashboard title, date range, and navigation/filter controls.
2. North-star metric band.
3. KPI card grid.
4. At least the top edge of the first chart section visible below.

### Density

The dashboard should be information-dense but not chaotic.

- Keep labels short.
- Use compact KPI cards.
- Use tables and charts that support scanning.
- Reserve big display type for major dashboard headings and top-line metrics.
- Avoid large empty hero space.

### Structure

Use full-width dark sections or unframed dashboard areas. Do not put large page sections inside decorative cards. Cards should be for repeated metric units, chart panels, table panels, and modal/detail surfaces.

## Component Rules

### Header

The header should feel like a trading interface.

- Black background.
- Thin bottom border.
- Uppercase nav labels.
- Date range and status in mono text.
- Compact controls on the right.

Example labels:

- `ATHL DATA`
- `MARKET HEALTH`
- `LAST 30D`
- `LIVE DATA`
- `DB_ENV: LOCAL`

### North-Star Band

The north-star metric should be the strongest visual element after the title.

Style:

- Charcoal panel.
- Left border or top rule in ATHL orange.
- Large condensed numeric value.
- Mono uppercase label.
- Lime or orange delta.
- Short explanatory text in muted gray.

Recommended content pattern:

```text
TOKEN ECONOMIC ACTIVITY
$213.3K
+1.7% VS PRIOR 30D
Completed USDC transaction volume generated across ATHL tokens.
```

### KPI Cards

KPI cards should feel like market tiles.

Style:

- Dark panel background.
- 6-8px border radius.
- 1px translucent white border.
- Thin accent bar or top border.
- Uppercase mono label.
- Large condensed value.
- Small mono delta.
- Muted helper copy.

Avoid:

- White cards.
- Large soft shadows.
- Rounded pill cards.
- Pastel status colors.
- Generic dashboard icon clutter.

### Charts

Charts should feel native to a dark trading dashboard.

Style:

- Transparent or charcoal background.
- Muted gridlines.
- White or muted axis labels.
- Mono axis labels where possible.
- Orange for primary revenue/volume.
- Lime for positive growth or active series.
- Blue for secondary comparison.
- Avoid rainbow categorical palettes.

Suggested chart palette:

```css
--chart-primary: #ff531c;
--chart-positive: #b3e562;
--chart-secondary: #0085ff;
--chart-neutral: rgba(255, 255, 255, 0.72);
--chart-grid: rgba(255, 255, 255, 0.08);
```

### Tables

Tables should feel like market data.

Style:

- Dark background.
- Dense row spacing.
- Uppercase column headers.
- Mono numeric values.
- Thin row separators.
- Lime/orange delta colors.
- Keep borders subtle.

Recommended table treatments:

- Right-align numeric columns.
- Use tabular numbers if available.
- Use compact badges for status.
- Use avatars only when they support athlete/issuer recognition.

### Buttons and Controls

Buttons should be stark and functional.

Primary button:

- White background.
- Black text.
- Uppercase.
- Pill radius only for true action buttons.

Secondary button:

- Transparent or dark panel.
- White border.
- White text.

Filters:

- Dark input backgrounds.
- Thin white translucent border.
- Mono labels.
- Compact sizing.

Tabs:

- Uppercase mono labels.
- Active underline in orange.
- No large tab cards.

## Image Usage

Images on the public site are direct athlete/creator cards, not abstract stock imagery. For dashboard use:

- Use athlete or issuer images as avatars, leaderboard thumbnails, or profile detail surfaces.
- Keep them crisp and visible.
- Avoid dark blurred background images behind data.
- Avoid decorative image collages in dashboard panels.
- Use the saved images as tone references rather than required production assets.

Recommended image placements:

- Leaderboard row thumbnail.
- Issuer detail side panel.
- Token profile header.
- Top mover card.
- Watchlist item avatar.

## Analytics Dashboard Example Structure

Recommended page hierarchy:

```text
Header
  ATHL Data Platform
  Date range selector
  Environment/status
  Refresh/export controls

North-Star Band
  Token Economic Activity
  Current value
  Delta vs previous period
  Short definition

KPI Tile Grid
  Gross Transaction Volume
  Monthly Active Traders
  Total Token Revenue
  Active Tokens
  Net New Users
  Active Issuers
  Verification Pass Rate
  Revenue Concentration

Marketplace Momentum
  Volume over time area chart
  Top tokens by volume bar chart

Growth and Issuer Ecosystem
  User growth line chart
  Issuer mix chart

Trust and Risk
  Verification status chart
  Suspended/review-needed table

Market Data Tables
  Token leaderboard
  Issuer leaderboard
  Recent transactions
```

## Copywriting Style

Use short, confident, data-native language.

Good:

- `MARKETPLACE MOMENTUM`
- `TOKEN ECONOMIC ACTIVITY`
- `ACTIVE ISSUERS`
- `TOP TOKENS`
- `WATCHLIST`
- `CURRENT PRICE`
- `PRICE CHANGE`
- `TOKENS SOLD`
- `TOKENS AVAILABLE`

Avoid:

- Long instructional UI text.
- Marketing explanations inside the dashboard.
- Friendly SaaS filler.
- Excessive helper text.

## Implementation Notes for Another Agent

If implementing in React, Streamlit, Dash, or another framework:

1. Start by applying global dark tokens.
2. Load ATHL-like fonts.
3. Replace all light cards with charcoal market tiles.
4. Make KPI labels mono uppercase.
5. Make numeric values condensed and large.
6. Retune chart colors to orange, lime, blue, white, and gray.
7. Keep tables dense and dark.
8. Use the saved images only where they reinforce athlete/issuer identity.
9. Verify mobile and desktop layouts for text overflow.
10. Avoid decorative gradients, oversized heroes, and generic SaaS panels.

## Quick CSS Starter

```css
body {
  background: #000;
  color: #fff;
  font-family: "Roboto", Arial, sans-serif;
}

.dashboard-shell {
  background:
    linear-gradient(180deg, rgba(255, 83, 28, 0.08), rgba(0, 0, 0, 0) 280px),
    #000;
}

.panel {
  background: linear-gradient(180deg, rgba(255,255,255,0.075), rgba(255,255,255,0.025));
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
}

.kpi-card {
  min-height: 148px;
  padding: 16px;
  border-top: 3px solid var(--athl-orange);
}

.kpi-label {
  color: rgba(255,255,255,0.38);
  font-family: "DM Mono", monospace;
  font-size: 12px;
  text-transform: uppercase;
}

.kpi-value {
  color: #fff;
  font-family: "Chakra Petch", "Roboto Condensed", sans-serif;
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.delta-positive {
  color: #b3e562;
}

.delta-negative {
  color: #ff531c;
}
```

## QA Checklist

Before handing off an ATHL-styled dashboard, verify:

- The first viewport shows real dashboard content, not a landing page.
- Backgrounds are black/charcoal, not white or pale gray.
- KPI values use large condensed display type.
- Labels are compact, uppercase, and mono.
- Orange, lime, and blue are used with restraint.
- Tables remain readable in dark mode.
- Chart axes and legends are visible on black.
- Text does not overflow buttons, cards, tabs, or filters.
- Cards use restrained radius, ideally 8px or less.
- Images are athlete/issuer-specific and not abstract filler.
