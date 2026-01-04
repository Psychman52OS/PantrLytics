# PantrLytics Changelog

## 2026.01.01
- Add an in-app mobile QR scanner (floating FAB, bottom-right) that opens the scanned item inside the app; version bump.

## 2026.01.02
- Fix the in-app scanner overlay so it actually opens on mobile (remove hidden flag, clearer errors); version bump.

## 2026.01.03
- Fix ingress scanning URL to respect the HA ingress root path (no more `//` redirects); version bump.

## 2025.12.33
- Use cook date (fallback to entry date) when calculating days on hand for depleted items in reports and the depleted list; keep edit modal items attached to avoid DetachedInstanceError; version bump.

## 2025.12.31
- Ensure default units (ounces, bottles, jugs, grams, etc.) are backfilled into existing databases so the admin unit list shows all standard units by default.

## 2025.12.32
- Reframe report compliance to track items past their use-by date (not depleted) and update the Reports label to “Use-by compliance”.

## 2025.12.30
- Fix unit normalization cleanup so duplicate/empty units are removed on startup and the admin list only shows real units; add local pytest env.

## 2025.12.25
- Ignore 1-character/empty units when backfilling into the admin list; adjustable toggles still control +/- visibility per unit.

## 2025.12.26
- Prune existing 1-character/empty unit rows and backfill without noise; +/- buttons remain driven by the unit toggle.

## 2025.12.27
- Run unit hygiene on startup (seed defaults, prune noise, backfill all units from items) so the admin list shows every real unit and toggles continue to hide/show +/- buttons.

## 2025.12.28
- Normalize unit names (trim/merge duplicates) and prune single-character entries before backfilling, so admin shows only real units and toggles map cleanly to +/- buttons.

## 2025.12.29
- Add detailed unit snapshot logging at startup and normalize/prune before backfill so only real units appear; version bump.

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
- Version bump.

## 2025.12.10
- Enable +/- quantity buttons for canned items by treating "can"/"cans" as adjustable units.
- Version bump.

## 2025.12.9
- Add lightweight polling endpoint plus front-end script so the inventory list auto-refreshes after adds/edits.
- Version bump.

## 2025.12.8
- Fix new item creation redirect by storing the item ID before closing the session (prevents DetachedInstanceError).
- Version bump.

## 2025.12.7
- Fix ingress redirects by using request-aware URLs for item actions; better logging for redirects.
- Version bump.

## 2025.12.6
- Expand request logging (root path, referer, forwarded headers, redirect target) to debug recover redirect/404s.
- Version bump.

## 2025.12.5
- Add debugging logs for recover/show flows to trace post-deplete recover 404s.
- Version bump.

## 2025.12.4
- Avoid rendering missing photo thumbs on depleted items to prevent 404s when viewing after deplete/recover.
- Version bump.

## 2025.12.3
- Skip missing photo files when showing depleted items to avoid 404s; prefer newest existing photo.
- Version bump.

## 2025.11.11
- Header grid tweaks: align title and nav horizontally, larger nav text, slogan remains italic next to title. Version bump.

## 0.6.43
- Enable SQLite WAL + sync tweak; add photo upload size limit; cache-control for CSS.
- Version bumps for HA add-on.

## 0.6.42
- GZip middleware and SQLite indexes to speed responses; image publishing workflow fixed for GHCR.

## 0.6.41
- Backup page now requires Admin auth; README notes to change the default password.
- Version bumps for HA add-on.

## 0.6.40
- Label presets restyled with switches; add explicit printer side (auto/left/right) for twin-roll printers.
- Default can be switched from the preset cards; printer slot now honors preset override.

## 0.6.39
- Add “Delete all items” action (with warning) on Backup page to wipe all items/depleted entries and photos.
- Version bumps for HA add-on.

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
