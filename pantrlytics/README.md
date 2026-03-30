# PantrLytics — Home Assistant Add-on

Inventory tracker with on-demand label generation and IPP printing, packaged as a Home Assistant Supervisor add-on.

## Installation

1. In Home Assistant, go to **Supervisor → Add-on Store → Repositories** and add:
   `https://github.com/Psychman52OS/PantrLytics`
2. Find **PantrLytics** in the store and install it.
3. Configure (see below), then start the add-on.
4. Open the web UI via **Open Web UI** (ingress) or `http://<HA-host>:<mapped-port>/`.

## Configuration

| Option | Required | Description |
|---|---|---|
| `base_url` | Recommended | Full URL that QR codes on labels will encode, e.g. `http://192.168.1.10:8099`. Must be reachable by the device scanning labels. |
| `ipp_host` | Optional | CUPS/IPP host and port, e.g. `192.168.1.50:631`. If unset, printing returns a PNG preview. |
| `ipp_printer` | Optional | IPP queue name, e.g. `DYMO_LabelWriter_450`. |
| `serial_prefix` | Optional | Prefix for auto-generated item serials (default `USERconfigurable-`). |

**Network port:** The container always listens on port **8099**. Map any host port to `8099` in the add-on network settings and use that same port in `base_url`.

**Default admin password:** `password` — change it immediately under Admin → Admin password.

## Local testing

```bash
docker build -t pantrlytics:local .
docker run --rm -p 8099:8099 pantrlytics:local
# then visit http://localhost:8099
```
