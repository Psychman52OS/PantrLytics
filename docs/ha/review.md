# Review

The Review page surfaces items that haven't been touched recently so you can verify they're still accurate — check quantities, confirm nothing has gone bad, and update use-by dates if needed.

Access it via **Review** in the desktop nav bar or **More → Review Items** on the mobile bottom sheet.

---

## How review works

PantrLytics tracks a **last reviewed date** on every item. An item counts as reviewed if any of the following happened within the review window:

- The item was created
- The item was edited
- The item was depleted
- You tapped **✓ Reviewed** on the Review page

Items not touched within the review window appear in the **Needs review** list. Once reviewed, they move to the **Recently reviewed** list.

---

## The Needs Review list

Each row shows:
- Item name (linked to the item detail page)
- Expiry badge if the item is expired or expiring soon
- Category, location, bin, and quantity
- Use-by date and last reviewed date (or "Never" if never touched)

### Marking an item as reviewed

Tap **✓ Reviewed** on any row. The item's last reviewed date is stamped to today and it moves to the Recently Reviewed section immediately.

---

## Mark all reviewed

A **Mark all reviewed** button appears at the top when there are items in the Needs Review list. Tapping it stamps today's date on every item in the list at once and redirects back to the Review page with a count.

---

## Recently Reviewed list

Items reviewed within the current review window are shown here. Each row shows the item name, category, location, quantity, and the date it was last reviewed.

---

## Review window

The review window defaults to **30 days**. You can change it in **Admin → Review window**:

1. Go to **Admin**.
2. Find the **Review window** section.
3. Enter a number of days (7–365).
4. Click **Save**.

A shorter window means items cycle through review more frequently. A longer window reduces how often items appear.

> The review window also drives the **Audit freshness** component (20%) of the Inventory Health Score on the Reports page.

---

## Per-item review window

You can override the global review window on a per-item basis.

**On the New or Edit form:** use the quick-select buttons (15d, 30d, 60d, 120d) next to the **Review window** field, or type a number of days manually. Leave the field blank to use the global default.

**On the item detail page:** the item's review status is shown in a dedicated panel:
- **Last reviewed** — date the item was last reviewed (or "Never")
- **Next review due** — date the next review is due, with a countdown pill (e.g. "in 12 days" or "overdue")

Items with a per-item window appear in the Review queue based on *their own* window rather than the global one.

---

## Audit freshness and the Health Score

The health score's "Reviewed" component reflects what percentage of your active items have been reviewed within the current window. Items auto-stamped by editing or depleting count toward this — only items that haven't been touched at all in the window will drag it down.

---

## Tips

- Do a quick review pass every month (or whenever the health score's "reviewed" percentage drops).
- Items with "Never" as the last reviewed date were added before the review system was introduced — work through those first.
- The Review page sorts the Needs Review list oldest-first, so the most overdue items are always at the top.
