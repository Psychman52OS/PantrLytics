# PantrLytics Changelog

## 2025.11.3
- Header layout with 100px icon spanning title/nav; bump for HA refresh. Added root icon.png for repo tile.

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
