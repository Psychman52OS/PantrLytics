# PantrLytics (Home Assistant add-on)

Inventory tracker with on-demand label generation and IPP printing. Built for Home Assistant ingress.

License: Personal use only (non-commercial). See LICENSE.

---

## Add-on install (Home Assistant)

1) **Add repo**: Supervisor → Add-on Store → “Repositories” → `https://github.com/Psychman52OS/PantrLytics`.
2) **Install**: Select “PantrLytics” and install.
3) **Network mapping (critical for QR codes)**:
   - Map a host port to container port `8099` (container always listens on 8099).
   - Example: host `8099` → container `8099`. Whatever host port you map is the one you must use in `base_url`.
4) **Configuration**:
   - `base_url` (strongly recommended): Use a direct, reachable URL with the correct host and mapped port, e.g. `http://192.168.1.10:8099`. Avoid ingress URLs for QR codes. If you use a reverse proxy with HTTPS, use that URL instead (e.g. `https://your.domain:443`).
   - `ipp_host` / `ipp_printer` (optional): IPP host:port and queue name for direct printing. If unset, print actions return PNG previews.
   - `serial_prefix` (optional): Prefix for new serials/barcodes (default `USERconfigurable-`).
   - `workers` (optional): Gunicorn workers (default 2).
5) **Start** the add-on. Open via “Open Web UI” (ingress) or `http://<HA-host>:<mapped-port>/`.
6) **Secure admin**: Default admin password is `password`. Go to Admin → “Admin password” and change it immediately.

### QR codes and `base_url` explained (don’t skip)
- The QR code encodes `base_url` + `/item/<id>`. If `base_url` is wrong, scans will fail (401s, timeouts, or blank pages).
- Use the HA host’s LAN IP plus the mapped port: e.g., `http://192.168.1.10:8099`. Include the port every time.
- If you front this with HTTPS (reverse proxy), set `https://your-domain:<port>` so the QR matches the TLS endpoint.
- Ingress URLs (`/api/hassio_ingress/...`) need short-lived tokens and often fail when scanned; prefer a direct reachable address.
- After changing `base_url`, **reprint labels** so the QR codes carry the new URL.

### In-app QR scanning (mobile)
- On mobile, a floating “Scan” button appears on the home page (bottom-right). Tap to open the in-app camera scanner.
- Grants camera access when prompted; scans QR codes and opens the matching item inside the app (no browser handoff).
- Works best over HTTPS (ingress is fine) so Safari/Chrome allow camera access.

---

## Using the app (all pages and controls)

### Home page (inventory list)
- Search by name, serial, barcode, tags, notes, category, location, bin, unit, or dates.
- Quick filters: categories, locations, bins, use-within, depleted reason, and show/hide depleted.
- Columns: configurable in Admin → Main table columns (show/hide/reorder).
- Quantity +/-: appears only for units marked **Adjustable** in Admin → Units. When off, buttons hide for that unit.

### Items
- **Create**: Click **New item**; fill name, category, location, bin, quantity, unit, condition, cook/use-by dates, use-within, tags, notes, and photos. Required fields are enforced per Admin settings.
- **Edit**: Open item → Edit. Photos can be added/replaced; tags/fields updated.
- **Deplete/Recover**: Mark depleted with reason (qty → 0). Recover restores quantity. Depleted list lives under “Depleted.”
- **Delete**: Permanently remove item and photos.

### Units (drives +/- buttons)
- Admin → Units: add/edit/delete units, drag to reorder, toggle **Adjustable** to control +/- visibility.
- Any unit already on items (e.g., grams) is auto-added to the list (non-adjustable by default) so you can toggle it.

### Labels
- Item page: **Preview Label** (PNG) or **Print Label** (with copy count). Multiple copies are one CUPS job.
- QR code uses `base_url`. If scans fail, fix `base_url`/port and reprint.

### Reports page
- **Horizon**: 7/14/30/60/all days for expiry risk.
- **KPIs**: Expired, ≤7d, ≤14d, ≤30d, ≤60d, total in view.
- **Use-by compliance**: % of items not past their use-by date (non-depleted).
- **Aging waterfall**: Age distribution bars.
- **Heatmap**: Category × Location counts for expiring items.
- **Depletions**: Counts, avg days on hand (cook date preferred, otherwise entry date), reasons (click to drill into items), recent depleted list.
- **Upcoming risk (top 25)**: Soonest-to-expire items sorted by days remaining.

### Admin sections (everything configurable)
- **Main table columns**: Show/hide and reorder columns on the home page.
- **Required fields**: Choose which fields are mandatory on new/edit.
- **Theme**: Light/Dark toggle.
- **App heading**: Custom text on the main page.
- **Categories / Bins / Locations / Use Within**: Add, edit (modal), delete, drag to reorder. Renames update existing items.
- **Units**: Add/edit/delete, reorder, toggle **Adjustable** (controls +/- buttons). Auto-captures any unit seen on items so you can manage it.
- **Admin password**: Change from the default.

### Backup, restore, and CSV
- **Backup page**:
  - Create zip backups (DB, photos, options, CSV export) and download.
  - Restore from a zip created by the app.
  - Delete all items/photos (irreversible).
- **CSV export/import**:
  - Export: choose fields and download.
  - Import: headers must match export; missing serials auto-generate. Categories/bins/locations/units are upserted.

---

## Printer setup (IPP/CUPS over local network)

1) Share your printer via CUPS/IPP:
   - Enable sharing: `cupsctl --remote-admin --remote-any --share-printers`.
   - Add printer in CUPS (`http://<cups-host>:631/admin`) and print a test page.
   - Note queue name and host:port (default 631).
2) In add-on config:
   - `ipp_host`: e.g., `192.168.1.50:631`
   - `ipp_printer`: queue name, e.g., `DYMO_LabelWriter_450`
3) Restart the add-on. Print from an item; IPP sends directly. If unreachable/unset, you get a PNG instead.
4) Troubleshoot: verify LAN reachability, queue name, CUPS sharing/firewall, and check add-on logs for IPP errors.

---

## CSV import/export (Backup page)

- Export selected fields to CSV.
- Import expects matching headers. Missing serials auto-generate; categories/bins/locations/units are upserted if new.
- Success message shows items added/skipped.

---

## Local development (optional)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
export DATA_DIR="$(pwd)/data"   # optional: keep data in repo instead of /data
./run.sh  # serves on http://localhost:8099
```
