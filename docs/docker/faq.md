# Frequently Asked Questions — Standalone Docker

---

## Installation and setup

**Q: The container starts but I can't reach the web UI.**
Check the port mapping in `docker-compose.yml`. The default maps host port `8099` to container port `8099`. If something else is using port 8099 on your host, change the host side (left number):
```yaml
ports:
  - "8100:8099"   # host 8100 → container 8099
```
Then open `http://<your-server-ip>:8100`.

**Q: The container exits immediately on startup.**
Run `docker compose logs pantrlytics` to see the error. Common causes:
- Data directory permission error — the container needs write access to the volume.
- Port already in use — change the host port as shown above.

**Q: What is the default admin password?**
`password` — change it immediately via **Admin → Admin password**.

**Q: How do I run PantrLytics without Docker Compose?**
You can use a plain `docker run` command:
```bash
docker run -d \
  --name pantrlytics \
  --restart unless-stopped \
  -p 8099:8099 \
  -v pantrlytics_data:/data \
  -e BASE_URL=http://192.168.1.100:8099 \
  ghcr.io/psychman52os/pantrlytics:latest
```

---

## QR codes and labels

**Q: I scan a label QR code and get a "connection refused" or timeout error.**
The QR code contains the `BASE_URL` from your `.env` file. The device scanning the label can't reach that URL. Fix:
1. Set `BASE_URL` to `http://<your-server-lan-ip>:8099` in `.env`.
2. Restart the container: `docker compose up -d`.
3. Reprint affected labels — old labels still carry the old URL.

**Q: QR codes work on my home network but not remotely.**
For remote access, `BASE_URL` must be a publicly reachable URL. If you use a reverse proxy with a domain name, set `BASE_URL=https://pantrlytics.yourdomain.com`.

**Q: The QR code links to `http://localhost:8099`.**
`BASE_URL` is not set in your `.env`. The app is falling back to the request hostname, which inside the container is localhost. Set `BASE_URL` to your server's LAN IP or domain.

---

## Printing

**Q: The Print Label button does nothing / I only see Preview.**
`IPP_HOST` and/or `IPP_PRINTER` are not set or are unreachable. Check your `.env` file and restart the container. See [Printer Setup](printer-setup.md).

**Q: I updated `.env` but the container still uses old settings.**
Environment variables are read at container start. After editing `.env`, restart: `docker compose up -d`.

**Q: Labels print but are the wrong size.**
The label size is controlled by the active preset in the Label Designer. Open **Designer** and check which preset is set as default. Also verify the paper size in CUPS matches your label stock.

---

## Data and storage

**Q: Where is my data stored?**
In a Docker named volume called `pantrlytics_data`. To see where Docker stores it on disk:
```bash
docker volume inspect pantrlytics_data
```

**Q: How do I move data to a new server?**
Use the in-app backup (creates a zip with database and photos), transfer the zip to the new server, set up Docker Compose there, start the container, and use the in-app restore function.

Alternatively, copy the Docker volume directly:
```bash
# On old server — export
docker run --rm -v pantrlytics_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/pantrlytics-data.tar.gz -C /data .

# On new server — import (after creating the volume)
docker volume create pantrlytics_data
docker run --rm -v pantrlytics_data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/pantrlytics-data.tar.gz"
```

**Q: Can I use a bind mount instead of a named volume?**
Yes. In `docker-compose.yml`, replace the volumes section:
```yaml
services:
  pantrlytics:
    volumes:
      - /your/host/path:/data
```
Remove the `volumes: pantrlytics_data:` declaration at the bottom. Make sure the host path exists and is writable.

---

## Inventory

**Q: Quantity +/− buttons don't appear for some items.**
The +/− buttons only appear for units marked **Adjustable** in Admin → Units. Find the unit in the list and enable the Adjustable toggle.

**Q: I renamed a category/location but old items still show the old name.**
Renaming from Admin updates all existing items automatically. If you see the old name, try a hard refresh (Ctrl+Shift+R / Cmd+Shift+R) to clear the browser cache.

---

## Reports

**Q: The health score seems low even though most items are fine.**
The score penalises items that have no use-by date set (date coverage = 30% of the score). Adding use-by dates to your items will improve it. The audit freshness component (20%) also drops if items haven't been reviewed recently — visit the Review page to clear the queue.

**Q: The depletion trend chart is empty.**
The trend shows the last 12 weeks of depletions. If you haven't depleted any items yet, the chart will be empty.

---

## Review

**Q: Every item shows as "Needs review" after the update.**
Items added before the review system was introduced have no last reviewed date. They all show as needing review on first use. Work through the list using **Mark all reviewed** to clear it, then the queue will only surface items that genuinely haven't been touched.

**Q: Items I just edited still show up in the Needs Review list.**
Editing an item automatically stamps the last reviewed date to today, so they should immediately move to Recently Reviewed. If they don't, try a hard refresh (Ctrl+Shift+R / Cmd+Shift+R).

---

## Updates and maintenance

**Q: How do I update PantrLytics?**
```bash
docker compose pull && docker compose up -d
```
Your data volume is not affected by updates.

**Q: How do I completely remove PantrLytics including all data?**
```bash
docker compose down -v   # removes containers AND the named volume
```
This is irreversible — back up your data first.
