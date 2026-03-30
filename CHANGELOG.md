# PantrLytics Changelog

## 2026.03.30-5

### Quick Edit — Auto-save
- **No more Save/Cancel buttons** — removed the per-row Save/Cancel buttons from Quick Edit mode; the actions column stays unchanged while editing
- **Auto-save on field change** — text and number fields save automatically when you click away (blur); date fields save as soon as a date is picked (change event)
- **Visual feedback** — the edited cell briefly dims while saving, then flashes green on success or red on failure; no alert dialogs
- **Unchanged fields skipped** — if you click into a field and leave without changing the value, no network request is made
- **State stays correct across saves** — after each auto-save the row's stored item data updates so subsequent edits to other fields in the same row merge cleanly

## 2026.03.30-4

### Quick Edit Overhaul
- **Global Quick Edit toggle** — replaced per-row ✏ Edit buttons with a single "✏ Quick Edit" toggle button in the view-toggle bar (desktop only, next to the Filters button)
- **All rows editable at once** — activating Quick Edit mode turns every non-depleted list row editable simultaneously; each row gets its own Save / Cancel in the actions column
- **Mode persists across saves** — after saving a row (which triggers an AJAX results refresh), Quick Edit mode stays active and re-applies to the refreshed rows
- **Toggle off cancels all** — clicking Quick Edit again cancels all in-progress edits and restores display mode

### UI Fix
- Filters button and Quick Edit button now turn orange when active, matching the List/Grid view toggle highlight behaviour

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

## 2026.03.30-1

- Version re-release — no functional changes; bumped because the `2026.03.30` Docker image tag had already been published before all changes were complete

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
- **Inventory Health Score** (0–100, letter grade A–F) combining use-by compliance (50%), date coverage (30%), and audit freshness (20%)
- **Action items banner** surfaces the most urgent issues at a glance: expired items still in stock, items expiring within 7 days, items missing use-by dates, and high waste rate alerts
- **Interactive Chart.js charts** replace CSS-only bars: compliance donut, aging distribution horizontal bar, depletion trend line (last 12 weeks), and top consumed items bar
- **Category and location compliance tables** show total, expired, and no-date counts with inline percent bars; sorted worst-first
- **Waste rate metric** tracks what percentage of depletions happened after the item's use-by date
- **Depletion velocity trend** — items consumed per week over the past 12 weeks (global, all time)
- **Top consumed items** — most-depleted item names by depletion event count
- **"Mark all expired depleted"** bulk action button on the reports page
- **Export report as CSV** — downloads active items in current view filtered by horizon/category/location
- Filters now auto-submit on dropdown change (no Apply button needed)

### Swipe Gestures
- **Configurable swipe actions** — new Admin section lets users set independent actions for left-swipe and right-swipe: Edit, Mark depleted, Open details, Print label, or No action
- **Desktop swipe support** — swipe gestures now work on desktop/touchscreen workstations via click-drag (pointer events with `setPointerCapture`)
- **List row swipe feedback** — list rows now show the same icon/label overlay as grid cards during a swipe; uses a `position: fixed` overlay positioned via `getBoundingClientRect` to work around `<tr>` DOM constraints
- Grab cursor on swipeable elements on desktop; suppressed on touch screens

### UI & Navigation
- **AJAX live search** — search results swap in place with no page reload or flash; 350ms debounce
- **List/Grid toggle** — switch between a compact table view and a responsive card grid with photo thumbnails; preference persists via `localStorage`
- **Mobile bottom tab bar** — replaces hamburger menu with a sticky bottom nav (Items, New, Designer, Reports, More); More tab opens a slide-up sheet for Admin, Backup, and Depleted Items
- **Quick-filter chips** — horizontal scrollable category and location chips on mobile; collapsible filter panel on desktop (auto-opens when filters are active)
- **Sidebar action panel** on item detail page — sticky action group with all item actions (print, deplete, edit, delete); replaces flat action rows
- **Deplete from list** — deplete button with date/time dialog directly on the home page rows and mobile cards
- **Card grid** — photo thumbnails, expiry badge, category/location, quick actions all in a scannable card layout

### Photos & Thumbnails
- **Set primary thumbnail** — star (★) button on each uploaded photo; clicking sets it as the card grid thumbnail
- **Default item icon** — configurable in Admin: choose from a grid of 40 food/pantry emojis or upload a custom PNG/JPG
- Cache-busting on thumbnail URLs so grid cards update immediately after changing the primary photo

### Admin & Settings
- **Font size controls** — global base font size plus per-page overrides for the inventory list and item detail pages; applied as a CSS variable
- **Swipe action configuration** — choose what fires on left-swipe and right-swipe independently
- **Unit management** — add, edit, reorder units; toggle which units show quantity +/− buttons

### Backup & Restore
- WAL-safe database snapshots using `VACUUM INTO` (eliminates WAL/SHM consistency issues during backup)
- Robust restore flow: `engine.dispose()` after DB file copy, stale WAL/SHM cleanup, Supervisor API options push
- HA Supervisor API calls moved to `urllib` to avoid missing-dependency failures
- Repair DB endpoint (`/repair-db`) for corrupted databases
- CSV import fix: corrected label/key mismatch that silently skipped rows

### Bug Fixes
- Fix sticky header disappearing after scrolling past one viewport height (`body: height:100%` → `min-height:100%`)
- Fix grid card dropdown menu being clipped by `overflow:hidden` on the card container
- Fix thumbnail star fetch using full URL (broke under HA ingress due to scheme mismatch; now pathname-only)
- Fix CSV import rows being silently skipped due to column label/key mismatch

 only host mapping in HA UI; app stays on 8099 internally.
