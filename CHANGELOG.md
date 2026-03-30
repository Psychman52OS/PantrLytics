# PantrLytics Changelog

## 2026.03.30-3

### Bug Fix
- Fix cook date and use-by date showing blank in the edit modal — browsers do not reliably initialise `<input type="date">` from a `value` attribute set via `innerHTML`; the modal loader now explicitly sets `.value` via JavaScript after injection

## 2026.03.30-2

### Per-Item Review Window
- **Quick-select buttons on New/Edit forms** — choose 15d, 30d, 60d, or 120d review interval per item; highlighted button shows active selection; leave blank to inherit the admin-level default
- **Per-item window respected everywhere** — the Review page and health score audit component both use each item's own interval where set, falling back to the global default
- **Item detail page** — read-only "Last reviewed" and "Next review" rows added; "Next review" shows the calculated date plus a countdown pill (`in Xd`, `Due today`, or `Xd overdue`)

### Bug Fix
- Fix health score card showing hardcoded "50%" for the compliance component — now shows the actual use-by compliance rate; the 50% is the formula weight, not the score

## 2026.03.30

### Desktop Quick Edit
- **Inline row editing** — desktop list view only; clicking ✏ Edit on a row converts every visible cell into an appropriate input (text, date, or number); edited row gets a subtle accent tint
- **Save via fetch** — no page navigation; on success the results region refreshes in place; Cancel restores the original cell HTML instantly
- **Read-only fields preserved** — `last_audit_date` stays as plain text in quick-edit mode

### Item Review System
- **Review page** — surfaces all active items not touched within the configured window; "Needs review" and "Recently reviewed" sections; accessible from desktop nav and the mobile More sheet
- **Mark Reviewed** — stamp today's date on an item and clear it from the queue; **Mark all reviewed** bulk action at the top of the page
- **Auto-stamping** — creating, editing, or depleting an item automatically counts as a review
- **Configurable review window** — Admin → Review window (7–365 days, default 30)
- **Audit freshness score** — health score "Reviewed" component reflects actual review stamps

### Reports Improvements
- **Inventory Health Score** (0–100, letter grade A–F) — three components: use-by compliance (50%), date coverage (30%), audit freshness (20%); each shows its real percentage in the card
- **Action items panel** — expired, expiring, no-date, and high-waste alerts; each alert is tappable and opens the matching item list
- **Most Consumed Categories** — consumption chart now groups by category instead of item name
- **Compliance by category/location tables** — total, expired, no-date counts with inline percent bars; sorted worst-first
- **Waste rate** — tracks depletions that occurred after the item's use-by date
- **Depletion velocity trend** — items consumed per week over the last 12 weeks
- **Wider desktop layout** — content area expanded from 1100 px to 1400 px
- **Mobile layout fixes** — health score card full width; no horizontal overflow; KPI strip uses fixed 3-column grid
- **"No use-by date" alert** drills down to only items missing a date

### Bug Fixes
- Fix backup restore hanging in Home Assistant — removed `os.execv` restart; redirects immediately on success
- Fix Review page 500 — `url_for('edit_item')` corrected to `url_for('edit_item_form')`

## 2026.03.27

### Reports — Complete Overhaul
- Inventory Health Score (0–100, A–F) combining compliance, date coverage, and audit freshness
- Interactive Chart.js charts: compliance donut, aging distribution bar, depletion trend line, top consumed bar
- Category and location compliance tables sorted worst-first
- Waste rate, depletion velocity trend, top consumed items
- "Mark all expired depleted" bulk action; Export report as CSV
- Filters auto-submit on change

### Swipe Gestures
- Configurable left/right swipe actions (Edit, Deplete, Open, Print, or None) set in Admin
- Desktop swipe via click-drag using pointer events
- List row swipe shows icon/label overlay via fixed-position overlay

### UI & Navigation
- AJAX live search with 350ms debounce; no page reload
- List/Grid toggle; grid shows photo thumbnails, expiry badges, quick actions; preference persists
- Mobile bottom tab bar (Items, New, Designer, Reports, More); More sheet for Admin, Backup, Depleted, Review
- Quick-filter chips (categories, locations) with collapsible desktop panel
- Sidebar action panel on item detail page
- Deplete button with date/time dialog directly on list rows and mobile cards

### Photos & Thumbnails
- Set primary thumbnail via star (★) button; cache-busted thumbnail URLs
- Default item icon — choose from 40 food/pantry emojis or upload a custom image

### Admin & Settings
- Font size controls (global + per-page overrides)
- Swipe action configuration
- Unit management — add, edit, reorder; toggle which units show +/− buttons

### Backup & Restore
- WAL-safe snapshots using `VACUUM INTO`
- Repair DB endpoint for corrupted databases
- CSV import fix: corrected label/key mismatch that silently skipped rows

### Bug Fixes
- Fix sticky header disappearing after scrolling past one viewport height
- Fix grid card dropdown clipped by `overflow:hidden`
- Fix thumbnail star fetch breaking under HA ingress
- Fix CSV import rows silently skipped

## Earlier releases (through 2026.01)

Unit system, backup/restore, CSV import/export, admin auth, WAL mode, photo uploads, multi-copy printing, QR code generation, pagination, ingress-safe redirects, and various startup/session stability fixes across the 2025.12.x and 2026.01.x series.
