# Lovelace Dashboard Cards

PantrLytics has a companion card bundle for Home Assistant dashboards. The cards connect to the app over HA's ingress proxy so they work without any extra network configuration.

Cards repo: [lovelace-pantrlytics-cards](https://github.com/Psychman52OS/lovelace-pantrlytics-cards)

---

## Available cards

| Card | Purpose |
|---|---|
| **Stats** | At-a-glance summary — active items, expiring count, used today |
| **Expiring Items** | List of items nearing use-by date with color-coded days remaining |
| **Reports** | Inventory health score (A–F), compliance breakdown, action items |
| **Quick Add** | Add new items from the dashboard with configurable field visibility |
| **Quick Adjust** | Up to 10 pinned items with +/− quantity buttons and swipe actions |
| **App Status** | IPP printer status, app storage breakdown, item counts, version |

---

## Installation

### 1. Install via HACS

1. Open **HACS** in Home Assistant.
2. Go to **Frontend** → click **⋮** → **Custom repositories**.
3. Add `https://github.com/Psychman52OS/lovelace-pantrlytics-cards` as type **Dashboard**.
4. Search for **PantrLytics Cards** and click **Download**.

### 2. Add the resource

1. Go to **Settings → Dashboards → ⋮ → Manage resources**.
2. Click **Add resource**:
   - URL: `/hacsfiles/lovelace-pantrlytics-cards/pantrlytics-cards.js`
   - Type: **JavaScript module**
3. Hard-refresh your browser (`Cmd+Shift+R` / `Ctrl+Shift+R`).

### Manual install (no HACS)

Download `pantrlytics-cards.js` from the [releases page](https://github.com/Psychman52OS/lovelace-pantrlytics-cards/releases), copy it to `/config/www/`, and add `/local/pantrlytics-cards.js` as a JavaScript module resource.

---

## Adding a card to your dashboard

1. Open a dashboard → click **Edit** (pencil icon).
2. Click **+ Add card**.
3. Search for **PantrLytics** and select a card.
4. Enter your PantrLytics URL (e.g. `http://192.168.1.10:8099`) and configure options.

---

## Stats card

Shows total active items, items expiring within 7 days, and items depleted today.

```yaml
type: custom:pantrlytics-stats-card
url: http://192.168.1.10:8099
title: PantrLytics          # optional
refresh_interval: 300       # optional, default 300s
```

---

## Expiring Items card

Lists items nearing their use-by date. Each row links to the item detail page.

```yaml
type: custom:pantrlytics-expiring-card
url: http://192.168.1.10:8099
days: 7                     # optional, default 7
max_items: 10               # optional, default 10
refresh_interval: 300       # optional, default 300s
```

---

## Reports card

Shows the inventory health score and action items from the Reports page.

```yaml
type: custom:pantrlytics-reports-card
url: http://192.168.1.10:8099
refresh_interval: 600       # optional, default 600s
```

---

## Quick Add card

An item entry form on your dashboard. Each field can be individually shown or hidden.

```yaml
type: custom:pantrlytics-quick-add-card
url: http://192.168.1.10:8099
show_category: true
show_location: true
show_use_by_date: true
show_use_within: true
show_notes: true
# see cards repo docs for full field list
```

---

## Quick Adjust card

Up to 10 pinned items with quantity +/− buttons and swipe gestures. Swipe actions mirror the settings in **Admin → Swipe actions**.

```yaml
type: custom:pantrlytics-quick-adjust-card
url: http://192.168.1.10:8099
item_id_1: 12
item_id_2: 7
item_id_3: 23
```

To find an item's ID, open it in the app — the number in the URL (`/item/12`) is the ID.

**Deplete via swipe:** if the swipe action is set to Deplete, a dialog appears asking for a reason and date before confirming.

---

## App Status card

Shows IPP printer connectivity, app storage breakdown (expandable), and active/total item counts.

```yaml
type: custom:pantrlytics-status-card
url: http://192.168.1.10:8099
title: PantrLytics          # optional — app name shown in header
refresh_interval: 60        # optional, default 60s
show_ipp: true              # optional, default true
show_storage: true          # optional, default true
show_items: true            # optional, default true
```

---

## Troubleshooting

**Cards don't appear in the card picker after installing**
- Make sure the resource was added under Manage resources and the URL is correct.
- Hard-refresh the browser (`Cmd+Shift+R`).

**Cards show "Error" or fail to load data**
- Check that the `url` field points to your PantrLytics instance and the add-on is running.
- Open the browser console (F12) — a 404 on the JS file means the resource path is wrong.

**Quick Adjust shows wrong swipe actions**
- Swipe actions come from **Admin → Swipe actions** in the app. Change them there and the card will reflect the update on next refresh.

For more detail on each card, see the [cards repo documentation](https://github.com/Psychman52OS/lovelace-pantrlytics-cards/tree/main/docs).
