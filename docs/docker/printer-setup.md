# Printer Setup

PantrLytics prints labels over **IPP (Internet Printing Protocol)** via a **CUPS** print server. The container sends print jobs to a CUPS server on your network — it does not connect to USB printers directly.

---

## What you need

- A printer supported by CUPS (most label printers and laser/inkjet printers work)
- A machine on your LAN running CUPS with printer sharing enabled (can be another computer, Raspberry Pi, NAS, or Mac)
- The CUPS server must be reachable from the machine running the PantrLytics container

---

## Step 1 — Set up CUPS on a print server

If you already have CUPS running and sharing printers, skip to Step 2.

**On a Linux machine (or Raspberry Pi):**

```bash
sudo apt install cups
sudo usermod -aG lpadmin $USER
```

Enable remote access and printer sharing:
```bash
sudo cupsctl --remote-admin --remote-any --share-printers
sudo systemctl restart cups
```

Open the CUPS web admin at `http://<cups-host>:631/admin`:
1. Click **Add Printer** and follow the wizard to add your printer.
2. Print a test page to confirm it works.
3. Note the **queue name** (shown in the printer URL, e.g. `DYMO_LabelWriter_450`).

---

## Step 2 — Configure PantrLytics

In your `.env` file, set:

```env
IPP_HOST=192.168.1.50:631
IPP_PRINTER=DYMO_LabelWriter_450
```

Then restart the container:
```bash
docker compose up -d
```

---

## Step 3 — Verify connectivity

Go to **Admin → Health** in the PantrLytics web UI. The **IPP connectivity** row shows whether the app can reach the printer.

- `OK` or `Connected` — printer is reachable, ready to print.
- `Unreachable` or an error — check the values below.

---

## Step 4 — Print a test label

Open any item and click **Preview Label** to confirm label generation works, then **Print Label** to send a job. Check the CUPS job queue at `http://<cups-host>:631/jobs` if nothing prints.

---

## Troubleshooting

**"IPP unreachable" in Admin Health**
- Confirm the CUPS machine is on and the service is running: `sudo systemctl status cups`
- Confirm the Docker host can reach the CUPS machine on port 631: `curl http://<cups-host>:631`
- Check that your firewall/router isn't blocking port 631 between the two machines

**Label prints but looks wrong (wrong size, cut off)**
- Make sure the correct label stock is loaded in the printer
- Check the CUPS printer settings for paper size — set it to match your label roll
- Try a different label preset in the PantrLytics Designer page

**Jobs appear in CUPS queue but don't print**
- Check for paper jams or low ink/ribbon on the printer
- Delete stuck jobs from the CUPS web UI and try again

**Queue name not matching**
- Go to `http://<cups-host>:631/printers` — the queue name is the part of the URL after `/printers/`
- Copy it exactly, including capitalisation and underscores

---

## Using a Mac as a print server

Macs have CUPS built in. Enable sharing:

1. **System Settings → Printers & Scanners** — add your printer.
2. Open Terminal and run:
   ```bash
   sudo cupsctl --remote-any --share-printers
   ```
3. Use your Mac's LAN IP and port 631 as `IPP_HOST`.
4. Find the queue name at `http://localhost:631/printers`.

---

## CUPS on the same machine as Docker

If you want to run CUPS on the same machine as the Docker container, install CUPS on the host and use `host.docker.internal` (Docker Desktop) or the host's LAN IP as `IPP_HOST`.

On Linux with a standard Docker install, use the Docker bridge gateway IP (usually `172.17.0.1`):

```env
IPP_HOST=172.17.0.1:631
```

---

## No printer? Use PNG preview

If you don't have a printer, leave `IPP_HOST` and `IPP_PRINTER` blank in your `.env`. Use **Preview Label** on any item to generate a PNG you can print manually or save.
