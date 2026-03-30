# Managing Inventory

This guide covers how to add, edit, search, and deplete items in PantrLytics.

---

## Adding an item

1. Tap **New item** (or the **+** tab on mobile).
2. Fill in the fields. The only required field by default is **Name** — all others are optional unless you've enabled required fields in Admin.

| Field | Description |
|---|---|
| Name | Item name (e.g. "Chicken Stock") |
| Category | Grouping for filters and reports (e.g. "Canned Goods") |
| Location | Where it's stored (e.g. "Pantry", "Freezer") |
| Bin | Sub-location within a location (e.g. "Shelf 2") |
| Quantity | How many you have |
| Unit | Unit of measure (e.g. "cans", "oz", "bottles") |
| Condition | Free text for condition notes |
| Cook date | Date the item was cooked or prepared |
| Use-by date | Expiry or best-by date (used in reports) |
| Use within | How soon after opening to use (e.g. "3 days") |
| Tags | Comma-separated labels for free-form grouping |
| Notes | Free text notes |
| Photos | Upload one or more photos |

3. Click **Save**. The item appears on the home page.

---

## Browsing and searching

### Search bar
Type in the search bar to filter by name, serial, barcode, tags, notes, category, location, bin, unit, or dates. Results update as you type (no need to press Enter).

### Quick-filter chips (mobile)
Horizontal scrollable chips for categories and locations appear below the search bar. Tap one to filter instantly.

### Filter panel (desktop)
Click **Filters** to expand a panel with dropdowns for category, location, bin, use-within, and depleted reason. Filters apply automatically when you change a dropdown — no Apply button needed.

### List vs Grid view
Toggle between **List** (compact table) and **Grid** (cards with photo thumbnails) using the view toggle near the top right. Your preference is saved automatically.

---

## Adjusting quantity

For units marked **Adjustable** in Admin → Units, **+** and **−** buttons appear on the item row. Tap them to increment or decrement the quantity directly from the list — no need to open the item.

---

## Editing an item

Open the item (tap the name or row) → click **Edit**. All fields are editable, including photos. Click **Save** when done.

---

## Swipe gestures

On the inventory list, you can swipe left or right on a row to trigger a quick action. The default actions and what they do can be configured in **Admin → Swipe actions**.

Available swipe actions:
- **Edit** — opens the edit form
- **Mark depleted** — opens the deplete dialog
- **Open details** — opens the item detail page
- **Print label** — sends a label to the printer
- **No action** — disables that swipe direction

Swipe works on both mobile (touch) and desktop (click-drag).

---

## Depleting an item

Depleting marks an item as used up and moves it to the Depleted list.

**From the list:** tap the deplete button on the row or swipe with the deplete action configured. A dialog will ask for the depletion date/time.

**From the item detail page:** click **Mark depleted**, choose a reason (optional), and confirm.

Depletion reasons (for reporting): Expired, Used, Donated, Discarded, or a custom note.

---

## Recovering a depleted item

Items in the Depleted list can be recovered (restored to active inventory).

1. Go to the **Depleted** tab or navigate to the Depleted Items page.
2. Find the item and click **Recover**. The item returns to active status with its previous data.

---

## Deleting an item

Open the item detail page → click **Delete**. This permanently removes the item and all its photos. This action cannot be undone.

---

## Photos

- Upload one or more photos on the new item or edit form.
- On the item detail page, tap the **★ star** button on a photo to set it as the **primary thumbnail** — this is the image shown in grid card view.
- Thumbnails update immediately after changing the primary photo (cache-busting is applied automatically).

---

## Serial numbers and barcodes

If a serial number is not entered manually, one is auto-generated using the `SERIAL_PREFIX` set in your `.env` file (default: `ITEM-`). Serials and barcodes are searchable from the main search bar.
