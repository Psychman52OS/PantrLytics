# PantrLytics Changelog

## 2026.03.30-14

### Bug Fixes
- **Grid card action dropdown rendered behind adjacent cards** — the dropdown uses `position:fixed` to escape the card's `overflow:hidden`, but still paints within its ancestor's stacking context; sibling cards later in DOM order painted on top of it; fixed by temporarily setting `z-index:10` on the active card when its dropdown opens (and resetting on close), lifting its stacking context above all sibling cards

## 2026.03.30-13

### Bug Fixes
- **Grid card ⋯ Actions dropdown broken** — `.swipe-inner` had `will-change: transform` in CSS; in Chromium, this creates a new containing block for `position: fixed` descendants, so the dropdown (which uses fixed positioning to escape the card's `overflow: hidden`) was positioned relative to `.swipe-inner` instead of the viewport — rendering off-screen; removed `will-change: transform` from `.swipe-inner` (the swipe animation works fine without it)
- **Reports "No Use-by Date" bucket empty** — the bucket was additionally gated on `if it.origin_date`, so items with no use-by date but also no origin date were never included; removed the origin_date guard so all active items with a NULL use-by date are flagged

## 2026.03.30-12

### Bug Fixes
- **Edit save always returned 422** — `review_window_days` was declared as `Optional[int] = Form(None)` in both the edit and new-item routes; Pydantic v2 cannot coerce an empty string `""` to `None` for `Optional[int]`, so any item without a review window set would fail FastAPI validation before the route function ran; changed both parameters to `Optional[str]` and parse to int manually in the route body
- **Reports "No Use-by Date" bucket showing wrong items** — the bucket was gated on `_expiry_info()` returning `None` (bare `else`), which is true for both genuinely NULL `use_by_date` AND for dates that are set but cannot be parsed (e.g. imported via CSV in a non-ISO format); items with a malformed date would appear as if they had no use-by date at all; changed gate to `elif not it.use_by_date` so only items with a truly NULL use-by date are included

## 2026.03.30-11

### Bug Fixes — Origin Date
- **Save failed on edit** — the `init_db()` migration block was missing `conn.commit()`; in SQLAlchemy 2.x the `ALTER TABLE` statements that add `origin_date` and `origin_date_label` columns are not committed automatically on connection close, so the columns never existed in the live database and every item save threw a DB error; explicit `conn.commit()` added at the end of the migration block
- **cook_date data not migrating** — same missing commit; the `UPDATE item SET origin_date = cook_date` data migration was also rolled back; now committed correctly so all historical cook dates populate origin_date on first startup after upgrade
- **Label showing "Origin Date" instead of "Cooked On"** — `show.html` fell back to the literal string `"Origin Date"` for items whose `origin_date_label` is still NULL; changed fallback to `"Cooked On"`
- **Label dropdown in edit modal had no effect** — scripts injected via `innerHTML` do not execute in browsers; the select→hidden-input sync JS in `edit_form.html` never ran, so changing the dropdown had no effect; moved the initialization into `layout.html`'s `openModal` function which runs explicitly after `body.innerHTML = html`

## 2026.03.30-10

### Bug Fixes
- **Grid view ⋯ Actions button** — dropdown was silently clipped by `overflow:hidden` on the card container (required for swipe gestures); fixed by using `position:fixed` via JS when opening a dropdown inside a grid card, allowing it to escape the clipping context
- **Reports — No Use-by Date bucket** — items with no dates at all (no origin date and no use-by date) were appearing in the "No Use-by Date" action bucket; the bucket now only includes items that have an origin date but are missing a use-by date, making the action list genuinely actionable

## 2026.03.30-9

### Flexible Origin Date field

- **Renamed "Cook Date" → "Origin Date"** — the field is now called *Origin Date* throughout the UI and database; existing `cook_date` values are automatically migrated to `origin_date` on first startup; no data loss
- **Per-item label** — each item can independently label its origin date: choose from a dropdown (Cooked On, Purchased On, Opened On, Made On, Frozen On, Received On, Prepared On, Picked On, Brewed On) or type a custom label; the label is shown on the item detail page instead of a static "Cook Date" heading
- **Admin — Origin Date Labels section** — manage the dropdown list (add, edit, delete, drag to reorder); changes propagate to any items using that label
- **Label printing** — the printed label uses the item's actual origin date label text instead of the hardcoded "Cook:"
- **CSV import backward compatibility** — imports with a `cook_date` column still work; `origin_date` column is preferred when present
- **Quick Edit + filters** — the `origin_date` column is editable in Quick Edit mode and filterable in the advanced filters panel

## 2026.03.30-8

### Bug Fix
- Fix Quick Edit: `data-item` attribute was broken HTML — `tojson` returns a `Markup` object so `| e` was a no-op, leaving raw JSON `"` characters inside a double-quoted attribute; browser read only the first `{` character; every `JSON.parse` call threw silently; changed to `| forceescape` which always escapes `"` → `&quot;` regardless of Markup status

## 2026.03.30-7

### Quick Edit — Complete interaction fix
- **Nuclear swipe disable** — swipe handlers now check `_quickEditActive` as their very first instruction; entire swipe system goes dark the moment Quick Edit is on, restores automatically when off
- **Event delegation** — replaced per-input `blur`/`change`/`click` listeners with three document-level delegated handlers (blur in capture phase, change, click-to-focus); no listeners are lost due to DOM timing or JS errors
- **Error isolation** — each row's `_qeStartEdit` is wrapped in try/catch so a failure on one row never aborts the others

## 2026.03.30-6

### Bug Fix
- Fix Quick Edit inputs being unclickable — the desktop swipe handler was calling `setPointerCapture` on the row when clicking cell padding, swallowing focus from the input; swipe now backs off when a row is in edit mode; each editable cell also gets a click handler that explicitly focuses its input

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

## 2026.01.11
- Default theme now follows the browser's color scheme when no preference is saved; version bump.

## 2026.01.10
- Run DB initialization before startup migrations/unit seeding so fresh installs don't crash; version bump.

## 2026.01.09
- Set admin auth cookie path to "/" so ingress/direct both honor login and backup redirect works; version bump.

## 2026.01.08
- Set admin auth cookie path to the ingress root so login persists under HA ingress; version bump.

## 2026.01.07
- Fix admin redirect so `next=backup` correctly lands on the Backup page; version bump.

## 2025.12.33
- Use cook date (fallback to entry date) when calculating days on hand for depleted items in reports and the depleted list; keep edit modal items attached to avoid DetachedInstanceError; version bump.

## 2025.12.32
- Reframe report compliance to track items past their use-by date (not depleted) and update the Reports label to "Use-by compliance".

## 2025.12.31
- Ensure default units (ounces, bottles, jugs, grams, etc.) are backfilled into existing databases so the admin unit list shows all standard units by default.

## 2025.12.30
- Fix unit normalization cleanup so duplicate/empty units are removed on startup and the admin list only shows real units; add local pytest env.

## 2025.12.29
- Add detailed unit snapshot logging at startup and normalize/prune before backfill so only real units appear; version bump.

## 2025.12.28
- Normalize unit names (trim/merge duplicates) and prune single-character entries before backfilling, so admin shows only real units and toggles map cleanly to +/- buttons.

## 2025.12.27
- Run unit hygiene on startup (seed defaults, prune noise, backfill all units from items) so the admin list shows every real unit and toggles continue to hide/show +/- buttons.

## 2025.12.26
- Prune existing 1-character/empty unit rows and backfill without noise; +/- buttons remain driven by the unit toggle.

## 2025.12.25
- Ignore 1-character/empty units when backfilling into the admin list; adjustable toggles still control +/- visibility per unit.

## 2025.12.24
- Keep admin query objects attached (no expire-on-commit) to prevent DetachedInstanceError when loading /admin.

## 2025.12.23
- Keep items attached during home page rendering to prevent DetachedInstanceError on the inventory list.

## 2025.12.22
- Prevent session expiration during unit backfill to avoid DetachedInstanceError when rendering the home page.

## 2025.12.21
- Prevent duplicate unit inserts during item-unit backfill to avoid startup 500s (UNIQUE constraint).

## 2025.12.20
- Backfill units from existing items into the admin list and keep +/- toggles in sync so any unit can be made adjustable (or not).

## 2025.12.19
- Fix startup/render crash by seeding default units without expiring existing session objects.

## 2025.12.18
- Add Admin controls to manage units (add/edit/delete, reorder) with a toggle for quantity buttons, and wire those units into item forms and adjustments.

## 2025.12.17
- Submit multi-copy print jobs as a single CUPS job by repeating the label image per page, keeping the queue tidy.

## 2025.12.16
- Derive QR code URLs from ingress/proxy headers so scans resolve correctly through Home Assistant ingress without configuring `BASE_URL`.

## 2025.12.15
- Generate QR codes with item detail URLs (using request context) so scans open the record even without `BASE_URL`.

## 2025.12.14
- Ensure multi-copy printing works with CUPS/IPP by submitting one job per requested label.

## 2025.12.13
- Fix server startup regression by defining `MAX_LABEL_COPIES` before templates import it.

## 2025.12.12
- Allow selecting the number of labels to print per item and clamp jobs to a safe copy limit.

## 2025.12.11
- Keep quantity buttons available regardless of item unit casing by sharing the adjustable unit list with the template.

## 2025.12.10
- Enable +/- quantity buttons for canned items by treating "can"/"cans" as adjustable units.

## 2025.12.9
- Add lightweight polling endpoint plus front-end script so the inventory list auto-refreshes after adds/edits.

## 2025.12.8
- Fix new item creation redirect by storing the item ID before closing the session (prevents DetachedInstanceError).

## 2025.12.7
- Fix ingress redirects by using request-aware URLs for item actions; better logging for redirects.

## 2025.12.6
- Expand request logging (root path, referer, forwarded headers, redirect target) to debug recover redirect/404s.

## 2025.12.5
- Add debugging logs for recover/show flows to trace post-deplete recover 404s.

## 2025.12.4
- Avoid rendering missing photo thumbs on depleted items to prevent 404s when viewing after deplete/recover.

## 2025.12.3
- Skip missing photo files when showing depleted items to avoid 404s; prefer newest existing photo.

## 2025.11.11
- Header grid tweaks: align title and nav horizontally, larger nav text, slogan remains italic next to title.

## 0.6.43
- Enable SQLite WAL + sync tweak; add photo upload size limit; cache-control for CSS.

## 0.6.42
- GZip middleware and SQLite indexes to speed responses; image publishing workflow fixed for GHCR.

## 0.6.41
- Backup page now requires Admin auth; README notes to change the default password.

## 0.6.40
- Label presets restyled with switches; add explicit printer side (auto/left/right) for twin-roll printers.

## 0.6.39
- Add "Delete all items" action (with warning) on Backup page to wipe all items/depleted entries and photos.

## 0.6.38
- Clarify startup logs about container vs host port mapping for HA users.

## 0.6.37
- Fix pagination links to use ingress-safe query params (prevents 500s after redirects).

## 0.6.36
- Show clear CSV import success text (items added/skipped) on Backup page.
- Add add-on metadata links (url + changelog) for HA Store.

## 0.6.35
- Fix ingress-safe redirects for CSV import and backup restore.

## 0.6.34
- Surface app version in /health and /whoami responses.
- Align add-on versions and metadata.

## 0.6.33
- Simplify port configuration: only host mapping in HA UI; app stays on 8099 internally.
