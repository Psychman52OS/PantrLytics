# PantrLytics (Home Assistant add-on)

Inventory tracker with on-demand label generation and IPP printing. Built for Home Assistant ingress.

## Add-on install (Home Assistant)
1) Add this repository in Supervisor → Add-on Store (`https://github.com/Psychman52OS/PantrLytics`).  
2) Install the “PantrLytics” add-on.  
3) In Configuration:
   - `base_url` (optional): URL used in QR codes and the “Direct label URL.” For HA mobile, use `homeassistant://navigate/hassio/ingress/<your_addon_slug>`.
   - `ipp_host` / `ipp_printer` (optional): IPP host:port and printer name for direct printing. If unset, print actions return PNG previews instead of sending to a printer.
   - `serial_prefix` (optional): Prefix for new serials/barcodes (default `USERconfigurable-`).  
   - `workers` (optional): Gunicorn workers (defaults to 2).
4) In Network, map the host port you want to container port 8099 (container always listens on 8099).  
5) Start the add-on, then open via “Open Web UI” (ingress) or `http://<HA-host>:<host-port>/`.
6) **Important:** Set a new Admin password (default is `password`). Go to Admin → “Admin password” and change it immediately after install.

## Using the app
- **Items**: Create/edit items, track quantity, units, locations/bins, tags, cook/use-by dates, photos, depletion, and recovery.  
- **Columns & filters**: Configure visible columns in Admin → “Main table columns.” Use quick filters for categories, bins, locations, and use-within.  
- **Depletion**: Mark items depleted, capture reason, optionally recover later, or delete permanently. Depleted items are listed under “Depleted.”  
- **Reports**: Aging buckets with drill-down modal showing the same columns you configured on the main list.  
- **Quantity adjust**: Inline +/– for units like each/bag/unit/serving; updates without page reload.  
- **Labels**: Generate/print labels per item or via designer presets.  
- **Backup/restore**: Create zip backups (DB, photos, options, CSV export) and restore. Import/export CSV from the Backup page. “Delete all items” wipes all items (including depleted) and photos—irreversible.

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
