# Printer Setup

PantrLytics prints labels over **IPP (Internet Printing Protocol)** via a **CUPS** print server on your local network. The app itself does not talk to USB printers directly — it sends jobs to a CUPS server, which handles the physical printer.

---

## What you need

- A printer supported by CUPS (most label printers and laser/inkjet printers work)
- A machine on your LAN running CUPS with printer sharing enabled (can be another Raspberry Pi, a NAS, a Mac, or a Linux machine)
- The CUPS server must be reachable from your Home Assistant host

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

In the add-on **Configuration** tab, set:

| Option | Value | Example |
|---|---|---|
| `ipp_host` | `<cups-server-ip>:<port>` | `192.168.1.50:631` |
| `ipp_printer` | Queue name from CUPS | `DYMO_LabelWriter_450` |

Save and restart the add-on.

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
- Confirm the HA host can reach the CUPS machine: from another device on the same LAN, open `http://<cups-host>:631`
- Check your router/firewall isn't blocking port 631 between the HA host and the CUPS machine

**Label prints but looks wrong (wrong size, cut off)**
- Make sure the correct label stock is loaded in the printer
- Check the CUPS printer settings for paper size — set it to match your label roll
- Try a different label preset in the PantrLytics Designer page

**Jobs appear in CUPS queue but don't print**
- Check for paper jams or low ink/ribbon on the printer
- Delete stuck jobs from the CUPS web UI and try again

**Queue name not matching**
- Go to `http://<cups-host>:631/printers` — the queue name is in the printer URL after `/printers/`
- Copy it exactly, including capitalisation and underscores

---

## Using a Mac as a print server

Macs have CUPS built in. Enable sharing:

1. **System Settings → Printers & Scanners** — add your printer.
2. Open Terminal and run:
   ```bash
   sudo cupsctl --remote-any --share-printers
   ```
3. Use your Mac's LAN IP and port 631 as `ipp_host`.
4. Find the queue name at `http://localhost:631/printers`.

---

## No printer? Use PNG preview

If you don't have a printer, leave `ipp_host` and `ipp_printer` blank. Print buttons will not appear. Use **Preview Label** on any item to generate a PNG you can print manually or save.
