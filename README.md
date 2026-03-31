# PantrLytics

**Version 2026.03.30-15**

Inventory tracker with on-demand label generation and IPP printing. Runs as a Home Assistant add-on or as a standalone Docker container.

License: Personal use only (non-commercial). See LICENSE.

---

## Standalone Docker install

No Home Assistant required. Runs on any machine with Docker.

**Quick start:**

```bash
# 1. Download the compose file
curl -O https://raw.githubusercontent.com/Psychman52OS/PantrLytics/main/docker-compose.yml

# 2. Create your config (copy the example and edit)
curl -O https://raw.githubusercontent.com/Psychman52OS/PantrLytics/main/.env.example
cp .env.example .env
nano .env   # set BASE_URL at minimum

# 3. Start
docker compose up -d
```

Then open `http://<your-server-ip>:8099` in a browser.

**Key settings (in `.env`):**

| Variable | Purpose | Example |
|---|---|---|
| `BASE_URL` | URL embedded in QR codes on labels | `http://192.168.1.100:8099` |
| `IPP_HOST` | CUPS/IPP printer host:port | `192.168.1.50:631` |
| `IPP_PRINTER` | IPP queue name | `DYMO_LabelWriter_450` |
| `SERIAL_PREFIX` | Prefix for auto-generated serials | `ITEM-` |
| `PORT` | Host port to expose | `8099` |

`BASE_URL` is the most important setting — it gets encoded into printed label QR codes. Set it to the IP:port your barcode scanner or phone can reach. Leave blank if you're only using the web UI.

**Data persistence:** All data (database, photos, backups) is stored in a Docker named volume (`pantrlytics_data`). To use a host directory instead, replace the volume with a bind mount in `docker-compose.yml`.

**Updating:**

```bash
docker compose pull && docker compose up -d
```

**Default admin password:** `password` — change it immediately in Admin → Admin password.

---

## Add-on install (Home Assistant)

1. **Add repo**: Supervisor → Add-on Store → Repositories → `https://github.com/Psychman52OS/PantrLytics`
2. **Install**: Select "PantrLytics" and install.
3. **Network mapping**: Map a host port to container port `8099`. Whatever host port you map must match the port in `base_url`.
4. **Configuration**:
   - `base_url` (strongly recommended): direct reachable URL with the correct host and mapped port, e.g. `http://192.168.1.10:8099`. Avoid ingress URLs for QR codes.
   - `ipp_host` / `ipp_printer` (optional): IPP host:port and queue name. If unset, print actions return PNG previews.
   - `serial_prefix` (optional): prefix for new serials (default `USERconfigurable-`).
5. **Start** the add-on. Open via "Open Web UI" (ingress) or `http://<HA-host>:<mapped-port>/`.
6. **Secure admin**: Default password is `password`. Change it immediately in Admin → Admin password.

### QR codes and `base_url`
- QR codes encode `base_url` + `/item/<id>`. If `base_url` is wrong, scans fail.
- Use the HA host's LAN IP and the mapped port: `http://192.168.1.10:8099`.
- If fronted by HTTPS/reverse proxy, use `https://your-domain:<port>`.
- Ingress URLs need short-lived tokens and often fail when scanned — prefer a direct address.
- After changing `base_url`, reprint labels.

---

## Using the app

### Home page (inventory list)

- **Search**: name, serial, barcode, tags, notes, category, location, bin, unit, or dates.
- **Quick-filter chips**: categories and locations with item counts; collapsible panel on desktop.
- **Views**: toggle between compact List view and card Grid view (with photo thumbnails); preference persists.
- **Columns**: configurable in Admin → Main table columns (show/hide/reorder).
- **Quantity +/−**: appears only for units marked **Adjustable** in Admin → Units.
- **Desktop Quick Edit**: click ✏ Edit on any list row to edit fields inline without leaving the page. Save updates in place; Cancel restores instantly.

### Items

