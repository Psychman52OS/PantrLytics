# Getting Started — Home Assistant Add-on

PantrLytics is a Home Assistant add-on for tracking pantry and household inventory. It runs as a Docker container inside Home Assistant OS and is accessible via the HA sidebar or a direct local URL.

---

## 1. Add the repository

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
2. Click the **⋮ menu** (top right) → **Repositories**.
3. Paste the repository URL and click **Add**:
   ```
   https://github.com/Psychman52OS/PantrLytics
   ```
4. Close the dialog. The **PantrLytics** add-on will appear in the store.

---

## 2. Install the add-on

1. Click **PantrLytics** in the add-on store and click **Install**.
2. Wait for the image to download and install (may take a few minutes).

---

## 3. Configure the add-on

Before starting, go to the **Configuration** tab:

| Option | Required | Description |
|---|---|---|
| `base_url` | Recommended | URL embedded in QR codes on printed labels. Use your HA host's LAN IP and mapped port, e.g. `http://192.168.1.10:8099`. See note below. |
| `ipp_host` | Optional | Hostname and port of your CUPS/IPP print server, e.g. `192.168.1.50:631`. Leave blank for PNG preview only. |
| `ipp_printer` | Optional | IPP queue name, e.g. `DYMO_LabelWriter_450`. |
| `serial_prefix` | Optional | Prefix for auto-generated serial numbers (default: `ITEM-`). |
| `workers` | Optional | Number of Gunicorn workers (default: 2). |

### About `base_url`

`base_url` is what gets encoded into the QR code on every printed label. It must be a URL that the device scanning the label can reach — typically your HA host's LAN IP and the port you mapped.

- **Use:** `http://192.168.1.10:8099`
- **Avoid:** HA ingress URLs (`/api/hassio_ingress/...`) — these require short-lived tokens and fail when scanned.
- If you use HTTPS via a reverse proxy, use `https://your-domain.com` instead.
- Leave blank to auto-detect from request headers (less reliable for labels).

---

## 4. Map the network port

On the **Network** tab, map a host port to container port **8099**:

```
Host: 8099  →  Container: 8099
```

Whatever host port you choose, use that same port in `base_url`.

---

## 5. Start the add-on

Click **Start** on the **Info** tab. Open the web UI via:
- **Open Web UI** button (uses HA ingress)
- Direct URL: `http://<your-ha-host>:8099`

---

## 6. First login

The default admin password is **`password`**.

**Change it immediately:** go to **Admin → Admin password** and set a strong password.

---

## 7. Updating

When a new version is available, the add-on store will show an update badge. Click **Update** on the add-on info page. Your data is stored in a persistent volume and is not affected by updates.

---

## Next steps

- [Managing Inventory](managing-inventory.md)
- [Labels and Printing](labels-and-printing.md)
- [Admin and Settings](admin-and-settings.md)
- [Printer Setup](printer-setup.md)
