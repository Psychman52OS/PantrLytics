# PantrLytics (Home Assistant add-on)

Inventory tracker with on-demand label generation and IPP printing. Built for Home Assistant ingress.

License: Personal use only (non-commercial). See LICENSE.

## Add-on install (Home Assistant)
1) Add this repository in Supervisor → Add-on Store (`https://github.com/Psychman52OS/PantrLytics`).  
2) Install the “PantrLytics” add-on.  
3) Configuration options:
   - `base_url` (recommended): The URL encoded in QR codes and shown as “Direct label URL.” Use a reachable, non-ingress address such as `http://<ha-host>:<mapped-port>` or your reverse proxy HTTPS URL. If you must use ingress, use the HA deep link: `homeassistant://navigate/hassio/ingress/<your_addon_slug>`.
   - `ipp_host` / `ipp_printer` (optional): IPP host:port and queue name for direct printing. If unset, print actions return PNG previews instead of sending to a printer.
   - `serial_prefix` (optional): Prefix for new serials/barcodes (default `USERconfigurable-`).
   - `workers` (optional): Gunicorn workers (default 2).
4) Network: map a host port to container port `8099` (container always listens on 8099). Example: host `8099` → container `8099`.  
5) Start the add-on, then open via “Open Web UI” (ingress) or `http://<HA-host>:<host-port>/`.  
6) **Important:** Set a new Admin password (default `password`) in Admin → “Admin password.”

## Core usage
### Adding and editing items
- From the main page, click **New item**, fill in name, category, location, bin, quantity, unit, dates, notes, and optional photos. Required fields are configurable in Admin → “Required fields.”
- Units are now admin-managed: pick from suggestions or type a new unit; any new unit is saved to Admin → Units.
- Edit an item via the row actions; depleted items can be recovered or deleted.

### Quantity buttons (±)
- The inline +/- buttons appear only for units marked **Adjustable** in Admin → Units. Turn the toggle off to hide the buttons for that unit; turn it on to re-enable them. All units (including ones found on existing items like “grams”) show up in the Units list so you can control the toggle.

### Labels and QR codes
- Each item can print a label or show a PNG preview. The QR code encodes `base_url` + `/item/<id>` (or the ingress deep link if you set it that way).
- For reliable scans outside HA ingress, set `base_url` to a direct, reachable URL with the correct scheme/port (e.g., `http://ha.local:8099` or your HTTPS reverse proxy). If you change `base_url`, reprint labels so QR codes carry the new link.

### Reports
- **Horizon filters:** Choose 7/14/30/60 days or All to control what’s in view.
- **KPIs:** Expired and upcoming expiry buckets.
- **Use-within compliance:** Percentage of items within their intended use-within window.
- **Aging waterfall:** Visualizes age buckets of items.
- **Heatmap:** Category × Location counts for expiring items.
- **Depletions:** Counts, average days on hand, reasons (click to drill down), and recent depleted items.
- **Upcoming risk:** Top 25 soon-to-expire items sorted by days remaining.

### Admin tools
- **Main table columns:** Show/hide and reorder columns on the main list.
- **Required fields:** Choose which fields must be filled on new/edit.
- **Theme:** Light/Dark toggle.
- **App heading:** Custom title on the main page.
- **Categories / Bins / Locations / Use Within:** Add, edit, delete, and drag to reorder. Item values update when you rename entries.
- **Units:** Add/edit/delete units, reorder, and toggle **Adjustable** to control the +/- buttons. New units from items auto-appear here so you can toggle them.
- **Admin password:** Change the default password.

### Backup and import/export
- **Backup page:** Create zip backups (DB, photos, options, CSV export) and download. Restore from a zip created by the app.  
- **CSV export/import:** Export selected fields; import expects matching headers. Missing serials auto-generate; categories/bins/locations/units are upserted.  
- **Delete all items:** On Backup page—wipes all items (including depleted) and photos. Irreversible.

## Printer setup (IPP/CUPS over local network)
1) Ensure your label printer is shared via CUPS/IPP on your LAN (e.g., DYMO/Brother):
   - On a machine with CUPS, enable remote sharing: `cupsctl --remote-admin --remote-any --share-printers`.
   - Add the printer in CUPS (usually at `http://<cups-host>:631/admin`) and confirm you can print a test page.
   - Note the **queue name** and **host:port** (default CUPS port is 631).  
2) In PantrLytics add-on config, set:
   - `ipp_host`: e.g., `192.168.1.50:631`
   - `ipp_printer`: the queue name from CUPS (e.g., `DYMO_LabelWriter_450`).
3) Save and restart the add-on. Use “Print” on an item; if IPP is reachable, jobs go directly to the printer. If IPP is unset/unreachable, the app returns a PNG preview instead of failing.
4) Troubleshooting:
   - From the HA host, ensure the IP and port are reachable (CUPS server firewall must allow LAN, and sharing must be enabled).  
   - Verify the queue name exactly matches CUPS.  
   - If prints don’t arrive, check add-on logs for IPP errors; test raw IPP with `ippfind`/`ipptool` from another machine if needed.

## CSV import/export
- Export: Backup page → choose fields and download CSV.  
- Import: Backup page → “Import items” (headers must match export). Missing serials auto-generate; categories/bins/locations are upserted for filters. A success message shows items added/skipped.

## Local development (optional)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
export DATA_DIR="$(pwd)/data"   # optional: keep data in repo instead of /data
./run.sh  # serves on http://localhost:8099
```