- **Create** (New Item): fill name, category, location, bin, quantity, unit, condition, cook/use-by dates, use-within, tags, notes, photos, and optional per-item review window.
- **Edit**: opens a modal; all fields editable; photos can be added or deleted.
- **Deplete/Recover**: mark depleted with a date, time, and reason (quantity → 0). Recover restores the item.
- **Delete**: permanently removes item and photos.
- **Detail page**: shows last reviewed date, next review due date with a countdown pill (`in Xd`, `Due today`, `Xd overdue`), plus all other item fields.

### Review page

Surfaces items that haven't been touched (created, edited, depleted, or manually reviewed) within the configured window.

- **Needs review** queue: sorted by oldest review date; never-reviewed items appear first.
- **Mark Reviewed** button on each item stamps today's date and removes it from the queue.
- **Mark all reviewed** bulk action clears the entire queue at once.
- **Per-item review window**: set a custom interval (15d / 30d / 60d / 120d) when creating or editing an item to override the global default for that item only.
- **Global default**: Admin → Review window (7–365 days, default 30).

### Reports page

- **Inventory Health Score** (0–100, letter grade A–F) composed of:
  - Use-by compliance (50%) — items not past their use-by date
  - Date coverage (30%) — items that have a use-by date set
  - Audit freshness (20%) — items reviewed within their window
- **Action items panel** — expired, expiring, no-date, and high-waste alerts; each is tappable and opens the matching item list.
- **KPI strip**: Expired / ≤7d / ≤14d / ≤30d / ≤60d / Total in view; each card opens a drill-down list.
- **Charts**: compliance donut, aging distribution bar, depletion trend (last 12 weeks), top consumed categories bar.
- **Compliance tables**: by category and location; worst performers first.
- **Waste rate**: percentage of depletions that occurred after the item's use-by date.
- **Filters**: horizon (7/14/30/60/all days), category, location; auto-submit on change.
- **Export CSV**: downloads active items in the current filtered view.

### Label Designer & Printing

- **Item page**: Preview Label (PNG) or Print Label with copy count. Multiple copies submit as one CUPS job.
- **Label Designer**: customise layout, font sizes, fields shown, and QR code placement. Save as named presets.
- **QR code** encodes `base_url + /item/<id>`. If scans fail, verify `base_url` and reprint.

### Admin sections

| Section | What it controls |
|---|---|
| Main table columns | Show/hide and reorder columns on the home page |
| Required fields | Which fields are mandatory when creating/editing |
| Theme | Light / Dark |
| App heading | Custom title text on the main page |
| Font sizes | Global base size plus per-page overrides for list and detail pages |
| Swipe actions | What left-swipe and right-swipe do on cards and rows (Edit, Deplete, Open, Print, or None) |
| Review window | Default review interval in days (7–365); per-item overrides take precedence |
| Default item icon | Choose from 40 food/pantry emojis or upload a custom image |
| Categories / Bins / Locations / Use Within | Add, edit, delete, drag to reorder; renames update existing items |
| Units | Add/edit/delete, reorder, toggle **Adjustable** (controls +/− buttons) |
| Admin password | Change from the default |

### Backup, Restore & CSV

- **Backup**: create zip (DB, photos, options, CSV export) and download.
- **Restore**: upload a zip created by the app. Works correctly in HA — no restart loop.
- **CSV export/import**: export any field set; import matches on headers, auto-generates serials, upserts categories/bins/locations/units.
- **Delete all items**: irreversible wipe of all items/photos on the Backup page.
- **Repair DB**: `/repair-db` endpoint for corrupted databases.

---

## Printer setup (IPP/CUPS)

1. Share your printer via CUPS: `cupsctl --remote-admin --remote-any --share-printers`
2. Add printer in CUPS (`http://<cups-host>:631/admin`), note queue name and host:port.
3. In add-on config / `.env`: set `ipp_host` (e.g. `192.168.1.50:631`) and `ipp_printer` (queue name).
4. Restart. Print from any item — IPP sends directly. If unreachable, you get a PNG preview instead.

---

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
export DATA_DIR="$(pwd)/data"
./run.sh   # serves on http://localhost:8099
```
