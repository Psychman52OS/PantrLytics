# Reports and Analytics

The Reports page gives you a full picture of your inventory health — what's expiring, what's been wasted, how quickly items are consumed, and where your biggest risks are.

---

## Opening Reports

Click **Reports** in the sidebar or bottom nav bar.

---

## Filters

At the top of the page, three dropdowns let you focus the report:

| Filter | Options |
|---|---|
| **Horizon** | 7 days / 14 days / 30 days / 60 days / All |
| **Category** | Any category defined in your inventory |
| **Location** | Any location defined in your inventory |

Filters apply automatically when you change a dropdown — no Apply button needed.

> **Note:** The Inventory Health Score always reflects your *entire* inventory, regardless of filters. Charts and tables update with the filtered view.

---

## Inventory Health Score

A score from **0–100** (with a letter grade A–F) summarising overall inventory health. It combines three components:

| Component | Weight | What it measures |
|---|---|---|
| Use-by compliance | 50% | Percentage of items not past their use-by date |
| Date coverage | 30% | Percentage of items that have a use-by date set |
| Audit freshness | 20% | Percentage of items reviewed within the review window |

**Grade scale:** A = 90–100, B = 80–89, C = 70–79, D = 60–69, F = below 60.

---

## Action items banner

Below the health score, a banner surfaces the most urgent issues:

- Items **expired** and still in active stock
- Items expiring **within 7 days**
- Items with **no use-by date** set
- **High waste rate** alert (if more than 20% of depletions happened after use-by date)

Each action item includes a count so you know the scale of the issue at a glance. Tap an alert to open a drill-down list of the affected items.

---

## Charts

Three interactive charts are shown:

### Use-by compliance (donut)
Shows the split between compliant items (not expired), expired items, and items with no date — as a percentage of total active inventory.

### Aging distribution (horizontal bar)
Breaks down active items into age buckets: under 7 days, 7–14 days, 14–30 days, 30–60 days, and over 60 days since they were added.

### Depletion trend (line chart)
Shows how many items were consumed per week over the **last 12 weeks**. Useful for spotting seasonal patterns or unusual spikes in consumption.

---

## Category and location compliance tables

Two sortable tables show compliance broken down by category and by location:

| Column | Description |
|---|---|
| Category / Location | Group name |
| Total | Active items in this group |
| Expired | Items past use-by date |
| No date | Items with no use-by date |
| % Compliant | Inline bar chart showing the compliance percentage |

Tables are sorted worst-first (most issues at the top).

---

## Top consumed categories

A horizontal bar chart showing the **10 most-depleted categories** by total depletion count (all time). Useful for identifying which areas of your inventory you turn over fastest.

---

## Waste rate

The waste rate card shows the percentage of depletion events where the item was past its use-by date at the time it was depleted. A high waste rate means items are frequently expiring before being used.

---

## KPI cards

A row of summary cards shows counts for:
- Expired items (past use-by date, still in stock)
- Expiring within 7 / 14 / 30 / 60 days
- Total items in the current filtered view

---

## Upcoming risk — Top 25

A table of the 25 active items with the soonest use-by dates. Sorted by days remaining (ascending). Each row shows the item name, category, location, and days left.

---

## Bulk actions

### Mark all expired depleted
A button at the top of the page marks every active item that is past its use-by date as depleted with the reason "Expired". A confirmation count is shown after the action completes.

### Export report as CSV
Downloads a CSV of all active items in the current filtered view (filtered by horizon, category, and location). Useful for exporting data for external analysis.

---

## Recent depletions

A list of recently depleted items showing the item name, depletion date, days on hand, and the reason given.
