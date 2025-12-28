# PantrLytics Changelog

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
