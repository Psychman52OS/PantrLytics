# Getting Started — Standalone Docker

PantrLytics runs as a standalone Docker container on any machine with Docker installed — no Home Assistant required. This guide covers installation using Docker Compose.

---

## Requirements

- Docker and Docker Compose installed on your machine
- A machine that's always on (or on when you need to access the app) — a home server, NAS, or Raspberry Pi works well

---

## 1. Download the Compose file

```bash
curl -O https://raw.githubusercontent.com/Psychman52OS/PantrLytics/main/docker-compose.yml
```

Or create a `docker-compose.yml` manually — see [docker-compose.yml](../../docker-compose.yml) in the repo.

---

## 2. Configure your environment

Download the example config file and edit it:

```bash
curl -O https://raw.githubusercontent.com/Psychman52OS/PantrLytics/main/.env.example
cp .env.example .env
nano .env
```

Available settings in `.env`:

| Variable | Required | Description | Example |
|---|---|---|---|
| `BASE_URL` | Recommended | URL encoded in QR codes on printed labels | `http://192.168.1.100:8099` |
| `IPP_HOST` | Optional | CUPS/IPP print server host:port | `192.168.1.50:631` |
| `IPP_PRINTER` | Optional | IPP queue name | `DYMO_LabelWriter_450` |
| `SERIAL_PREFIX` | Optional | Prefix for auto-generated serials | `ITEM-` |
| `PORT` | Optional | Host port to expose (default: 8099) | `8099` |

### About `BASE_URL`

`BASE_URL` is the URL encoded into every printed label's QR code. It must be reachable by the device doing the scanning — typically your server's LAN IP and port.

- **Use:** `http://192.168.1.100:8099`
- **If using HTTPS/reverse proxy:** `https://pantrlytics.yourdomain.com`
- Leave blank to auto-detect from request headers (less reliable for printed labels).

---

## 3. Start the container

```bash
docker compose up -d
```

Open the app at `http://<your-server-ip>:8099` (or the PORT you configured).

---

## 4. First login

The default admin password is **`password`**.

**Change it immediately:** go to **Admin → Admin password** and set a strong password.

---

## 5. Updating

Pull the latest image and restart:

```bash
docker compose pull && docker compose up -d
```

Your data is stored in a Docker named volume (`pantrlytics_data`) and is not affected by updates.

---

## Data persistence

All data (database, uploaded photos, backups) is stored in a Docker named volume called `pantrlytics_data`. Docker manages the storage location automatically.

**To use a specific host directory instead**, edit `docker-compose.yml` and replace the volume with a bind mount:

```yaml
services:
  pantrlytics:
    volumes:
      - /your/host/path:/data   # replace named volume with a bind mount
```

And remove or comment out the `volumes:` section at the bottom of the file.

---

## Running behind a reverse proxy

If you run PantrLytics behind a reverse proxy (nginx, Traefik, Caddy, etc.):

- The app respects `X-Forwarded-For` and `X-Forwarded-Proto` headers.
- Set `BASE_URL` to the external URL (e.g. `https://pantrlytics.yourdomain.com`) so QR codes work correctly.
- Ensure your proxy forwards `X-Forwarded-Proto: https` so the app knows the external scheme.

---

## Next steps

- [Managing Inventory](managing-inventory.md)
- [Labels and Printing](labels-and-printing.md)
- [Admin and Settings](admin-and-settings.md)
- [Printer Setup](printer-setup.md)
