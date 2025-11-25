# Inventory & Labels (Home Assistant add-on)

Inventory tracker with on-demand label generation and IPP printing. Built for Home Assistant ingress but also runnable locally for development.

## Configuration
- `base_url` (optional): URL used in QR codes and "Direct label URL". For HA mobile, use `homeassistant://navigate/hassio/ingress/<your_addon_slug>`.
- `ipp_host` / `ipp_printer` (optional): IPP host:port and printer name. If unset, print actions return a PNG preview instead of calling `lp`.
- `serial_prefix` (optional): Prefix for new serial numbers and barcodes. Defaults to `USERconfigurable-` (change to anything you want).

All options can also be supplied as environment variables (`BASE_URL`, `IPP_HOST`, `IPP_PRINTER`, `SERIAL_PREFIX`) when running outside Home Assistant. Data is stored under `/data` in the add-on; set `DATA_DIR` if you want a different location when running locally.

## Developing or running locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt

# Optional: keep data in the repo instead of /data
export DATA_DIR="$(pwd)/data"
./run.sh  # serves on http://localhost:8099
```

## What changed for portability
- Removed hard-coded printer/URL defaults; configuration now starts empty.
- Serial numbers are configurable and no longer tied to the original BRUCKkitch prefix.
- Local/dev runs fall back to a repo-local data directory via `DATA_DIR` and fixed `run.sh`.
- The main inventory table columns are user-selectable from Admin → “Main table columns”.
