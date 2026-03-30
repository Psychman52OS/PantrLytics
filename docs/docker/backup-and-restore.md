# Backup and Restore

The Backup page lets you create full backups of your inventory data, restore from a previous backup, import/export CSV files, and perform maintenance actions.

Access it via **More → Backup** on the mobile nav or the sidebar.

> The Backup page requires admin authentication.

---

## Creating a backup

Click **Create backup**. The app generates a `.zip` file containing:
- The SQLite database (using `VACUUM INTO` for a WAL-safe snapshot)
- All uploaded photos
- The options/config file
- A CSV export of your active items

A download prompt will appear. Save the file somewhere safe — outside the Docker volume.

---

## Restoring from a backup

1. Click **Choose file** under the Restore section and select a `.zip` backup created by PantrLytics.
2. Click **Restore**.
3. The app will replace the current database and photos, then restart automatically.
4. A "waiting" page will poll until the app is back up, then redirect you to the home page.

> **Warning:** Restoring overwrites all current data. There is no undo. Back up your current data first if you want to keep it.

---

## CSV export

Export your inventory to a CSV file for use in spreadsheets or external tools.

1. Select the fields you want to include using the checkboxes.
2. Click **Export CSV**. The file downloads immediately.

---

## CSV import

Import items from a CSV file. This is useful for bulk-loading inventory or migrating from another system.

**Format requirements:**
- The CSV headers must match the export format (use an exported CSV as a template).
- Items without a serial number will have one auto-generated.
- Categories, locations, bins, and units that don't already exist will be created automatically (upserted).
- Rows that are missing required data or have errors will be skipped.

After import, a summary shows how many items were added and how many were skipped.

---

## Delete all items

A **Delete all items** button is available at the bottom of the Backup page. This permanently removes all active items, depleted items, and uploaded photos from the database.

> **This is irreversible.** A confirmation prompt is shown before the action runs. Back up your data first.

---

## Repair database

If the database becomes corrupted (e.g. after an unclean shutdown or container crash), a **Repair DB** option is available. This runs SQLite's integrity check and attempts to recover the database. If repair fails, restore from a backup.

---

## Manual backup via Docker volume

As an alternative to the in-app backup, you can copy the data directory directly from the Docker volume:

```bash
# Copy the entire data volume to a local backup folder
docker run --rm \
  -v pantrlytics_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/pantrlytics-$(date +%Y%m%d).tar.gz -C /data .
```

To restore from a tar backup:
```bash
docker run --rm \
  -v pantrlytics_data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/pantrlytics-YYYYMMDD.tar.gz"
```

Stop the container before restoring to avoid database corruption:
```bash
docker compose down
# ... restore command ...
docker compose up -d
```

---

## Best practices

- **Back up before updates.** Run a backup before `docker compose pull` so you have a restore point.
- **Store backups off the host.** Copy the zip to a NAS, cloud storage, or another machine.
- **Test restores occasionally.** A backup you've never restored is an untested backup.
