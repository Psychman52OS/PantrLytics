# Labels and Printing

PantrLytics can generate and print inventory labels with item details and a scannable QR code. Printing requires a CUPS/IPP printer on your local network. Without a printer configured, you can still preview and download labels as PNG images.

---

## How labels work

Each item label contains:
- Item name and serial number
- Key dates (use-by, cook date if set)
- Category, location, and bin
- A QR code that links to the item's detail page

The QR code URL is built from the `base_url` you set in the add-on config. If `base_url` is wrong or missing, QR scans will fail. See [Getting Started](getting-started.md) for how to set it correctly.

---

## Printing a label from an item

1. Open the item detail page.
2. Choose how many copies you want in the **copy count** field.
3. Click **Print Label**. The label is sent directly to your IPP printer as a single CUPS job.

If no printer is configured, the button will not send to a printer — use **Preview Label** instead.

---

## Previewing a label

Click **Preview Label** on the item detail page to open the label as a PNG in a new browser tab. You can save or print it from there using your browser's print function.

---

## Label Designer

The **Designer** page (accessible from the sidebar or bottom nav) has two sections:

### Quick Label
For one-off labels that are not linked to any inventory item — useful for boxes, bins, or anything you want to label on the fly.

- Enter a **Title** (large text) and optional **Description** (smaller text).
- Click **Preview** to see the PNG, or **Print quick label** to send it directly to your printer.

### Presets
Presets control how item labels look when you print from an item page. Each preset defines the label size, font, and layout. You can set a **default preset** from the preset cards.

- **Printer side**: For twin-roll printers, choose Auto, Left, or Right to select which roll is used.
- The active default preset is highlighted on the preset card.

---

## Printer requirements

- A CUPS/IPP print server must be reachable on your local network.
- The add-on config needs `ipp_host` (e.g. `192.168.1.50:631`) and `ipp_printer` (the CUPS queue name).
- If the printer is unreachable or not configured, print actions fall back to PNG preview.

See [Printer Setup](printer-setup.md) for full setup instructions.

---

## Multiple copies

When printing from an item, set the copy count before clicking Print. All copies are submitted as a single CUPS job (one job with repeated pages), keeping your print queue tidy.

---

## QR code troubleshooting

If scanning a label opens the wrong page, times out, or shows a 401 error:

1. Check `base_url` in Admin → Configuration. It must be a URL reachable by the scanning device.
2. Use your HA host's LAN IP and the mapped port — not the HA ingress URL.
3. After fixing `base_url`, **reprint labels** for existing items. Old labels still carry the old URL.
