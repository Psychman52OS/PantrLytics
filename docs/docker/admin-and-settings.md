# Admin and Settings

The Admin page is the control centre for PantrLytics. It covers display preferences, required fields, categories, units, swipe actions, and more.

Access Admin via the sidebar or **More → Admin** on the mobile bottom nav bar. You will be prompted for your admin password if the session has expired.

---

## Locking and unlocking Admin

At the top of the Admin page is a **Lock admin** button. Tap it to lock the admin area until the password is entered again. This prevents accidental changes when handing a device to someone else.

---

## Health

A quick-status panel at the top shows:
- **IPP connectivity** — whether the app can reach the configured printer
- **Disk usage** — MB used vs. total in the data directory
- **Total items** — count of active items in the database
- **Debug / Who am I** — a diagnostic link showing request headers and config values (useful when debugging proxy or URL issues)

---

## Main table columns

Choose which fields are shown on the home page inventory list and set their order.

- **Toggle** the switch next to a field to show or hide it. Name is always shown.
- **Drag** the ☰ handle to reorder columns.
- Changes save automatically.

---

## Required fields

Choose which fields are mandatory when creating or editing an item. Any toggled-on field will show a validation error if left blank.

Useful for enforcing data consistency — for example, requiring Category and Use-by date on every item.

---

## Theme

Toggle between **Light** and **Dark** mode. The preference is saved per browser.

---

## App heading

Customise the text shown at the top of the home page. Useful if you're running multiple instances or just want to personalise it.

---

## Font size

Set a **global base font size** for the entire app, plus optional per-page overrides for the inventory list and item detail pages. Font sizes are applied as CSS variables, so all text scales proportionally.

---

## Default item icon

Choose the icon shown on items that don't have a photo. Options:
- A grid of 40 food and pantry emojis — tap one to set it as default.
- **Upload a custom image** (PNG or JPG) to use as the default icon instead.

---

## Swipe actions

Configure what happens when you swipe left or right on an inventory row or card.

Each direction (left, right) can be set independently to one of:
- **Edit** — open the edit form
- **Mark depleted** — open the deplete dialog
- **Open details** — navigate to the item detail page
- **Print label** — send a label to the printer
- **No action** — disable that swipe direction

---

## Categories

Add, edit, delete, and reorder the categories available when creating or editing items.

- Click **+ Add** to create a new category.
- Click a category name to edit it in a modal. Renaming a category updates all existing items that use it.
- Drag the ☰ handle to reorder.
- Click the trash icon to delete. Items using the deleted category will have the field cleared.

---

## Locations

Same controls as Categories — add, edit (renaming updates all items), reorder, and delete.

---

## Bins

Sub-locations within a location (e.g. "Shelf 1", "Door"). Same controls as Categories.

---

## Use Within

Manage the "Use Within" values available on items (e.g. "3 days", "1 week", "1 month"). Same controls as above.

---

## Origin Date Labels

Manage the dropdown options shown when setting the **Origin Date** label on an item (e.g. "Cooked On", "Purchased On", "Opened On").

- **Add** a new label with the **+ Add** button.
- **Edit** a label in-place by clicking it.
- **Delete** a label with the trash icon. Items that use the deleted label keep their existing label text but the option is removed from the dropdown.
- **Drag** the ☰ handle to reorder entries — the first entry in the list is the default shown on new items.

Default labels included: Cooked On, Purchased On, Opened On, Made On, Frozen On, Received On, Prepared On, Picked On, Brewed On. You can rename, remove, or add your own.

The selected label is printed on item labels when printing via the Label Designer.

---

## Units

Manage the units of measure available on items (e.g. "cans", "oz", "bottles", "grams").

- **Add / edit / delete / reorder** units the same way as categories.
- **Adjustable toggle**: when enabled for a unit, quantity **+** and **−** buttons appear on the inventory list for items using that unit. Turn it off to hide the buttons for that unit.
- Any unit already used on an existing item is automatically added to this list (non-adjustable by default) so you can manage it.

---

## Review window

Set how many days before an item needs to be re-reviewed. Items not touched within this window appear in the **Review** queue.

- Enter a number between **7 and 365** (default: 30).
- Click **Save**.

This setting also controls the **Audit freshness** component of the Inventory Health Score on the Reports page. See [Review](review.md) for full details.

---

## Admin password

Change the admin area password. Enter the new password twice to confirm.

**Default password:** `password` — change it immediately after install.
