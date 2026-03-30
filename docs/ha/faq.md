# Frequently Asked Questions — Home Assistant

---

## Installation and setup

**Q: The add-on is installed but I can't find it in the store.**
After adding the repository URL, refresh the add-on store page. If PantrLytics still doesn't appear, remove and re-add the repository URL.

**Q: The add-on won't start.**
Check the **Log** tab on the add-on page for error messages. Common causes:
- Port conflict: another service is already using port 8099. Change the mapped host port in Network settings.
- Database error on first boot: restart the add-on — the database initialises on the first run and sometimes needs a second start.

**Q: What is the default admin password?**
`password` — change it immediately via **Admin → Admin password**.

---

## QR codes and labels

**Q: I scan a label QR code and get a 401 error or a blank page.**
The QR code contains the `base_url` from your config. The URL is either wrong or the device can't reach it. Fix:
1. Set `base_url` to `http://<your-ha-host-lan-ip>:<mapped-port>` (e.g. `http://192.168.1.10:8099`).
2. Restart the add-on.
3. Reprint the affected labels — old labels still carry the old URL.

**Q: I scan the QR code and it opens but asks me to log in.**
QR links go to the item detail page. Admin auth is separate from item viewing. If you're being asked for admin credentials, check that your session hasn't expired. The admin session is cookie-based and expires after inactivity.

**Q: Should I use the HA ingress URL for `base_url`?**
No. HA ingress URLs (`/api/hassio_ingress/...`) require short-lived tokens embedded in the URL. These expire and will cause scan failures. Always use a direct LAN IP + port URL.

---

## Printing

**Q: The Print Label button does nothing / I get a PNG instead.**
`ipp_host` and/or `ipp_printer` are not set or are incorrect. Go to the add-on Configuration tab and check both values. See [Printer Setup](printer-setup.md).

**Q: Labels print but are the wrong size.**
The label size is controlled by the active preset in the Label Designer. Open **Designer** and check which preset is set as default. Also verify the paper size in CUPS matches your label stock.

**Q: I have a twin-roll printer and it's printing on the wrong roll.**
In the Label Designer, find the active preset and change the **Printer side** setting to Left or Right.

---

## Inventory

**Q: Quantity +/− buttons don't appear for some items.**
The +/− buttons only appear for units marked **Adjustable** in Admin → Units. Find the unit in the list and enable the Adjustable toggle.

**Q: I renamed a category/location but old items still show the old name.**
Renaming from Admin updates all existing items automatically. If you see the old name, try a hard refresh (Ctrl+Shift+R / Cmd+Shift+R) to clear the browser cache.

**Q: I deleted a photo but the thumbnail still shows.**
Hard refresh the page (Ctrl+Shift+R / Cmd+Shift+R). Thumbnails use cache-busting, but the browser may have cached an older version.

---

## Reports

**Q: The health score seems low even though most items are fine.**
The health score penalises items that have no use-by date set (date coverage component = 30% of the score). Adding use-by dates to your items will improve it. The audit freshness component (20%) also drops if items haven't been reviewed recently — visit the Review page to clear the queue.

**Q: The depletion trend chart is empty.**
The trend shows the last 12 weeks of depletions. If you haven't depleted any items yet, the chart will be empty. Deplete some items and revisit.

---

## Review

**Q: Every item shows as "Needs review" after the update.**
Items added before the review system was introduced have no last reviewed date. They all show as needing review on first use. Work through the list using **Mark all reviewed** to clear it, then the queue will only surface items that genuinely haven't been touched.

**Q: Items I just edited still show up in the Needs Review list.**
Editing an item automatically stamps the last reviewed date to today, so they should immediately move to Recently Reviewed. If they don't, try a hard refresh (Ctrl+Shift+R / Cmd+Shift+R).

---

## Backup and restore

**Q: The restore completed but nothing seems to have changed.**
After a successful restore you are redirected to the Backup page with a confirmation message. The restored data is immediately active — no restart required. If items still look wrong, do a hard refresh (Ctrl+Shift+R / Cmd+Shift+R).

**Q: Can I use HA's built-in backup to back up PantrLytics data?**
HA's snapshot/backup does include add-on data volumes, so yes — HA backups will capture PantrLytics data. However, using PantrLytics' own backup feature gives you a portable zip you can restore independently, without needing to restore an entire HA snapshot.

---

## Performance

**Q: The app is slow.**
Try increasing the `workers` value in the add-on config (default: 2). On lower-powered hardware like a Raspberry Pi 3, keep it at 2. On more capable hardware, 3–4 workers can help.

**Q: I have hundreds of items and the list loads slowly.**
Use the search and filter options to narrow the view. The AJAX search avoids full page reloads, so searching is faster than loading the unfiltered list.
