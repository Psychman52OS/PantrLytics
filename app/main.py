import os, io, subprocess, tempfile, hashlib
import zipfile
import threading
import time
import datetime as dt
import uuid
import shutil
import socket
from typing import Optional, List

from fastapi import FastAPI, Request, Form, UploadFile, File, Response
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
    JSONResponse,
    FileResponse,
)
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Session, SQLModel, create_engine, select, func
from PIL import Image, ImageDraw, ImageFont
import qrcode, qrcode.image.pil, json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

from datetime import datetime
from zoneinfo import ZoneInfo
import tzlocal
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF_OK = True
except Exception as e:
    print("[PHOTO] HEIF/HEIC support not available:", e)
    HEIF_OK = False

# -------------------------------------------------
# Timezone / datetime formatting helper
# -------------------------------------------------
LOCAL_TZ = tzlocal.get_localzone()
APP_VERSION = "2026.01.09"
APP_INTERNAL_PORT = 8099


def format_datetime(value: str):
    """Format an ISO timestamp string into local time (24-hour)."""
    try:
        d = datetime.fromisoformat(value)
    except Exception:
        # If it's not a valid ISO string, just return as-is
        return value

    # If no timezone info, assume UTC
    if d.tzinfo is None:
        d = d.replace(tzinfo=ZoneInfo("UTC"))

    # Convert to the local (HA host) timezone
    d_local = d.astimezone(ZoneInfo(str(LOCAL_TZ)))
    return d_local.strftime("%Y-%m-%d %H:%M")


# -----------------------------
# Options / config
# -----------------------------
DATA_DIR = os.environ.get("DATA_DIR", "/data")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5MB safety limit
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
ADDON_OPTIONS_PATH = os.environ.get(
    "ADDON_OPTIONS_PATH", os.path.join(DATA_DIR, "options.json")
)


def load_options():
    """Load Home Assistant add-on options, if they exist."""
    try:
        with open(ADDON_OPTIONS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        # Falls back to env-only config when running locally
        return {}


def merged_config():
    """
    Prefer environment variables (for local/dev) and fall back to add-on options.
    """
    opts = load_options()

    def _get(key: str, default: str = ""):
        # Env wins; options.json (add-on config) is the fallback
        return os.environ.get(key.upper(), opts.get(key, default))

    return {
        "base_url": _get("base_url", ""),
        "ipp_host": _get("ipp_host", ""),
        "ipp_printer": _get("ipp_printer", ""),
        # A placeholder default prefix; users should override in add-on config.
        "serial_prefix": _get("serial_prefix", "USERconfigurable-"),
    }


config = merged_config()
BASE_URL = config["base_url"].rstrip("/")  # used for QR/links
IPP_HOST = config["ipp_host"]
IPP_PRINTER = config["ipp_printer"]
SERIAL_PREFIX = config["serial_prefix"]
DEFAULT_UNIT_ENTRIES = [
    {"name": "each", "adjustable": True},
    {"name": "unit", "adjustable": True},
    {"name": "units", "adjustable": True},
    {"name": "bag", "adjustable": True},
    {"name": "bags", "adjustable": True},
    {"name": "serving", "adjustable": True},
    {"name": "servings", "adjustable": True},
    {"name": "can", "adjustable": True},
    {"name": "cans", "adjustable": True},
    {"name": "ounce", "adjustable": False},
    {"name": "ounces", "adjustable": False},
    {"name": "oz", "adjustable": False},
    {"name": "pound", "adjustable": False},
    {"name": "pounds", "adjustable": False},
    {"name": "lb", "adjustable": False},
    {"name": "lbs", "adjustable": False},
    {"name": "gram", "adjustable": False},
    {"name": "grams", "adjustable": False},
    {"name": "kilogram", "adjustable": False},
    {"name": "kilograms", "adjustable": False},
    {"name": "liter", "adjustable": False},
    {"name": "liters", "adjustable": False},
    {"name": "milliliter", "adjustable": False},
    {"name": "milliliters", "adjustable": False},
    {"name": "gallon", "adjustable": False},
    {"name": "gallons", "adjustable": False},
    {"name": "quart", "adjustable": False},
    {"name": "quarts", "adjustable": False},
    {"name": "pint", "adjustable": False},
    {"name": "pints", "adjustable": False},
    {"name": "cup", "adjustable": False},
    {"name": "cups", "adjustable": False},
    {"name": "bottle", "adjustable": False},
    {"name": "bottles", "adjustable": False},
    {"name": "jug", "adjustable": False},
    {"name": "jugs", "adjustable": False},
    {"name": "jar", "adjustable": False},
    {"name": "jars", "adjustable": False},
    {"name": "box", "adjustable": False},
    {"name": "boxes", "adjustable": False},
    {"name": "pack", "adjustable": False},
    {"name": "packs", "adjustable": False},
    {"name": "package", "adjustable": False},
    {"name": "packages", "adjustable": False},
]
MAX_LABEL_COPIES = 25  # Safety limit for print jobs triggered via UI
DEPLETION_REASONS = [
    "Consumed/Used",
    "Discarded (expired/spoiled)",
    "Discarded (damaged)",
    "Donated/Returned",
    "Lost/Missing",
    "Restocked/Replaced (new batch)",
    "Other",
]

# -----------------------------
# DB
# -----------------------------
DB_PATH = os.path.join(DATA_DIR, "inventory.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def _inventory_update_token() -> str:
    """Return a string token that changes whenever the inventory DB is written."""
    try:
        return str(os.path.getmtime(DB_PATH))
    except OSError:
        # Fall back to current time so clients still get a monotonic token.
        return str(time.time())

def _parse_date(date_str: Optional[str]) -> Optional[dt.date]:
    """Parse a date or datetime-ish value into a date, or None on failure."""
    if not date_str:
        return None
    if isinstance(date_str, dt.datetime):
        return date_str.date()
    if isinstance(date_str, dt.date):
        return date_str
    text = str(date_str)
    try:
        return dt.date.fromisoformat(text.split("T")[0])
    except Exception:
        try:
            return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except Exception:
            return None

def _days_until(date_str: Optional[str]) -> Optional[int]:
    d = _parse_date(date_str)
    if not d:
        return None
    return (d - dt.date.today()).days

def _expiry_info(item: "Item") -> Optional[dict]:
    days = _days_until(item.use_by_date)
    if days is None:
        return None
    if days < 0:
        return {"days": days, "severity": "overdue", "label": "Overdue", "badge": "Expired"}
    if days <= 7:
        return {"days": days, "severity": "critical", "label": f"{days}d", "badge": "Expires ≤7d"}
    if days <= 14:
        return {"days": days, "severity": "soon", "label": f"{days}d", "badge": "Expires ≤14d"}
    if days <= 30:
        return {"days": days, "severity": "watch", "label": f"{days}d", "badge": "Expires ≤30d"}
    return {"days": days, "severity": "ok", "label": f"{days}d", "badge": "Fresh"}


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    serial_number: str = Field(index=True, unique=True)

    name: str
    category: Optional[str] = None
    tags: Optional[str] = None
    location: Optional[str] = None
    bin_number: Optional[str] = None

    quantity: int = 1
    unit: Optional[str] = "each"
    barcode: Optional[str] = None
    second_serial_number: Optional[str] = None
    condition: Optional[str] = None
    cook_date: Optional[str] = None
    use_by_date: Optional[str] = None
    use_within: Optional[str] = None  # "Use Within" field
    notes: Optional[str] = None
    photo_path: Optional[str] = None
    last_audit_date: Optional[str] = None

    depleted_at: Optional[str] = None  # ISO timestamp when item was marked depleted
    depleted_reason: Optional[str] = None
    depleted_qty: Optional[int] = None

    created_at: str = Field(
        default_factory=lambda: dt.datetime.utcnow().isoformat()
    )


class ItemPhoto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id", index=True)
    path: str
    created_at: str = Field(
        default_factory=lambda: dt.datetime.utcnow().isoformat()
    )


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: str = Field(
        default_factory=lambda: dt.datetime.utcnow().isoformat()
    )


class Bin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: str = Field(
        default_factory=lambda: dt.datetime.utcnow().isoformat()
    )


class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: str = Field(
        default_factory=lambda: dt.datetime.utcnow().isoformat()
    )


class UseWithin(SQLModel, table=True):
    """Admin-managed list of 'Use Within' options."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: str = Field(
        default_factory=lambda: dt.datetime.utcnow().isoformat()
    )


class UnitOption(SQLModel, table=True):
    """Admin-managed unit names with adjustable toggle."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    adjustable: bool = Field(default=True)
    created_at: str = Field(
        default_factory=lambda: dt.datetime.utcnow().isoformat()
    )


class LabelPreset(SQLModel, table=True):
    """
    Global label presets used when printing item labels.

    Only one preset should have is_default = True at a time.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    # CUPS media string, e.g. "w79h252" (small address) or "w154h64" (bigger)
    media: str = Field(default="w79h252")
    # Which roll to use on twin printers: auto (by size), left, or right
    printer_side: str = Field(default="auto")

    # Field toggles
    include_name: bool = Field(default=True)
    include_location: bool = Field(default=True)
    include_bin: bool = Field(default=True)
    include_qty_unit: bool = Field(default=True)  # Qty + Unit combined
    include_condition: bool = Field(default=False)
    include_cook_date: bool = Field(default=False)
    include_use_by: bool = Field(default=True)
    include_use_within: bool = Field(default=False)
    include_qr: bool = Field(default=True)

    # “Advanced” tweaks
    align_center: bool = Field(default=False)
    font_scale: float = Field(default=1.0)

    # Is this the preset used by default when printing items?
    is_default: bool = Field(default=False)


class AppSetting(SQLModel, table=True):
    """Simple key/value storage for app-level settings (JSON strings)."""
    key: str = Field(primary_key=True)
    value: str = Field(default="")


# -----------------------------
# Display preferences (main table columns)
# -----------------------------
DISPLAYABLE_FIELDS = [
    {"key": "location", "label": "Location", "sort_type": "text"},
    {"key": "bin_number", "label": "Bin", "sort_type": "text"},
    {"key": "category", "label": "Category", "sort_type": "text"},
    {"key": "quantity", "label": "QTY", "sort_type": "number"},
    {"key": "unit", "label": "Unit", "sort_type": "text"},
    {"key": "condition", "label": "Condition", "sort_type": "text"},
    {"key": "cook_date", "label": "Cook date", "sort_type": "text"},
    {"key": "use_by_date", "label": "Use-by date", "sort_type": "text"},
    {"key": "use_within", "label": "Use within", "sort_type": "text"},
    {"key": "tags", "label": "Tags", "sort_type": "text"},
    {"key": "last_audit_date", "label": "Last audit", "sort_type": "text"},
    {"key": "barcode", "label": "Barcode", "sort_type": "text"},
    {"key": "serial_number", "label": "Serial number", "sort_type": "text"},
    {"key": "second_serial_number", "label": "Sub item tracking ID", "sort_type": "text"},
    {"key": "notes", "label": "Notes", "sort_type": "text"},
]

# Default columns shown on the main inventory table (after Name)
DEFAULT_DISPLAY_FIELDS = ["location", "bin_number", "category", "quantity", "unit"]

DISPLAY_FIELD_KEYS = {f["key"] for f in DISPLAYABLE_FIELDS}

# Fields that can be marked required when creating/editing items
REQUIRED_FIELD_OPTIONS = [
    {"key": "name", "label": "Name"},
    {"key": "category", "label": "Category"},
    {"key": "tags", "label": "Tags"},
    {"key": "location", "label": "Location"},
    {"key": "bin_number", "label": "Bin"},
    {"key": "quantity", "label": "Quantity"},
    {"key": "unit", "label": "Unit"},
    {"key": "condition", "label": "Condition"},
    {"key": "cook_date", "label": "Cook date"},
    {"key": "use_by_date", "label": "Use-by date"},
    {"key": "use_within", "label": "Use within"},
    {"key": "notes", "label": "Notes"},
]
DEFAULT_REQUIRED_FIELDS = ["name"]
REQUIRED_FIELD_LABELS = {f["key"]: f["label"] for f in REQUIRED_FIELD_OPTIONS}

BACKUP_DEFAULT_OPTIONS = {
    "include_db": True,
    "include_photos": True,
    "include_export": True,
    "include_config": True,
    "target_dir": BACKUP_DIR,
}

THEME_DEFAULT = "dark"
APP_HEADING_DEFAULT = "Pantrlytics"
ADMIN_DEFAULT_PASSWORD = "password"

# Export CSV field options
EXPORTABLE_FIELDS = [
    {"key": "serial_number", "label": "Serial number"},
    {"key": "name", "label": "Name"},
    {"key": "category", "label": "Category"},
    {"key": "tags", "label": "Tags"},
    {"key": "location", "label": "Location"},
    {"key": "bin_number", "label": "Bin"},
    {"key": "quantity", "label": "Quantity"},
    {"key": "unit", "label": "Unit"},
    {"key": "barcode", "label": "Barcode"},
    {"key": "condition", "label": "Condition"},
    {"key": "cook_date", "label": "Cook date"},
    {"key": "use_by_date", "label": "Use-by date"},
    {"key": "use_within", "label": "Use within"},
    {"key": "notes", "label": "Notes"},
    {"key": "photo_path", "label": "Photo path"},
    {"key": "last_audit_date", "label": "Last audit date"},
    {"key": "depleted_at", "label": "Depleted at"},
    {"key": "depleted_reason", "label": "Depletion reason"},
    {"key": "depleted_qty", "label": "Depleted qty"},
    {"key": "created_at", "label": "Created at"},
]
EXPORTABLE_FIELD_KEYS = [f["key"] for f in EXPORTABLE_FIELDS]


def init_db():
    # Create any missing tables based on models
    SQLModel.metadata.create_all(engine)

    def ensure_column(conn, table: str, column: str, ddl: str):
        """Add a column to 'table' if it does not already exist."""
        try:
            cols = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            col_names = {c[1] for c in cols}
            if column not in col_names:
                conn.exec_driver_sql(
                    f"ALTER TABLE {table} ADD COLUMN {column} {ddl};"
                )
                print(f"[MIGRATION] Added '{column}' column on table '{table}'.")
        except Exception as e:
            print(f"[MIGRATION] Error ensuring {table}.{column} exists:", e)

    # Lightweight migrations
    with engine.connect() as conn:
        # ensure Item.use_within exists (if DB pre-dates the field)
        ensure_column(conn, "item", "use_within", "VARCHAR")
        ensure_column(conn, "item", "depleted_at", "VARCHAR")
        ensure_column(conn, "item", "depleted_reason", "VARCHAR")
        ensure_column(conn, "item", "depleted_qty", "INTEGER")

        # ensure created_at on supporting tables
        for tbl in ("category", "bin", "location", "usewithin"):
            ensure_column(conn, tbl, "created_at", "VARCHAR")
        # label preset additions
        ensure_column(conn, "labelpreset", "printer_side", "VARCHAR DEFAULT 'auto'")

    # Seed default UseWithin options if table is empty
    ensure_usewithin_defaults()


def ensure_usewithin_defaults():
    """Ensure baseline Use Within options exist (e.g., if one was deleted accidentally)."""
    defaults = [
        "1 Day",
        "2 Days",
        "3 Days",
        "4 Days",
        "5 Days",
        "6 Days",
        "7 Days",
        "8 Days",
        "9 Days",
        "10 Days",
    ]
    with Session(engine) as session:
        existing = session.exec(select(UseWithin)).all()
        names = {u.name for u in existing}
        if not existing:
            for name in defaults:
                session.add(UseWithin(name=name))
            session.commit()
            print(f"[SEED] Inserted default UseWithin options: {', '.join(defaults)}")
        else:
            missing = [n for n in defaults if n not in names]
            if missing:
                for name in missing:
                    session.add(UseWithin(name=name))
                session.commit()
                print(f"[SEED] Restored missing UseWithin options: {', '.join(missing)}")


def _get_setting(session: Session, key: str, default=None):
    setting = session.get(AppSetting, key)
    if setting and setting.value is not None:
        return setting.value
    return default


def _set_setting(session: Session, key: str, value: str):
    setting = session.get(AppSetting, key)
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=key, value=value)
    session.add(setting)
    session.commit()


def get_display_field_keys(session: Session) -> list[str]:
    """Return ordered list of display field keys for the main table."""
    raw = _get_setting(session, "display_fields")
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [k for k in data if k in DISPLAY_FIELD_KEYS]
        except Exception:
            pass
    return list(DEFAULT_DISPLAY_FIELDS)


def save_display_field_keys(session: Session, keys: list[str]):
    valid = [k for k in keys if k in DISPLAY_FIELD_KEYS]
    if not valid:
        valid = list(DEFAULT_DISPLAY_FIELDS)
    _set_setting(session, "display_fields", json.dumps(valid))


def get_display_field_defs(session: Session) -> list[dict]:
    """Return the list of field metadata (label/type) for selected keys."""
    keys = get_display_field_keys(session)
    def _by_key(k):  # preserve configured order
        for f in DISPLAYABLE_FIELDS:
            if f["key"] == k:
                return f
        return None
    return [f for f in (_by_key(k) for k in keys) if f]


def get_use_withins_ordered(session: Session) -> list[UseWithin]:
    items = {u.id: u for u in session.exec(select(UseWithin)).all()}
    raw = _get_setting(session, "usewithin_order")
    ordered: list[UseWithin] = []
    if raw:
        try:
            ids = [int(x) for x in json.loads(raw) if x]
            for _id in ids:
                if _id in items:
                    ordered.append(items.pop(_id))
        except Exception:
            pass
    # append any remaining, sorted by name
    remaining = sorted(items.values(), key=lambda u: u.name.lower())
    ordered.extend(remaining)
    return ordered


def save_usewithin_order(session: Session, ids: list[int]):
    existing = {u.id for u in session.exec(select(UseWithin)).all()}
    filtered = [i for i in ids if i in existing]
    _set_setting(session, "usewithin_order", json.dumps(filtered))


def _ordered_generic(session: Session, model, setting_key: str, name_attr: str = "name"):
    items = {getattr(o, "id"): o for o in session.exec(select(model)).all()}
    raw = _get_setting(session, setting_key)
    ordered: list = []
    if raw:
        try:
            ids = [int(x) for x in json.loads(raw) if x]
            for _id in ids:
                if _id in items:
                    ordered.append(items.pop(_id))
        except Exception:
            pass
    remaining = sorted(items.values(), key=lambda o: getattr(o, name_attr, "").lower())
    ordered.extend(remaining)
    return ordered


def _save_order_generic(session: Session, ids: list[int], model, setting_key: str):
    existing = {getattr(o, "id") for o in session.exec(select(model)).all()}
    filtered = [i for i in ids if i in existing]
    _set_setting(session, setting_key, json.dumps(filtered))


def get_categories_ordered(session: Session) -> list[Category]:
    return _ordered_generic(session, Category, "category_order")


def save_category_order(session: Session, ids: list[int]):
    _save_order_generic(session, ids, Category, "category_order")


def get_bins_ordered(session: Session) -> list[Bin]:
    return _ordered_generic(session, Bin, "bin_order")


def save_bin_order(session: Session, ids: list[int]):
    _save_order_generic(session, ids, Bin, "bin_order")


def get_locations_ordered(session: Session) -> list[Location]:
    return _ordered_generic(session, Location, "location_order")


def save_location_order(session: Session, ids: list[int]):
    _save_order_generic(session, ids, Location, "location_order")


def ensure_default_units(session: Session):
    """Ensure the default unit set exists, backfilling any missing rows."""
    existing = {
        (u.name or "").strip().lower()
        for u in session.exec(select(UnitOption)).all()
    }
    added = False
    # Avoid expiring other objects when we commit seeds
    orig_expire = session.expire_on_commit
    session.expire_on_commit = False
    for entry in DEFAULT_UNIT_ENTRIES:
        name = entry["name"]
        if name.lower() in existing:
            continue
        session.add(
            UnitOption(
                name=name,
                adjustable=bool(entry.get("adjustable", False)),
            )
        )
        existing.add(name.lower())
        added = True
    if added:
        session.commit()
    session.expire_on_commit = orig_expire


def prune_noise_units(session: Session):
    """Remove stray unit rows that are empty or single-character noise."""
    bad_units = session.exec(
        select(UnitOption).where(
            (func.length(func.trim(UnitOption.name)) < 2)
            | (UnitOption.name.is_(None))
        )
    ).all()
    if not bad_units:
        return
    for u in bad_units:
        session.delete(u)
    session.commit()


def normalize_units(session: Session):
    """Trim names and merge duplicate units (case-insensitive)."""
    units = session.exec(select(UnitOption)).all()
    if not units:
        return
    seen: dict[str, UnitOption] = {}
    to_delete: list[UnitOption] = []
    for u in units:
        raw = (u.name or "").strip()
        if not raw:
            to_delete.append(u)
            continue
        key = raw.lower()
        if key in seen:
            # Merge adjustable flag; drop duplicate row
            seen[key].adjustable = seen[key].adjustable or u.adjustable
            to_delete.append(u)
            continue
        if u.name != raw:
            u.name = raw
        seen[key] = u
    if to_delete:
        for u in to_delete:
            session.delete(u)
    session.commit()


def _log_unit_snapshot(session: Session, label: str = "units"):
    """Debug helper to print unit state and item unit usage."""
    units = session.exec(select(UnitOption)).all()
    item_units = session.exec(
        select(Item.unit).where(Item.unit.is_not(None)).group_by(Item.unit)
    ).all()
    unit_names = [f"{u.name} ({'adj' if u.adjustable else 'locked'})" for u in units]
    print(f"[UNIT] Snapshot [{label}] stored={len(units)} items={len(item_units)}")
    print(f"[UNIT] Stored: {unit_names}")
    print(f"[UNIT] Item units: {[ (row[0] or '').strip() for row in item_units ]}")


def ensure_units_from_items(session: Session):
    """Backfill UnitOption entries for any units already used on items."""
    ensure_default_units(session)
    normalize_units(session)
    prune_noise_units(session)
    existing = {
        (u.name or "").strip().lower()
        for u in session.exec(select(UnitOption)).all()
    }
    units_in_items = session.exec(
        select(Item.unit).where(Item.unit.is_not(None)).group_by(Item.unit)
    ).all()
    added = False
    orig_expire = session.expire_on_commit
    session.expire_on_commit = False
    for row in units_in_items:
        name = (row[0] or "").strip()
        # Skip empty or 1-character noise values
        if not name or len(name.strip()) < 2:
            continue
        key = name.lower()
        if key in existing:
            continue
        # Insert non-adjustable by default; track existing to avoid dup inserts this pass
        session.add(UnitOption(name=name, adjustable=False))
        existing.add(key)
        added = True
    if added:
        session.commit()
    session.expire_on_commit = orig_expire
    ordered = session.exec(select(UnitOption).order_by(UnitOption.created_at)).all()
    save_unit_order(session, [u.id for u in ordered])


def get_units_ordered(session: Session) -> list[UnitOption]:
    ensure_default_units(session)
    ensure_units_from_items(session)
    return _ordered_generic(session, UnitOption, "unit_order")


def save_unit_order(session: Session, ids: list[int]):
    _save_order_generic(session, ids, UnitOption, "unit_order")


def get_unit_names(session: Session) -> list[str]:
    return [u.name for u in get_units_ordered(session)]


def get_adjustable_unit_names(session: Session) -> set[str]:
    ensure_default_units(session)
    ensure_units_from_items(session)
    units = session.exec(
        select(UnitOption).where(UnitOption.adjustable == True)  # noqa: E712
    ).all()
    result = set()
    for u in units:
        name = (u.name or "").strip().lower()
        if name:
            result.add(name)
    return result


def ensure_unit_entry(session: Session, value: str):
    """Ensure a unit exists in UnitOption list (defaults to non-adjustable)."""
    if not value:
        return
    ensure_default_units(session)
    existing = session.exec(
        select(UnitOption).where(func.lower(UnitOption.name) == value.lower())
    ).first()
    if existing:
        return existing
    unit_obj = UnitOption(name=value, adjustable=False)
    session.add(unit_obj)
    session.commit()
    session.refresh(unit_obj)
    current_order = [u.id for u in get_units_ordered(session)]
    if unit_obj.id not in current_order:
        current_order.append(unit_obj.id)
        save_unit_order(session, current_order)
    return unit_obj


def get_required_field_keys(session: Session) -> list[str]:
    raw = _get_setting(session, "required_fields")
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [k for k in data if k in REQUIRED_FIELD_LABELS]
        except Exception:
            pass
    return list(DEFAULT_REQUIRED_FIELDS)


def get_app_heading(session: Session) -> str:
    return _get_setting(session, "app_heading", APP_HEADING_DEFAULT) or APP_HEADING_DEFAULT


def save_app_heading(session: Session, heading: str):
    heading = (heading or APP_HEADING_DEFAULT).strip() or APP_HEADING_DEFAULT
    _set_setting(session, "app_heading", heading)


def _hash_pw(pw: str) -> str:
    return hashlib.sha256((pw or "").encode("utf-8")).hexdigest()


def get_admin_password_hash(session: Session) -> str:
    stored = _get_setting(session, "admin_password_hash")
    if stored:
        return stored
    default_hash = _hash_pw(ADMIN_DEFAULT_PASSWORD)
    _set_setting(session, "admin_password_hash", default_hash)
    return default_hash


def set_admin_password(session: Session, new_password: str):
    _set_setting(session, "admin_password_hash", _hash_pw(new_password))


def save_required_field_keys(session: Session, keys: list[str]):
    valid = [k for k in keys if k in REQUIRED_FIELD_LABELS]
    _set_setting(session, "required_fields", json.dumps(valid))


# -----------------------------
# Backup helpers
# -----------------------------
def get_backup_options(session: Session) -> dict:
    raw = _get_setting(session, "backup_options")
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return {**BACKUP_DEFAULT_OPTIONS, **data}
        except Exception:
            pass
    return dict(BACKUP_DEFAULT_OPTIONS)


def save_backup_options(session: Session, opts: dict):
    merged = {**BACKUP_DEFAULT_OPTIONS, **opts}
    _set_setting(session, "backup_options", json.dumps(merged))


def get_backup_target_dir(session: Session) -> str:
    opts = get_backup_options(session)
    target = opts.get("target_dir") or BACKUP_DEFAULT_OPTIONS["target_dir"]
    return target


def get_backup_schedule(session: Session) -> dict:
    raw = _get_setting(session, "backup_schedule")
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return {
                    "enabled": bool(data.get("enabled", False)),
                    "time": data.get("time", "02:00"),
                }
        except Exception:
            pass
    return {"enabled": False, "time": "02:00"}


def save_backup_schedule(session: Session, enabled: bool, time_str: str):
    if not time_str:
        time_str = "02:00"
    _set_setting(session, "backup_schedule", json.dumps({"enabled": enabled, "time": time_str}))


def get_theme(session: Session) -> str:
    raw = _get_setting(session, "theme")
    if raw in ("light", "dark"):
        return raw
    return THEME_DEFAULT


def save_theme(session: Session, theme: str):
    if theme not in ("light", "dark"):
        theme = THEME_DEFAULT
    _set_setting(session, "theme", theme)


def _export_csv_bytes(session: Session, fields: list[str] | None = None) -> bytes:
    import csv
    items = session.exec(select(Item)).all()
    use_fields = fields or list(EXPORTABLE_FIELD_KEYS)
    # ensure valid keys only
    use_fields = [f for f in use_fields if f in EXPORTABLE_FIELD_KEYS]
    if not use_fields:
        use_fields = list(EXPORTABLE_FIELD_KEYS)

    headers = []
    for key in use_fields:
        label = next((f["label"] for f in EXPORTABLE_FIELDS if f["key"] == key), key)
        headers.append(label)

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for i in items:
        row = []
        for key in use_fields:
            val = getattr(i, key, "")
            if val is None:
                val = ""
            row.append(val)
        w.writerow(row)
    return buf.getvalue().encode("utf-8")


def list_backups() -> list[dict]:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = []
    for fname in os.listdir(BACKUP_DIR):
        if not fname.lower().endswith(".zip"):
            continue
        path = os.path.join(BACKUP_DIR, fname)
        try:
            stat = os.stat(path)
            files.append(
                {
                    "name": fname,
                    "path": path,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                }
            )
        except OSError:
            continue
    files.sort(key=lambda f: f["mtime"], reverse=True)
    return files


def _safe_backup_path(filename: str) -> str | None:
    try:
        fname = os.path.basename(filename)
    except Exception:
        return None
    path = os.path.join(BACKUP_DIR, fname)
    if os.path.isfile(path):
        return path
    return None


def check_ipp_status() -> str:
    host = IPP_HOST
    if not host or not IPP_PRINTER:
        return "Not configured"
    if ":" in host:
        h, p = host.split(":", 1)
        try:
            port = int(p)
        except Exception:
            port = 631
    else:
        h, port = host, 631
    try:
        with socket.create_connection((h, port), timeout=2):
            return "Reachable"
    except Exception:
        return "Unreachable"


def get_disk_usage(path: str) -> dict:
    try:
        total, used, free = shutil.disk_usage(path)
        return {"total": total, "used": used, "free": free}
    except Exception:
        return {"total": 0, "used": 0, "free": 0}


def create_backup_zip(opts: dict, session: Session, target_dir: str | None = None) -> tuple[str, str]:
    """Create a backup zip on disk. Returns (path, filename)."""
    target_dir = target_dir or BACKUP_DIR
    os.makedirs(target_dir, exist_ok=True)
    ts = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    fname = f"inventory-backup-{ts}.zip"
    fpath = os.path.join(target_dir, fname)

    with zipfile.ZipFile(fpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        info = {
            "created_utc": dt.datetime.utcnow().isoformat() + "Z",
            "options": opts,
        }
        zf.writestr("backup_info.json", json.dumps(info, indent=2))

        if opts.get("include_db") and os.path.isfile(DB_PATH):
            zf.write(DB_PATH, arcname="inventory.db")

        if opts.get("include_photos") and os.path.isdir(PHOTOS_DIR):
            for root, dirs, files in os.walk(PHOTOS_DIR):
                for f in files:
                    abs_path = os.path.join(root, f)
                    rel = os.path.relpath(abs_path, PHOTOS_DIR)
                    zf.write(abs_path, arcname=os.path.join("photos", rel))

        if opts.get("include_export"):
            csv_bytes = _export_csv_bytes(session)
            zf.writestr("export.csv", csv_bytes)

        if opts.get("include_config") and os.path.isfile(ADDON_OPTIONS_PATH):
            zf.write(ADDON_OPTIONS_PATH, arcname="options.json")

    return fpath, fname


def restore_backup(zip_path: str) -> dict:
    """Restore DB/photos/options from a backup zip. Returns a summary dict."""
    summary = {"db": False, "photos": 0, "options": False}

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                if member.startswith("/") or ".." in member.split("/"):
                    continue  # skip unsafe entries

                if member == "inventory.db":
                    target = os.path.join(tmpdir, "inventory.db")
                    zf.extract(member, path=tmpdir)
                    # backup existing db
                    try:
                        if os.path.isfile(DB_PATH):
                            shutil.copyfile(DB_PATH, DB_PATH + ".bak")
                        shutil.copyfile(target, DB_PATH)
                        summary["db"] = True
                    except Exception as e:
                        print("[RESTORE] DB restore error", e)

                elif member.startswith("photos/"):
                    zf.extract(member, path=tmpdir)
                    rel_path = member[len("photos/") :]
                    dest = os.path.join(PHOTOS_DIR, rel_path)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copyfile(os.path.join(tmpdir, member), dest)
                    summary["photos"] += 1

                elif member == "options.json":
                    zf.extract(member, path=tmpdir)
                    try:
                        shutil.copyfile(os.path.join(tmpdir, member), ADDON_OPTIONS_PATH)
                        summary["options"] = True
                    except Exception as e:
                        print("[RESTORE] options restore error", e)
    return summary


def run_scheduled_backup():
    """Background loop to perform scheduled backups once per day."""
    while True:
        try:
            with Session(engine) as session:
                schedule = get_backup_schedule(session)
                if not schedule.get("enabled"):
                    # sleep and check again later
                    time.sleep(60)
                    continue

                target_time = schedule.get("time", "02:00")
                try:
                    hour, minute = [int(x) for x in target_time.split(":")]
                except Exception:
                    hour, minute = 2, 0

                now = dt.datetime.now()
                last_key = "backup_last_auto"
                last_val = _get_setting(session, last_key)
                last_date = last_val or ""

                today_str = now.date().isoformat()
                if last_date == today_str:
                    time.sleep(60)
                    continue

                if now.hour > hour or (now.hour == hour and now.minute >= minute):
                    opts = get_backup_options(session)
                    target_dir = opts.get("target_dir") or BACKUP_DIR
                    create_backup_zip(opts, session, target_dir=target_dir)
                    _set_setting(session, last_key, today_str)
        except Exception as e:
            print("[BACKUP] scheduler error", e)
        time.sleep(60)


def next_serial(session: Session) -> str:
    """Generate a new serial using a configurable prefix + UUID."""
    return f"{SERIAL_PREFIX}{uuid.uuid4()}"


def _request_base_url(request: Request) -> str | None:
    """
    Compose a base URL (scheme + host + ingress prefix) using proxy headers.
    """
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        return None
    prefix = (
        request.headers.get("x-ingress-path")
        or request.headers.get("x-forwarded-prefix")
        or request.scope.get("root_path", "")
    )
    prefix = prefix.rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{proto}://{host}{prefix}"


def build_item_link(item: Item, request: Request | None = None) -> str:
    """
    Build the URL encoded into the QR code and shown as 'Open link'.
    """
    serial = item.serial_number

    if BASE_URL:
        base = BASE_URL.rstrip("/")
        return f"{base}/item/by-serial/{serial}"
    if request:
        base = _request_base_url(request)
        if base:
            return f"{base}/item/{item.id}"
        return str(request.url_for("show_item", item_id=item.id))

    # Last resort: plain serial text
    return serial


# -----------------------------
# App + middleware
# -----------------------------
app = FastAPI(title="Inventory & Labels")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals["css_version"] = str(int(dt.datetime.utcnow().timestamp()))
templates.env.globals["format_datetime"] = format_datetime  # <-- global for Jinja
templates.env.globals["BASE_URL"] = BASE_URL
templates.env.globals["app_version"] = APP_VERSION
templates.env.globals["max_label_copies"] = MAX_LABEL_COPIES


class PrefixFromHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        xip = request.headers.get("x-ingress-path")
        xfp = request.headers.get("x-forwarded-prefix")
        if xip:
            request.scope["root_path"] = xip
        elif xfp:
            request.scope["root_path"] = xfp
        return await call_next(request)


class LoggerMW(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        root_path = request.scope.get("root_path", "")
        print(
            f">>> {request.method} {request.url.path} "
            f"q={request.url.query} root={root_path}"
        )
        resp = await call_next(request)
        if resp.status_code >= 300:
            print(
                f"<<< {resp.status_code} {request.method} {request.url.path} "
                f"root={root_path} referer={request.headers.get('referer','')} "
                f"xfp={request.headers.get('x-forwarded-prefix','')} "
                f"xip={request.headers.get('x-ingress-path','')} "
                f"loc={resp.headers.get('location','')}"
            )
        else:
            print(f"<<< {resp.status_code} {request.method} {request.url.path}")
        return resp


app.add_middleware(PrefixFromHeaders)
app.add_middleware(LoggerMW)
app.add_middleware(GZipMiddleware, minimum_size=512)

@app.on_event("startup")
def _log_port_notice():
    host_port = os.environ.get("PORT", APP_INTERNAL_PORT)
    print(
        f"[startup] Container listening on :{APP_INTERNAL_PORT}; "
        "the HA Network tab controls the host port mapping. "
        f"(env PORT={host_port})"
    )
    # Enable WAL + sync tweak, and ensure common indexes exist for faster filters/search
    with engine.connect() as conn:
        try:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            print("[startup] Enabled SQLite WAL mode")
        except Exception as e:
            print(f"[startup] Could not enable WAL: {e}")

        def ensure_index(name: str, ddl: str):
            try:
                exists = conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                    (name,),
                ).fetchone()
                if not exists:
                    conn.exec_driver_sql(ddl)
                    print(f"[MIGRATION] Created index {name}")
            except Exception as e:
                print(f"[MIGRATION] Could not create index {name}: {e}")

        ensure_index("idx_item_location", "CREATE INDEX idx_item_location ON item(location)")
        ensure_index("idx_item_bin", "CREATE INDEX idx_item_bin ON item(bin_number)")
        ensure_index("idx_item_category", "CREATE INDEX idx_item_category ON item(category)")
        ensure_index("idx_item_use_by", "CREATE INDEX idx_item_use_by ON item(use_by_date)")
        ensure_index("idx_item_depleted_at", "CREATE INDEX idx_item_depleted_at ON item(depleted_at)")
        ensure_index("idx_item_created_at", "CREATE INDEX idx_item_created_at ON item(created_at)")
    # Unit hygiene at startup: seed defaults, prune noise, and backfill from items
    with Session(engine, expire_on_commit=False) as session:
        ensure_units_from_items(session)
        _log_unit_snapshot(session, label="startup")

def _norm(s: str | None) -> str | None:
    if s is None:
        return None
    s2 = str(s).strip()
    return s2 if s2 else None


def _upsert_name(session: Session, model, value: str):
    """Insert row into model if a case-insensitive match does not already exist."""
    if not value:
        return
    existing = session.exec(
        select(model).where(func.lower(model.name) == value.lower())
    ).first()
    if existing:
        return existing
    obj = model(name=value)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def process_photo_upload(upload: UploadFile) -> str | None:
    """
    Resize/compress uploaded photo and store under PHOTOS_DIR.

    - Tries to convert everything to a sane JPEG (max 1600x1600, quality 80).
    - Falls back to saving the original bytes if Pillow cannot decode (e.g., unsupported HEIC build).
    """
    if not upload or not upload.filename:
        return None

    os.makedirs(PHOTOS_DIR, exist_ok=True)

    # Read the whole file once
    try:
        upload.file.seek(0)
    except Exception:
        pass
    data = upload.file.read()
    if len(data or b"") > MAX_PHOTO_BYTES:
        print(f"[PHOTO] upload rejected: {len(data)} bytes exceeds {MAX_PHOTO_BYTES}")
        return None
    original_ext = os.path.splitext(upload.filename)[1].lower()

    def _unique_name(ext: str) -> str:
        return os.path.join(
            PHOTOS_DIR,
            f"{int(dt.datetime.utcnow().timestamp())}_{uuid.uuid4().hex}{ext}",
        )

    target_path = _unique_name(".jpg")

    try:
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        img.thumbnail((1600, 1600))
        img.save(target_path, format="JPEG", quality=80, optimize=True)
        return target_path
    except Exception as e:
        print("[PHOTO] error processing image, saving original:", e)
        # If Pillow couldn't read it but HEIF support is available, try re-opening
        if HEIF_OK:
            try:
                img = Image.open(io.BytesIO(data))
                img = img.convert("RGB")
                img.thumbnail((1600, 1600))
                img.save(target_path, format="JPEG", quality=80, optimize=True)
                return target_path
            except Exception as e2:
                print("[PHOTO] HEIF retry failed:", e2)
        try:
            # Preserve recognizable extension when possible
            fallback_ext = (
                original_ext
                if original_ext in {".heic", ".heif", ".png", ".jpg", ".jpeg"}
                else ".bin"
            )
            raw_path = _unique_name(fallback_ext)
            with open(raw_path, "wb") as f:
                f.write(data)
            return raw_path
        except Exception as e2:
            print("[PHOTO] failed to save original bytes:", e2)
            return None


@app.on_event("startup")
def startup():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    init_db()

    # Debug: see what the container actually has in /app/static
    try:
        print("DEBUG BASE_DIR:", BASE_DIR)
        print("DEBUG STATIC_DIR:", STATIC_DIR)
        print("DEBUG STATIC_DIR exists:", os.path.isdir(STATIC_DIR))
        print("DEBUG STATIC_DIR contents:", os.listdir(STATIC_DIR))
    except Exception as e:
        print("DEBUG STATIC_DIR error:", e)

    # ---- Ensure existing rows at least have serial/barcode values ----
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        changed_serial = 0
        changed_barcode = 0
        for i in items:
            if not (i.serial_number or "").strip():
                i.serial_number = next_serial(session)
                changed_serial += 1
            if not (i.barcode or "").strip():
                i.barcode = i.serial_number
                changed_barcode += 1

        if changed_serial or changed_barcode:
            session.commit()
            print(
                f"[MIGRATION] Added serials to {changed_serial} item(s) "
                f"and barcodes to {changed_barcode} item(s)."
            )
        else:
            print("[MIGRATION] No serial/barcode backfill needed.")

    # Start backup scheduler thread (daemon)
    def _start_scheduler():
        t = threading.Thread(target=run_scheduled_backup, daemon=True)
        t.start()
    _start_scheduler()


# -----------------------------
# Label image helpers
# -----------------------------
def make_label_image(
    item: Item,
    preset: LabelPreset | None = None,
    link_override: str | None = None,
) -> Image.Image:
    """
    Build the PIL.Image for a DYMO label (89x28mm @ 300 dpi).

    If a LabelPreset is provided, it controls:
      - which fields are printed
      - whether QR is shown
      - font scale
      - basic alignment (left / center)
    """
    dpi = 300
    w = int((89 / 25.4) * dpi)  # 89mm wide
    h = int((28 / 25.4) * dpi)  # 28mm high

    img = Image.new("L", (w, h), color=255)
    draw = ImageDraw.Draw(img)

    # --- Fonts -----------------------------------------------------------
    candidates_bold = [
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates_regular = [
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    candidates_mono = [
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]

    def _font(paths, size, fallback=None):
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return fallback or ImageFont.load_default()

    # Advanced “font scale” from preset
    scale = 1.0
    if preset is not None:
        try:
            scale = max(0.6, min(1.4, float(preset.font_scale or 1.0)))
        except Exception:
            scale = 1.0

    font_title = _font(candidates_bold, int(48 * scale))
    font_small = _font(candidates_regular, int(28 * scale))
    font_mono = _font(candidates_mono, 20)

    include_qr = True if preset is None else bool(preset.include_qr)

    # --- QR code (optional) ---------------------------------------------
    x = 10
    if include_qr:
        link_text = link_override or build_item_link(item)
        qr = qrcode.make(link_text, image_factory=qrcode.image.pil.PilImage)
        qr_size = h - 20
        qr = qr.resize((qr_size, qr_size), Image.NEAREST)
        img.paste(qr, (10, 10))
        x = 20 + qr_size  # text starts to the right of QR
    else:
        x = 20

    # --- Title (Name) ---------------------------------------------------
    title = (item.name or "").strip() or "Item"
    max_title_width = w - x - 10

    def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if not test:
                continue
            bbox = font.getbbox(test)
            line_w = bbox[2] - bbox[0]
            if line_w <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                    current = word
                else:
                    # single long word: take it as-is on its own line
                    lines.append(word)
                    current = ""
        if current:
            lines.append(current)
        return lines

    lines = wrap_text(title, font_title, max_title_width)
    max_lines = 3
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # Ellipsize the last line to fit
        last = lines[-1]
        ellipsis = "…"
        while last and (
            font_title.getbbox(last + ellipsis)[2]
            - font_title.getbbox(last + ellipsis)[0]
            > max_title_width
        ):
            last = last[:-1]
        lines[-1] = (last.rstrip() + ellipsis) if last else ellipsis

    line_height = font_title.getbbox("Ag")[3] - font_title.getbbox("Ag")[1]
    y = 6
    for line in lines:
        bbox = font_title.getbbox(line)
        line_w = bbox[2] - bbox[0]
        if preset is not None and preset.align_center:
            text_x = x + max(0, (w - x - line_w) // 2)
        else:
            text_x = x
        draw.text((text_x, y), line, font=font_title, fill=0)
        y += line_height + 2
    y += 2  # small gap before details

    # --- Detail lines (according to preset) -----------------------------
    lines: list[str] = []

    if preset is None:
        # old behaviour: only Use-by if present
        if item.use_by_date:
            lines.append(f"Use-by: {item.use_by_date}")
    else:
        if preset.include_location and item.location:
            lines.append(f"Loc: {item.location}")
        if preset.include_bin and item.bin_number:
            lines.append(f"Bin: {item.bin_number}")

        if preset.include_qty_unit:
            qty = item.quantity
            unit = (item.unit or "").strip()
            if unit:
                lines.append(f"Qty: {qty} {unit}")
            else:
                lines.append(f"Qty: {qty}")

        if preset.include_condition and item.condition:
            lines.append(f"Cond: {item.condition}")

        if preset.include_cook_date and item.cook_date:
            lines.append(f"Cook: {item.cook_date}")

        if preset.include_use_by and item.use_by_date:
            lines.append(f"Use-by: {item.use_by_date}")

        # Use Within (string field on Item; getattr for safety)
        use_within_value = getattr(item, "use_within", None)
        if preset.include_use_within and use_within_value:
            lines.append(f"Use within: {use_within_value}")

    # Render detail lines
    small_line_h = font_small.getbbox("Ag")[3] - font_small.getbbox("Ag")[1]
    for line in lines:
        if not line:
            continue
        bbox = font_small.getbbox(line)
        line_w = bbox[2] - bbox[0]

        if preset is not None and preset.align_center:
            lx = x + max(0, (w - x - line_w) // 2)
        else:
            lx = x

        draw.text((lx, y), line, font=font_small, fill=0)
        y += small_line_h + 2

    # --- Serial (always printed, under QR area) -------------------------
    serial_text = item.serial_number
    base_y = h - (font_mono.getbbox("123")[3] - font_mono.getbbox("123")[1]) - 4
    draw.text((10, base_y), serial_text, font=font_mono, fill=0)

    return img


def make_label_png(
    item: Item,
    preset: LabelPreset | None = None,
    link_override: str | None = None,
) -> bytes:
    """
    Return PNG bytes for the label image.
    """
    img = make_label_image(item, preset, link_override=link_override)
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(300, 300))
    return buf.getvalue()


def make_quick_label_image(title: str, description: str) -> Image.Image:
    """
    Simple label image used for Quick Labels (no QR, no DB item).
    """
    dpi = 300
    w = int((89 / 25.4) * dpi)  # 89mm
    h = int((28 / 25.4) * dpi)  # 28mm

    img = Image.new("L", (w, h), color=255)
    draw = ImageDraw.Draw(img)

    candidates_bold = [
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates_regular = [
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    def _font(paths, size, fallback=None):
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return fallback or ImageFont.load_default()

    font_title = _font(candidates_bold, 40)
    font_body = _font(candidates_regular, 24)

    title = (title or "").strip() or "Label"
    desc = (description or "").strip()

    # Title
    y = 6
    bbox = font_title.getbbox(title)
    x = 10
    draw.text((x, y), title, font=font_title, fill=0)
    y += (bbox[3] - bbox[1]) + 6

    # Description: simple word wrap
    max_width = w - 20
    words = desc.split()
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        tb = font_body.getbbox(test)
        tw = tb[2] - tb[0]
        if tw > max_width and line:
            draw.text((x, y), line, font=font_body, fill=0)
            y += (tb[3] - tb[1]) + 2
            line = word
        else:
            line = test
    if line:
        draw.text((x, y), line, font=font_body, fill=0)

    return img


# -----------------------------
# Helpers
# -----------------------------
def _choices(session: Session):
    cats = [c.name for c in get_categories_ordered(session)]
    bins = [b.name for b in get_bins_ordered(session)]
    locations = [l.name for l in get_locations_ordered(session)]
    use_withins = [u.name for u in get_use_withins_ordered(session)]
    return cats, bins, locations, use_withins


def get_item_photos(session: Session, item_id: int, include_missing: bool = False) -> list[ItemPhoto]:
    """Fetch photos for an item. Optionally filter out rows whose files are gone."""
    photos = session.exec(
        select(ItemPhoto)
        .where(ItemPhoto.item_id == item_id)
        .order_by(ItemPhoto.created_at)
    ).all()
    if include_missing:
        return photos
    return [p for p in photos if os.path.isfile(p.path)]


def _delete_photo_file(path: str):
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except Exception as e:
        print("[PHOTO] delete error", e)


def _save_item_photos(session: Session, item: Item, uploads: List[UploadFile] | None):
    """Persist uploaded photos for an item and set legacy photo_path if empty."""
    if not uploads:
        return
    added_first = False
    for up in uploads:
        try:
            up.file.seek(0)
        except Exception:
            pass
        path = process_photo_upload(up)
        if not path:
            continue
        photo = ItemPhoto(item_id=item.id, path=path)
        session.add(photo)
        if not added_first and not item.photo_path:
            item.photo_path = path
            added_first = True
    session.commit()
    if added_first:
        session.refresh(item)


def get_default_preset(session: Session) -> LabelPreset:
    """
    Fetch the default label preset.

    If none exists yet, create a sensible 'Default' preset and return it.
    """
    preset = session.exec(
        select(LabelPreset).where(LabelPreset.is_default == True)
    ).first()
    if preset:
        return preset

    # Auto-create a basic default preset
    preset = LabelPreset(
        name="Default",
        media="w79h252",
        include_name=True,
        include_location=True,
        include_bin=True,
        include_qty_unit=True,
        include_condition=False,
        include_cook_date=False,
        include_use_by=True,
        include_use_within=False,
        include_qr=True,
        align_center=False,
        font_scale=1.0,
        is_default=True,
    )
    session.add(preset)
    session.commit()
    session.refresh(preset)
    return preset


def _get_item_or_404(session: Session, item_id: int) -> Item:
    item = session.get(Item, item_id)
    if not item:
        raise RuntimeError("Not Found")
    return item


# -----------------------------
# Backup routes
# -----------------------------
@app.get("/backup", name="backup_page", response_class=HTMLResponse)
def backup_page(request: Request):
    # Require admin auth cookie just like /admin
    with Session(engine) as session:
        stored_hash = get_admin_password_hash(session)
        cookie_token = request.cookies.get("admin_auth", "")
        if cookie_token != stored_hash:
            return RedirectResponse(
                url=str(request.url_for("admin")) + "?next=backup",
                status_code=303,
            )

    with Session(engine) as session:
        opts = get_backup_options(session)
        schedule = get_backup_schedule(session)
        export_fields = EXPORTABLE_FIELDS
        msg = request.query_params.get("msg", "")
        err = request.query_params.get("err", "")
        backups = list_backups()
    return templates.TemplateResponse(
        "backup.html",
        {
            "request": request,
            "options": opts,
            "schedule": schedule,
            "export_fields": export_fields,
            "backups": backups,
            "msg": msg,
            "err": err,
        },
    )


@app.post("/backup/run")
def backup_run(
    include_db: bool = Form(False),
    include_photos: bool = Form(False),
    include_export: bool = Form(False),
    include_config: bool = Form(False),
    backup_target_dir: str = Form(""),
    schedule_enabled: bool = Form(False),
    schedule_time: str = Form("02:00"),
):
    opts = {
        "include_db": include_db,
        "include_photos": include_photos,
        "include_export": include_export,
        "include_config": include_config,
        "target_dir": backup_target_dir.strip() or BACKUP_DEFAULT_OPTIONS["target_dir"],
    }

    with Session(engine) as session:
        save_backup_options(session, opts)
        save_backup_schedule(session, schedule_enabled, schedule_time)
        path, fname = create_backup_zip(opts, session, target_dir=opts["target_dir"])

    return FileResponse(
        path,
        media_type="application/zip",
        filename=fname,
    )


@app.post("/export/custom")
def export_custom(fields: list[str] = Form(None)):
    with Session(engine) as session:
        use_fields = fields or EXPORTABLE_FIELD_KEYS
        csv_bytes = _export_csv_bytes(session, use_fields)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_export.csv"},
    )


@app.post("/item/{item_id}/adjust-qty")
def adjust_qty(
    request: Request,
    item_id: int,
    delta: int = Form(...),
    redirect_to: str = Form(""),
):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            return RedirectResponse(
                url=str(request.url_for("index")),
                status_code=303,
            )
        if item.depleted_at:
            if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                return JSONResponse({"ok": False, "reason": "depleted"}, status_code=400)
            target = redirect_to or str(request.url_for("index"))
            return RedirectResponse(url=target, status_code=303)

        adjustable_units = get_adjustable_unit_names(session)
        unit_norm = (item.unit or "").strip().lower()
        if unit_norm not in adjustable_units:
            if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                return JSONResponse({"ok": False, "reason": "unit_not_adjustable"}, status_code=400)
            target = redirect_to or str(request.url_for("index"))
            return RedirectResponse(url=target, status_code=303)
        try:
            new_qty = max(0, item.quantity + int(delta))
        except Exception:
            new_qty = item.quantity
        item.quantity = new_qty
        session.add(item)
        session.commit()
    # If this was an AJAX/fetch request, return JSON so the UI can update in-place
    if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
        return JSONResponse({"ok": True, "quantity": new_qty})
    target = redirect_to or str(request.url_for("index"))
    return RedirectResponse(url=target, status_code=303)


@app.post("/item/{item_id}/deplete")
def deplete_item(
    request: Request,
    item_id: int,
    reason: str = Form(""),
):
    reason_clean = _norm(reason) or ""
    if reason_clean and reason_clean not in DEPLETION_REASONS:
        reason_clean = "Other"
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            return RedirectResponse(url=str(request.url_for("index")), status_code=303)
        if item.depleted_at:
            return RedirectResponse(
                url=str(request.url_for("show_item", item_id=item_id)),
                status_code=303,
            )
        now_iso = dt.datetime.utcnow().isoformat()
        item.depleted_at = now_iso
        item.depleted_reason = reason_clean
        item.depleted_qty = item.quantity
        item.quantity = 0
        session.add(item)
        session.commit()
    return RedirectResponse(
        url=str(request.url_for("show_item", item_id=item_id)),
        status_code=303,
    )


@app.post("/item/{item_id}/recover")
def recover_item(
    request: Request,
    item_id: int,
):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            print(f"[recover] item {item_id} not found")
            return RedirectResponse(url=str(request.url_for("index")), status_code=303)
        if not item.depleted_at:
            print(f"[recover] item {item_id} not depleted; redirecting to show")
            return RedirectResponse(
                url=str(request.url_for("show_item", item_id=item_id)),
                status_code=303,
            )
        restore_qty = item.depleted_qty if item.depleted_qty is not None else (item.quantity or 1)
        item.depleted_at = None
        item.depleted_reason = None
        item.depleted_qty = None
        item.quantity = restore_qty
        session.add(item)
        session.commit()
        print(
            f"[recover] restored item {item_id}: qty={restore_qty} "
            f"photo_path={item.photo_path} photos={len(get_item_photos(session, item_id))}"
        )
    target = str(request.url_for("show_item", item_id=item_id))
    print(f"[recover] redirect -> {target}")
    return RedirectResponse(url=target, status_code=303)


@app.post("/import/csv")
async def import_csv(request: Request, file: UploadFile = File(...)):
    """Import items from a CSV whose columns match the export."""
    import csv

    if not file or not file.filename:
        target = str(request.url_for("backup_page")) + "?err=No+file+uploaded"
        print(f"[csv import] redirect -> {target}")
        return RedirectResponse(url=target, status_code=303)

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except Exception:
        target = str(request.url_for("backup_page")) + "?err=Invalid+file+encoding"
        print(f"[csv import] redirect -> {target}")
        return RedirectResponse(url=target, status_code=303)

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        target = str(request.url_for("backup_page")) + "?err=Missing+CSV+headers"
        print(f"[csv import] redirect -> {target}")
        return RedirectResponse(url=target, status_code=303)

    created = 0
    skipped = 0

    def _clean(v):
        return _norm(v) or None

    with Session(engine) as session:
        for row in reader:
            if not row:
                continue
            name = _clean(row.get("name"))
            if not name:
                skipped += 1
                continue

            qty_raw = _clean(row.get("quantity"))
            try:
                qty = int(qty_raw) if qty_raw is not None else 1
            except Exception:
                qty = 1
            depleted_qty_raw = _clean(row.get("depleted_qty"))
            try:
                depleted_qty = int(depleted_qty_raw) if depleted_qty_raw is not None else None
            except Exception:
                depleted_qty = None

            serial = _clean(row.get("serial_number"))
            if serial:
                existing = session.exec(
                    select(Item).where(Item.serial_number == serial)
                ).first()
                if existing:
                    serial = None
            serial = serial or next_serial(session)

            item = Item(
                serial_number=serial,
                name=name,
                category=_clean(row.get("category")),
                tags=_clean(row.get("tags")),
                location=_clean(row.get("location")),
                bin_number=_clean(row.get("bin_number")),
            quantity=qty,
            unit=_clean(row.get("unit")) or "each",
            barcode=_clean(row.get("barcode")),
            second_serial_number=_clean(row.get("second_serial_number")),
            condition=_clean(row.get("condition")),
                cook_date=_clean(row.get("cook_date")),
                use_by_date=_clean(row.get("use_by_date")),
                use_within=_clean(row.get("use_within")),
                notes=_clean(row.get("notes")),
                photo_path=_clean(row.get("photo_path")),
                last_audit_date=_clean(row.get("last_audit_date")),
                depleted_at=_clean(row.get("depleted_at")),
                depleted_reason=_clean(row.get("depleted_reason")),
                depleted_qty=depleted_qty,
                created_at=_clean(row.get("created_at")) or dt.datetime.utcnow().isoformat(),
            )
            session.add(item)
            created += 1
            # ensure related lookups exist for filters/quick lists
            _upsert_name(session, Category, item.category or "")
            _upsert_name(session, Bin, item.bin_number or "")
            _upsert_name(session, Location, item.location or "")
        session.commit()

    msg = f"CSV+import+ok:+{created}+added"
    if skipped:
        msg += f",+{skipped}+skipped"
    target = str(request.url_for("backup_page")) + f"?msg={msg}"
    print(f"[csv import] redirect -> {target}")
    return RedirectResponse(url=target, status_code=303)


@app.post("/backup/restore")
async def backup_restore(request: Request, file: UploadFile = File(...)):
    if not file or not file.filename:
        target = str(request.url_for("backup_page")) + "?err=No+file+uploaded"
        print(f"[backup restore upload] redirect -> {target}")
        return RedirectResponse(url=target, status_code=303)
    # Save uploaded file to temp and restore
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        summary = restore_backup(tmp_path)
        msg_parts = []
        if summary.get("db"):
            msg_parts.append("DB")
        if summary.get("photos"):
            msg_parts.append(f"Photos:{summary['photos']}")
        if summary.get("options"):
            msg_parts.append("Options")
        msg = "+".join(msg_parts) or "Restored"
        target = str(request.url_for("backup_page")) + f"?msg=Restore+ok:+{msg}"
        print(f"[backup restore upload] redirect -> {target}")
        return RedirectResponse(url=target, status_code=303)
    except Exception as e:
        target = str(request.url_for("backup_page")) + f"?err=Restore+failed"
        print(f"[backup restore upload] redirect -> {target} err={e}")
        return RedirectResponse(url=target, status_code=303)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@app.get("/backup/file/{filename}")
def backup_file(filename: str):
    path = _safe_backup_path(filename)
    if not path:
        return Response(status_code=404)
    return FileResponse(path, media_type="application/zip", filename=os.path.basename(path))


@app.post("/backup/restore/file")
def backup_restore_file(request: Request, filename: str = Form(...)):
    path = _safe_backup_path(filename)
    if not path:
        target = str(request.url_for("backup_page")) + "?err=Backup+not+found"
        print(f"[backup restore file] redirect -> {target}")
        return RedirectResponse(url=target, status_code=303)
    try:
        summary = restore_backup(path)
        msg_parts = []
        if summary.get("db"):
            msg_parts.append("DB")
        if summary.get("photos"):
            msg_parts.append(f"Photos:{summary['photos']}")
        if summary.get("options"):
            msg_parts.append("Options")
        msg = "+".join(msg_parts) or "Restored"
        target = str(request.url_for("backup_page")) + f"?msg=Restore+ok:+{msg}"
        print(f"[backup restore file] redirect -> {target}")
        return RedirectResponse(url=target, status_code=303)
    except Exception as e:
        target = str(request.url_for("backup_page")) + "?err=Restore+failed"
        print(f"[backup restore file] redirect -> {target} err={e}")
        return RedirectResponse(url=target, status_code=303)


@app.post("/backup/delete_all")
def delete_all_items(request: Request):
    """
    Danger: deletes every item (including depleted) and associated photos.
    Leaves categories/bins/locations intact for convenience.
    """
    print("[delete_all] wiping items + item photos")
    removed_photos = 0
    with Session(engine) as session:
        photos = session.exec(select(ItemPhoto)).all()
        for p in photos:
            if p.path:
                try:
                    # Stored paths are already safe/normalized when saved
                    if os.path.isfile(p.path):
                        os.remove(p.path)
                        removed_photos += 1
                except Exception as e:
                    print(f"[delete_all] failed to remove photo {p.path}: {e}")
            session.delete(p)
        deleted_items = session.exec(select(Item)).all()
        for it in deleted_items:
            session.delete(it)
        session.commit()
    msg = f"Deleted+{len(deleted_items)}+items"
    if removed_photos:
        msg += f"+and+{removed_photos}+photos"
    target = str(request.url_for("backup_page")) + f"?msg={msg}"
    print(f"[delete_all] redirect -> {target}")
    return RedirectResponse(url=target, status_code=303)


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    bin: Optional[str] = None,
    cook_date: Optional[str] = None,
    use_by_date: Optional[str] = None,
    tags: Optional[str] = None,
    page: int = 1,
    include_depleted: bool | str = False,
    depleted_reason: str = "",
):
    # Defaults to avoid unbound locals if something goes wrong
    items = []
    cats = []
    bins = []
    locations = []
    search_suggestions = []
    cat_counts = {}
    loc_counts = {}
    bin_counts = {}
    total_count = 0
    per_page = 50
    adjustable_units: list[str] = []

    # Normalize include_depleted query param
    if isinstance(include_depleted, str):
        include_depleted = include_depleted.lower() in ("1", "true", "yes", "on")

    # Handle deep-link ?serial=... from HA app and jump straight to item
    serial = request.query_params.get("serial")
    if serial:
        with Session(engine) as session:
            item = session.exec(
                select(Item).where(Item.serial_number == serial)
            ).first()
            if item:
                return RedirectResponse(
                    url=str(request.url_for("show_item", item_id=item.id)),
                    status_code=303,
                )

    page = max(1, int(page or 1))

    with Session(engine, expire_on_commit=False) as session:
        stmt = select(Item)

        # Global search: hit pretty much every useful field
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                (Item.name.like(like))
                | (Item.serial_number.like(like))
                | (Item.barcode.like(like))
                | (Item.tags.like(like))
                | (Item.notes.like(like))
                | (Item.location.like(like))
                | (Item.bin_number.like(like))
                | (Item.category.like(like))
                | (Item.unit.like(like))
                | (Item.condition.like(like))
                | (Item.cook_date.like(like))
                | (Item.use_by_date.like(like))
                | (Item.use_within.like(like))
            )

        # Individual filters
        if category:
            stmt = stmt.where(Item.category == category)
        if location:
            stmt = stmt.where(Item.location == location)
        if bin:
            stmt = stmt.where(Item.bin_number == bin)
        if cook_date:
            stmt = stmt.where(Item.cook_date == cook_date)
        if use_by_date:
            stmt = stmt.where(Item.use_by_date == use_by_date)
        if tags:
            stmt = stmt.where(Item.tags.like(f"%{tags}%"))
        if not include_depleted:
            stmt = stmt.where(Item.depleted_at.is_(None))
        if depleted_reason:
            stmt = stmt.where(Item.depleted_reason == depleted_reason)

        stmt_ordered = stmt.order_by(Item.created_at.desc())
        total_count = session.exec(select(func.count()).select_from(stmt.subquery())).one()
        items = session.exec(
            stmt_ordered.offset((page - 1) * per_page).limit(per_page)
        ).all()
        for it in items:
            object.__setattr__(it, "expiry_info", _expiry_info(it))

        # Choices for dropdowns (all known values, not just filtered ones)
        cats, bins, locations, _use_withins = _choices(session)
        display_fields = get_display_field_defs(session)
        # counts for quick filters
        cat_counts = {
            k: v
            for k, v in session.exec(
                select(Item.category, func.count())
                .where(Item.category.is_not(None))
                .where(Item.depleted_at.is_(None))
                .group_by(Item.category)
            )
        }
        loc_counts = {
            k: v
            for k, v in session.exec(
                select(Item.location, func.count())
                .where(Item.location.is_not(None))
                .where(Item.depleted_at.is_(None))
                .group_by(Item.location)
            )
        }
        bin_counts = {
            k: v
            for k, v in session.exec(
                select(Item.bin_number, func.count())
                .where(Item.bin_number.is_not(None))
                .where(Item.depleted_at.is_(None))
                .group_by(Item.bin_number)
            )
        }
        tag_suggestions = set()
        for i in session.exec(select(Item.tags)).all():
            if not i:
                continue
            for t in str(i).split(","):
                t2 = t.strip()
                if t2:
                    tag_suggestions.add(t2)
        search_suggestions = list({*cats, *bins, *locations, *tag_suggestions})
        app_heading = get_app_heading(session)
        adjustable_units = sorted(get_adjustable_unit_names(session))

    db_updated_at = _inventory_update_token()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": items if 'items' in locals() else [],
            "q": q or "",
            "category": category or "",
            "location": location or "",
            "bin": bin or "",
            "cook_date": cook_date or "",
            "use_by_date": use_by_date or "",
            "tags": tags or "",
            "depleted_reason": depleted_reason or "",
            "categories": cats,
            "cats": cats,
            "bins": bins,
            "locations": locations,
            "include_depleted": include_depleted,
            "DEPLETION_REASONS": DEPLETION_REASONS,
            "display_fields": display_fields,
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "search_suggestions": search_suggestions,
            "cat_counts": cat_counts,
            "loc_counts": loc_counts,
            "bin_counts": bin_counts,
            "app_heading": app_heading,
            "db_updated_at": db_updated_at,
            "adjustable_units": adjustable_units,
        },
)


@app.get("/depleted", response_class=HTMLResponse)
def depleted_items(
    request: Request,
    page: int = 1,
):
    with Session(engine) as session:
        stmt = select(Item).where(Item.depleted_at.is_not(None))
        stmt_ordered = stmt.order_by(Item.depleted_at.desc())
        per_page = 50
        page = max(1, int(page or 1))
        total_count = session.exec(select(func.count()).select_from(stmt.subquery())).one()
        items = session.exec(
            stmt_ordered.offset((page - 1) * per_page).limit(per_page)
        ).all()
        for it in items:
            created = _parse_date(it.created_at)
            cooked = _parse_date(it.cook_date)
            depleted = _parse_date(it.depleted_at)
            days_on_hand = None
            # Prefer cook_date to represent when the item was prepared; fall back to created_at
            basis = cooked or created
            if basis and depleted:
                days_on_hand = (depleted - basis).days
            object.__setattr__(it, "days_on_hand", days_on_hand)

    total_pages = max(1, (total_count + per_page - 1) // per_page)
    return templates.TemplateResponse(
        "depleted.html",
        {
            "request": request,
            "items": items,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_count": total_count,
        },
    )


@app.get("/api/items/updated-at")
def items_updated_at():
    """Expose a polling-friendly token so clients can auto-refresh when data changes."""
    return {"updated_at": _inventory_update_token()}


@app.api_route("/new", methods=["GET", "POST"], response_class=HTMLResponse)
async def new_item(
    request: Request,
    name: Optional[str] = Form(None),
    category: str = Form(""),
    tags: str = Form(""),
    location: str = Form(""),
    bin_number: str = Form(""),
    quantity: int = Form(1),
    unit: str = Form("each"),
    condition: str = Form(""),
    cook_date: str = Form(""),
    use_by_date: str = Form(""),
    use_within: str = Form(""),
    notes: str = Form(""),
    photos: List[UploadFile] = File([]),
):
    with Session(engine) as session:
        cats, bins, locations, use_withins = _choices(session)
        unit_names = get_unit_names(session)
        required_fields = get_required_field_keys(session)

    if request.method == "GET":
        return templates.TemplateResponse(
            "new.html",
            {
                "request": request,
                "cats": cats,
                "bins": bins,
                "locations": locations,
                "use_withins": use_withins,
                "units": unit_names,
                "required_fields": required_fields,
                "form_values": {},
                "error": "",
            },
        )

    # Normalize incoming strings to avoid duplicate-case issues and trim spaces
    name = _norm(name)
    category = _norm(category)
    tags = _norm(tags)
    location = _norm(location)
    bin_number = _norm(bin_number)
    unit = _norm(unit)
    condition = _norm(condition)
    cook_date = _norm(cook_date)
    use_by_date = _norm(use_by_date)
    use_within = _norm(use_within)
    notes = _norm(notes)

    def _missing_required() -> list[str]:
        missing: list[str] = []
        for key in required_fields:
            value = {
                "name": name,
                "category": category,
                "tags": tags,
                "location": location,
                "bin_number": bin_number,
                "quantity": quantity,
                "unit": unit,
                "condition": condition,
                "cook_date": cook_date,
                "use_by_date": use_by_date,
                "use_within": use_within,
                "notes": notes,
            }.get(key)

            if key == "quantity":
                if value is None:
                    missing.append(key)
                continue

            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(key)
        return missing

    missing = _missing_required()
    if missing:
        label_list = [REQUIRED_FIELD_LABELS.get(k, k) for k in missing]
        msg = "Required fields: " + ", ".join(label_list)
        return templates.TemplateResponse(
            "new.html",
            {
                "request": request,
                "cats": cats,
                "bins": bins,
                "locations": locations,
                "use_withins": use_withins,
                "units": unit_names,
                "required_fields": required_fields,
                "error": msg,
                "form_values": {
                    "name": name,
                    "category": category,
                    "tags": tags,
                    "location": location,
                    "bin_number": bin_number,
                    "quantity": quantity,
                    "unit": unit,
                    "condition": condition,
                    "cook_date": cook_date,
                    "use_by_date": use_by_date,
                    "use_within": use_within,
                    "notes": notes,
                },
            },
            status_code=400,
        )

    with Session(engine) as session:
        _upsert_name(session, Category, category)
        _upsert_name(session, Bin, bin_number)
        _upsert_name(session, Location, location)
        _upsert_name(session, UseWithin, use_within)
        ensure_unit_entry(session, unit)
        ensure_unit_entry(session, unit)

        serial = next_serial(session)
        item = Item(
            serial_number=serial,
            name=name or "Unnamed Item",
            category=category or None,
            tags=tags or None,
            location=location or None,
            bin_number=bin_number or None,
            quantity=quantity,
            unit=unit or None,
            condition=condition or None,
            cook_date=cook_date or None,
            use_by_date=use_by_date or None,
            use_within=use_within or None,
            notes=notes or None,
            barcode=serial,
            photo_path=None,
        )
        session.add(item)
        session.commit()
        session.refresh(item)

        item_id = item.id

        _save_item_photos(session, item, photos)

    return RedirectResponse(
        url=str(request.url_for("show_item", item_id=item_id)), status_code=303
    )


@app.get("/item/{item_id}", name="show_item", response_class=HTMLResponse)
def show_item(request: Request, item_id: int):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            print(f"[show_item] item {item_id} not found")
            return Response(status_code=404)
        photos = get_item_photos(session, item_id)
        object.__setattr__(item, "expiry_info", _expiry_info(item))
        print(
            f"[show_item] item {item_id} depleted={bool(item.depleted_at)} "
            f"photos={len(photos)}"
        )

    link = build_item_link(item, request=request)

    # One-shot flag to auto-open the edit modal
    auto_edit = request.query_params.get("auto_edit") == "1"

    return templates.TemplateResponse(
        "show.html",
        {
            "request": request,
            "item": item,
            "photos": photos,
            "qr_link": link,
            "auto_edit": auto_edit,
            "expiry_info": item.expiry_info,
        },
    )


@app.get("/item/by-serial/{serial}", response_class=HTMLResponse)
def show_by_serial(request: Request, serial: str):
    with Session(engine) as session:
        item = session.exec(
            select(Item).where(Item.serial_number == serial)
        ).first()
        if not item:
            return Response(status_code=404)
        photos = get_item_photos(session, item.id)
        object.__setattr__(item, "expiry_info", _expiry_info(item))
    link = build_item_link(item, request=request)
    return templates.TemplateResponse(
        "show.html",
        {
            "request": request,
            "item": item,
            "photos": photos,
            "qr_link": link,
            "expiry_info": _expiry_info(item),
            "DEPLETION_REASONS": DEPLETION_REASONS,
        },
    )


@app.get("/reports", name="reports", response_class=HTMLResponse)
def reports(
    request: Request,
    horizon: str = "60",
    category: str = "",
    location: str = "",
):
    horizon_map = {"7": 7, "14": 14, "30": 30, "60": 60, "all": None}
    horizon_days = horizon_map.get(horizon, 60)
    today = dt.date.today()

    summary = {"overdue": 0, "d7": 0, "d14": 0, "d30": 0, "d60": 0, "total": 0}
    expiring: list[Item] = []
    heatmap: dict[str, dict[str, int]] = {}
    category_counts: dict[str, int] = {}
    location_counts: dict[str, int] = {}
    depleted_records: list[dict] = []
    bucket_items: dict[str, list[Item]] = {
        "overdue": [],
        "d7": [],
        "d14": [],
        "d30": [],
        "d60": [],
    }
    total_items: list[Item] = []

    def parse_use_within(v: Optional[str]) -> Optional[int]:
        if not v:
            return None
        try:
            num = int(str(v).split()[0])
            return num
        except Exception:
            return None

    noncompliant = 0
    compliant_total = 0
    aging_buckets = {"expired": 0, "1-7": 0, "8-14": 0, "15-30": 0, "31-60": 0, "61+": 0}

    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        for it in items:
            object.__setattr__(it, "expiry_info", _expiry_info(it))

            # Filters
            if category and (it.category or "") != category:
                continue
            if location and (it.location or "") != location:
                continue

            if it.depleted_at:
                created = _parse_date(it.created_at)
                cooked = _parse_date(it.cook_date)
                depleted_date = _parse_date(it.depleted_at)
                if depleted_date:
                    lookback_ok = True
                    if horizon_days is not None:
                        lookback_ok = (today - depleted_date).days <= horizon_days
                    if lookback_ok:
                        doh = None
                        basis = cooked or created
                        if basis:
                            doh = (depleted_date - basis).days
                        depleted_records.append(
                            {
                                "item": it,
                                "depleted_date": depleted_date,
                                "days_on_hand": doh,
                            }
                        )
                continue

            if it.category:
                category_counts[it.category] = category_counts.get(it.category, 0) + 1
            if it.location:
                location_counts[it.location] = location_counts.get(it.location, 0) + 1

            info = it.expiry_info
            if info and horizon_days is not None and info["days"] > horizon_days:
                continue

            summary["total"] += 1
            days_until_expiry = info["days"] if info else None
            compliant_total += 1
            total_items.append(it)
            if info:
                if info["days"] < 0:
                    summary["overdue"] += 1
                    bucket_items["overdue"].append(it)
                elif info["days"] <= 7:
                    summary["d7"] += 1
                    bucket_items["d7"].append(it)
                elif info["days"] <= 14:
                    summary["d14"] += 1
                    bucket_items["d14"].append(it)
                elif info["days"] <= 30:
                    summary["d30"] += 1
                    bucket_items["d30"].append(it)
                elif info["days"] <= 60:
                    summary["d60"] += 1
                    bucket_items["d60"].append(it)

            if info:
                expiring.append(it)

            # Heatmap counts for items with a use-by date
            if info:
                cat = it.category or "Uncategorized"
                loc = it.location or "Unassigned"
                heatmap.setdefault(cat, {})
                heatmap[cat][loc] = heatmap[cat].get(loc, 0) + 1

            # Aging waterfall + use-within compliance
            created = _parse_date(it.created_at)
            days_on_hand = (today - created).days if created else None
            aging_basis = days_until_expiry if days_until_expiry is not None else days_on_hand
            if aging_basis is not None:
                # Group by days-until-expiry when available, otherwise by days on hand
                if aging_basis <= 0:
                    aging_buckets["expired"] += 1
                elif aging_basis <= 7:
                    aging_buckets["1-7"] += 1
                elif aging_basis <= 14:
                    aging_buckets["8-14"] += 1
                elif aging_basis <= 30:
                    aging_buckets["15-30"] += 1
                elif aging_basis <= 60:
                    aging_buckets["31-60"] += 1
                else:
                    aging_buckets["61+"] += 1
            # Use-by compliance: only flag items that are expired but not depleted.
            if days_until_expiry is not None and days_until_expiry <= 0:
                noncompliant += 1

    expiring_sorted = sorted(
        expiring,
        key=lambda i: (
            i.expiry_info["days"] if i.expiry_info else 9999,
            i.use_by_date or "",
        ),
    )[:25]

    compliance_rate = None
    if compliant_total:
        compliance_rate = round(100 * (1 - (noncompliant / compliant_total)))

    with Session(engine) as session:
        display_fields = get_display_field_defs(session)

    depleted_sorted = sorted(
        depleted_records,
        key=lambda r: r["depleted_date"],
        reverse=True,
    )
    depleted_count = len(depleted_sorted)
    depleted_avg_doh = None
    doh_vals = [r["days_on_hand"] for r in depleted_sorted if r["days_on_hand"] is not None]
    if doh_vals:
        depleted_avg_doh = round(sum(doh_vals) / len(doh_vals))
    depleted_recent = depleted_sorted[:25]

    depletion_reason_map: dict[str, list[dict]] = {}
    for rec in depleted_sorted:
        reason = rec["item"].depleted_reason or "Unspecified"
        depletion_reason_map.setdefault(reason, []).append(rec)
    depletion_reasons = sorted(
        depletion_reason_map.items(),
        key=lambda kv: len(kv[1]),
        reverse=True,
    )
    depletion_reason_max = max((len(v) for v in depletion_reason_map.values()), default=0)

    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "summary": summary,
            "expiring": expiring_sorted,
            "heatmap": heatmap,
            "aging": aging_buckets,
            "compliance_rate": compliance_rate,
            "horizon": horizon,
            "category": category,
            "location": location,
            "categories": sorted(category_counts.keys()),
            "locations": sorted(location_counts.keys()),
            "depleted_count": depleted_count,
            "depleted_avg_doh": depleted_avg_doh,
            "depleted_recent": depleted_recent,
            "depletion_reasons": depletion_reasons,
            "depletion_reason_max": depletion_reason_max,
            "depletion_reason_items": depletion_reason_map,
            "bucket_items": bucket_items,
            "total_items": total_items,
            "display_fields": display_fields,
        },
    )


def _resolve_photo_path(session: Session, item_id: int, prefer_photo_id: int | None = None):
    """Return (path, photo_id) for an item's photo.

    Prioritizes an explicitly requested photo id, otherwise returns the most
    recent photo file that still exists on disk before falling back to legacy
    `photo_path`.
    """
    photos = get_item_photos(session, item_id)

    if prefer_photo_id:
        for p in photos:
            if p.id == prefer_photo_id and os.path.isfile(p.path):
                return p.path, p.id

    # Prefer newest-to-oldest so we skip stale DB rows pointing at deleted files.
    for p in reversed(photos):
        if os.path.isfile(p.path):
            return p.path, p.id

    item = session.get(Item, item_id)
    if item and item.photo_path and os.path.isfile(item.photo_path):
        return item.photo_path, None
    return None, None


def _photo_response(item_id: int, path: str):
    exists = os.path.isfile(path)
    print(f"PHOTO: item {item_id} -> path='{path}' exists={exists}")
    if not exists:
        return Response(status_code=404)
    lower = path.lower()
    if lower.endswith(".png"):
        mt = "image/png"
    elif lower.endswith((".jpg", ".jpeg")):
        mt = "image/jpeg"
    else:
        mt = "application/octet-stream"
    return FileResponse(path, media_type=mt)


@app.get("/photo/{item_id}", name="photo")
def photo(item_id: int):
    """Serve the first stored photo for an item (legacy route)."""
    with Session(engine) as session:
        path, _pid = _resolve_photo_path(session, item_id)
        if not path:
            print(f"PHOTO: item {item_id} has no photo")
            return Response(status_code=404)
    return _photo_response(item_id, path)


@app.get("/photo/file/{photo_id}", name="photo_by_id")
def photo_by_id(photo_id: int):
    with Session(engine) as session:
        photo = session.get(ItemPhoto, photo_id)
        if not photo:
            return Response(status_code=404)
    return _photo_response(photo.item_id, photo.path)


@app.get("/export.csv")
def export_csv():
    import csv

    with Session(engine) as session:
        csv_bytes = _export_csv_bytes(session)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_export.csv"},
    )


# -----------------------------
# Label PNG routes (preview)
# -----------------------------
@app.get("/label/{item_id}.png", name="label_png")
def label_png_file(request: Request, item_id: int):
    """
    File-style PNG route, used by the "Direct label URL" link
    and anywhere we need a label preview image.

    Uses the *default* label preset.
    """
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            return Response(status_code=404)

        preset = get_default_preset(session)
        link = build_item_link(item, request=request)
        png = make_label_png(item, preset, link_override=link)

    return StreamingResponse(io.BytesIO(png), media_type="image/png")


@app.get("/designer", name="label_designer", response_class=HTMLResponse)
def label_designer(request: Request):
    """
    Print designer page.

    - Quick Labels (title + description, no DB item)
    - Item Label Presets (global, used when printing items)
    """
    quick_printed = request.query_params.get("quick_printed") == "1"
    quick_error = request.query_params.get("quick_error", "")

    with Session(engine) as session:
        presets = session.exec(select(LabelPreset).order_by(LabelPreset.name)).all()
        default_id = None
        for p in presets:
            if p.is_default:
                default_id = p.id
                break

    return templates.TemplateResponse(
        "designer.html",
        {
            "request": request,
            "quick_printed": quick_printed,
            "quick_error": quick_error,
            "presets": presets,
            "default_preset_id": default_id,
        },
    )


@app.post("/designer/preset/save", name="label_preset_save")
async def label_preset_save(
    request: Request,
    name: str = Form(...),
    media: str = Form("w79h252"),
    include_name: bool = Form(False),
    include_location: bool = Form(False),
    include_bin: bool = Form(False),
    include_qty_unit: bool = Form(False),
    include_condition: bool = Form(False),
    include_cook_date: bool = Form(False),
    include_use_by: bool = Form(False),
    include_use_within: bool = Form(False),
    include_qr: bool = Form(False),
    align_center: bool = Form(False),
    font_scale: float = Form(1.0),
    make_default: bool = Form(False),
    printer_side: str = Form("auto"),
):
    """
    Create a new global label preset.
    """
    printer_side = (printer_side or "auto").lower()
    if printer_side not in ("auto", "left", "right"):
        printer_side = "auto"

    with Session(engine) as session:
        preset = LabelPreset(
            name=name.strip() or "Preset",
            media=media.strip() or "w79h252",
            printer_side=printer_side,
            include_name=include_name,
            include_location=include_location,
            include_bin=include_bin,
            include_qty_unit=include_qty_unit,
            include_condition=include_condition,
            include_cook_date=include_cook_date,
            include_use_by=include_use_by,
            include_use_within=include_use_within,
            include_qr=include_qr,
            align_center=align_center,
            font_scale=font_scale or 1.0,
            is_default=False,
        )
        session.add(preset)
        session.commit()
        session.refresh(preset)

        if make_default:
            # clear default on others
            others = session.exec(
                select(LabelPreset).where(LabelPreset.id != preset.id)
            ).all()
            for o in others:
                o.is_default = False
            preset.is_default = True
            session.add(preset)
            session.commit()

    return RedirectResponse(
        url=str(request.url_for("label_designer")), status_code=303
    )


@app.post("/designer/preset/default", name="label_preset_default")
async def label_preset_default(
    request: Request,
    preset_id: int = Form(...),
):
    """
    Mark a preset as the global default for item printing.
    """
    with Session(engine) as session:
        preset = session.get(LabelPreset, preset_id)
        if preset:
            all_presets = session.exec(select(LabelPreset)).all()
            for p in all_presets:
                p.is_default = (p.id == preset.id)
            session.commit()

    return RedirectResponse(
        url=str(request.url_for("label_designer")), status_code=303
    )


@app.post("/designer/preset/delete", name="label_preset_delete")
async def label_preset_delete(
    request: Request,
    preset_id: int = Form(...),
):
    """
    Delete a preset. If it was default, pick another as default (if any).
    """
    with Session(engine) as session:
        preset = session.get(LabelPreset, preset_id)
        was_default = False
        if preset:
            was_default = preset.is_default
            session.delete(preset)
            session.commit()

        if was_default:
            # pick a new default if there is at least one preset left
            remaining = session.exec(select(LabelPreset)).all()
            if remaining:
                remaining[0].is_default = True
                session.add(remaining[0])
                session.commit()

    return RedirectResponse(
        url=str(request.url_for("label_designer")), status_code=303
    )


# --- Printing helpers -------------------------------------------------

# Default label size used today (based on lpoptions: *w79h252)
DEFAULT_MEDIA = "w79h252"


def _roll_for_media(media: str) -> str | None:
    """
    Decide which roll to use based on label size (CUPS media string).
    """
    m = (media or "").lower()

    # 1) Small address label (e.g. w79h252 / 30334-style) -> LEFT roll
    if m.startswith("w79h252") or "30334_2-1_4_in_x_1-1_4_in".lower() in m:
        return "Left"

    # 2) Larger label -> RIGHT roll
    if m.startswith("w154h64") or m.startswith("w154h198"):
        return "Right"

    # If we don't recognize the size, let the driver auto-select.
    return None


def _slot_for_preset(preset: LabelPreset | None, media: str) -> str | None:
    """Decide input slot honoring preset.printer_side, else infer from media."""
    if preset and getattr(preset, "printer_side", None):
        side = (preset.printer_side or "").lower()
        if side in ("left", "right"):
            return side.capitalize()
    return _roll_for_media(media)


def _normalize_copy_count(value) -> int:
    """Clamp requested copy count to a safe, positive range."""
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 1
    return max(1, min(MAX_LABEL_COPIES, count))


@app.get("/print/{item_id}", name="print_label_get")
def print_label_get(request: Request, item_id: int, copies: int = 1):
    # Simple GET: print and then redirect back to the item
    return _print_impl(
        request,
        item_id,
        prefer_redirect=True,
        copies=_normalize_copy_count(copies),
    )


@app.post("/print/{item_id}", name="print_label_post")
def print_label_post(
    request: Request,
    item_id: int,
    copies: int = Form(1),
):
    # POST (used from UI): print and then redirect back to the item
    return _print_impl(
        request,
        item_id,
        prefer_redirect=True,
        copies=_normalize_copy_count(copies),
    )


def _print_impl(
    request: Request,
    item_id: int,
    prefer_redirect: bool = False,
    media: str | None = None,
    copies: int = 1,
):
    """
    Core print implementation.
    """
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            if prefer_redirect:
                return RedirectResponse(
                    url=request.url_for("index"),
                    status_code=303,
                )
            return JSONResponse({"ok": False, "error": "Item not found"}, status_code=404)

        preset = get_default_preset(session)

    # If IPP not configured, fall back to label PNG preview
    if not IPP_HOST or not IPP_PRINTER:
        label_url = request.url_for("label_png", item_id=item_id)
        if prefer_redirect:
            return RedirectResponse(url=label_url, status_code=303)
        return JSONResponse(
            {
                "ok": False,
                "error": "IPP printer is not configured.",
                "label_url": str(label_url),
            },
            status_code=400,
        )

    link = build_item_link(item, request=request)
    base_img = make_label_image(item, preset, link_override=link)
    img_for_print = base_img.rotate(270, expand=True)

    buf = io.BytesIO()
    img_for_print.save(buf, format="PNG", dpi=(300, 300))
    png_bytes = buf.getvalue()

    with tempfile.NamedTemporaryFile(prefix="label_", suffix=".png", delete=False) as tmp:
        tmp.write(png_bytes)
        tmp_path = tmp.name

    media_opt = media or DEFAULT_MEDIA
    slot = _slot_for_preset(preset, media_opt)
    copies = _normalize_copy_count(copies)

    base_cmd = [
        "lp",
        "-h",
        IPP_HOST,
        "-d",
        IPP_PRINTER,
        "-o",
        f"media={media_opt}",
        "-o",
        "orientation-requested=3",
        "-o",
        "page-left=0",
        "-o",
        "page-right=0",
        "-o",
        "page-top=0",
        "-o",
        "page-bottom=0",
    ]
    if slot:
        base_cmd.extend(["-o", f"InputSlot={slot}"])

    file_args = [tmp_path] * copies
    cmd = [*base_cmd, *file_args]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    ok = proc.returncode == 0

    if prefer_redirect:
        base_url = request.url_for("show_item", item_id=item_id)
        if ok:
            return RedirectResponse(url=f"{base_url}?printed=1", status_code=303)
        else:
            return RedirectResponse(url=f"{base_url}?print_error=1", status_code=303)

    return JSONResponse(
        {
            "ok": ok,
            "cmd": " ".join(list(base_cmd) + ["<label_png>"] * copies),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        },
        status_code=200 if ok else 500,
    )


@app.post("/designer/quick/preview", name="quick_label_preview")
async def quick_label_preview(
    title: str = Form(""),
    description: str = Form(""),
):
    """
    Generate a PNG preview of a Quick Label (no printing).
    Used by the Print Designer preview button.
    """
    img = make_quick_label_image(title, description)
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(300, 300))
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.post("/designer/quick/print", name="quick_label_print")
async def quick_label_print(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
):
    """
    Print a one-off quick label that is NOT tied to an Item in the DB.
    """
    if not IPP_HOST or not IPP_PRINTER:
        img = make_quick_label_image(title, description)
        buf = io.BytesIO()
        img.save(buf, format="PNG", dpi=(300, 300))
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    base_img = make_quick_label_image(title, description)
    img_for_print = base_img.rotate(270, expand=True)

    buf = io.BytesIO()
    img_for_print.save(buf, format="PNG", dpi=(300, 300))
    png_bytes = buf.getvalue()

    media_opt = DEFAULT_MEDIA
    slot = _roll_for_media(media_opt)

    with tempfile.NamedTemporaryFile(prefix="quick_label_", suffix=".png", delete=False) as tmp:
        tmp.write(png_bytes)
        tmp_path = tmp.name

    cmd = [
        "lp",
        "-h",
        IPP_HOST,
        "-d",
        IPP_PRINTER,
        "-o",
        f"media={media_opt}",
        "-o",
        "orientation-requested=3",
        "-o",
        "page-left=0",
        "-o",
        "page-right=0",
        "-o",
        "page-top=0",
        "-o",
        "page-bottom=0",
    ]
    if slot:
        cmd.extend(["-o", f"InputSlot={slot}"])
    cmd.append(tmp_path)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    ok = proc.returncode == 0
    if ok:
        redirect_url = str(request.url_for("label_designer")) + "?quick_printed=1"
    else:
        err = (proc.stderr or "").strip().replace(" ", "+")
        redirect_url = str(request.url_for("label_designer")) + f"?quick_error={err}"

    return RedirectResponse(url=redirect_url, status_code=303)


# -------- Edit (modal) + Delete ----------
@app.get("/item/{item_id}/edit", name="edit_item_form", response_class=HTMLResponse)
def edit_item_form(request: Request, item_id: int, partial: int = 0):
    with Session(engine) as session:
        session.expire_on_commit = False  # keep item attached for template rendering
        item = _get_item_or_404(session, item_id)
        cats, bins, locations, use_withins = _choices(session)
        required_fields = get_required_field_keys(session)
        unit_names = get_unit_names(session)
        photos = get_item_photos(session, item_id, include_missing=True)
    ctx = {
        "request": request,
        "item": item,
        "cats": cats,
        "bins": bins,
        "locations": locations,
        "use_withins": use_withins,
        "units": unit_names,
        "required_fields": required_fields,
        "photos": photos,
        "error": "",
    }
    if partial:
        return templates.TemplateResponse("edit_form.html", ctx)
    return templates.TemplateResponse("show.html", ctx)


@app.post("/item/{item_id}/edit", name="edit_item_submit")
async def edit_item_submit(
    request: Request,
    item_id: int,
    name: str = Form(...),
    category: str = Form(""),
    tags: str = Form(""),
    location: str = Form(""),
    bin_number: str = Form(""),
    quantity: int = Form(1),
    unit: str = Form("each"),
    condition: str = Form(""),
    cook_date: str = Form(""),
    use_by_date: str = Form(""),
    use_within: str = Form(""),
    notes: str = Form(""),
    photos: List[UploadFile] = File([]),
):
    # Normalize for consistent comparisons and to avoid duplicate-case inserts
    name = _norm(name)
    category = _norm(category)
    tags = _norm(tags)
    location = _norm(location)
    bin_number = _norm(bin_number)
    unit = _norm(unit)
    condition = _norm(condition)
    cook_date = _norm(cook_date)
    use_by_date = _norm(use_by_date)
    use_within = _norm(use_within)
    notes = _norm(notes)

    with Session(engine) as session:
        item = _get_item_or_404(session, item_id)
        cats, bins, _locations, use_withins = _choices(session)
        unit_names = get_unit_names(session)
        required_fields = get_required_field_keys(session)

        def _missing_required() -> list[str]:
            missing: list[str] = []
            for key in required_fields:
                value = {
                    "name": name,
                    "category": category,
                    "tags": tags,
                    "location": location,
                    "bin_number": bin_number,
                    "quantity": quantity,
                    "unit": unit,
                    "condition": condition,
                    "cook_date": cook_date,
                    "use_by_date": use_by_date,
                    "use_within": use_within,
                    "notes": notes,
                }.get(key)

                if key == "quantity":
                    if value is None:
                        missing.append(key)
                    continue

                if value is None or (isinstance(value, str) and not value.strip()):
                    missing.append(key)
            return missing

        missing = _missing_required()
        if missing:
            label_list = [REQUIRED_FIELD_LABELS.get(k, k) for k in missing]
            msg = "Required fields: " + ", ".join(label_list)
            wants_json = (
                "application/json" in (request.headers.get("Accept", "") or "")
                or request.headers.get("X-Requested-With", "").lower() == "fetch"
            )
            if wants_json:
                return JSONResponse({"ok": False, "error": msg}, status_code=400)
            return templates.TemplateResponse(
                "edit_form.html",
                {
                    "request": request,
                    "item": item,
                    "cats": cats,
                    "bins": bins,
                    "locations": _locations,
                    "use_withins": use_withins,
                    "units": unit_names,
                    "required_fields": required_fields,
                    "error": msg,
                },
                status_code=400,
            )

        _upsert_name(session, Category, category)
        _upsert_name(session, Bin, bin_number)
        _upsert_name(session, Location, location)
        _upsert_name(session, UseWithin, use_within)

        item.name = name or "Unnamed Item"
        item.category = category or None
        item.tags = tags or None
        item.location = location or None
        item.bin_number = bin_number or None
        item.quantity = quantity
        item.unit = unit or None
        item.condition = condition or None
        item.cook_date = cook_date or None
        item.use_by_date = use_by_date or None
        item.use_within = use_within or None
        item.notes = notes or None
        session.add(item)
        session.commit()

        _save_item_photos(session, item, photos)

    wants_json = (
        "application/json" in (request.headers.get("Accept", "") or "")
        or request.headers.get("X-Requested-With", "").lower() == "fetch"
    )
    if wants_json:
        return JSONResponse({"ok": True, "item_id": item_id})
    return RedirectResponse(
        url=str(request.url_for("show_item", item_id=item_id)), status_code=303
    )


@app.post("/item/{item_id}/delete", name="delete_item")
def delete_item(request: Request, item_id: int):
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            return RedirectResponse(
                url=str(request.url_for("index")), status_code=303
            )
        # Delete all photos and records for this item
        photos = get_item_photos(session, item_id)
        for p in photos:
            _delete_photo_file(p.path)
            session.delete(p)
        try:
            if item.photo_path and os.path.isfile(item.photo_path):
                os.remove(item.photo_path)
        except Exception:
            pass
        session.delete(item)
        session.commit()
    wants_json = (
        "application/json" in (request.headers.get("Accept", "") or "")
        or request.headers.get("X-Requested-With", "").lower() == "fetch"
    )
    if wants_json:
        return JSONResponse({"ok": True})
    return RedirectResponse(
        url=str(request.url_for("index")), status_code=303
    )


@app.post("/photo/{photo_id}/delete", name="delete_photo")
def delete_photo(request: Request, photo_id: int):
    """Remove a specific photo from an item."""
    with Session(engine) as session:
        photo = session.get(ItemPhoto, photo_id)
        if not photo:
            return RedirectResponse(url=str(request.url_for("index")), status_code=303)
        item_id = photo.item_id
        item = session.get(Item, item_id)
        path = photo.path
        session.delete(photo)
        session.commit()

        _delete_photo_file(path)

        # If the item's primary path pointed to this photo, choose another
        if item and item.photo_path == path:
            remaining = get_item_photos(session, item.id)
            item.photo_path = remaining[0].path if remaining else None
            session.add(item)
            session.commit()

    wants_json = (
        "application/json" in (request.headers.get("Accept", "") or "")
        or request.headers.get("X-Requested-With", "").lower() == "fetch"
    )
    if wants_json:
        return JSONResponse({"ok": True, "item_id": item_id})
    return RedirectResponse(
        url=str(request.url_for("show_item", item_id=item_id)), status_code=303
    )


@app.post("/item/{item_id}/photos/delete-all", name="delete_all_photos")
def delete_all_photos(request: Request, item_id: int):
    """Remove every photo tied to an item (files + DB rows)."""
    with Session(engine) as session:
        item = session.get(Item, item_id)
        if not item:
            return RedirectResponse(url=str(request.url_for("index")), status_code=303)
        photos = get_item_photos(session, item_id)
        for p in photos:
            _delete_photo_file(p.path)
            session.delete(p)
        # Legacy path cleanup
        _delete_photo_file(item.photo_path or "")
        item.photo_path = None
        session.add(item)
        session.commit()

    wants_json = (
        "application/json" in (request.headers.get("Accept", "") or "")
        or request.headers.get("X-Requested-With", "").lower() == "fetch"
    )
    if wants_json:
        return JSONResponse({"ok": True, "item_id": item_id})
    return RedirectResponse(
        url=str(request.url_for("show_item", item_id=item_id)), status_code=303
    )


# -------- Duplicate item --------
@app.post("/item/{item_id}/duplicate", name="duplicate_item")
def duplicate_item(request: Request, item_id: int):
    """Create a new item by copying fields from an existing one, with a new serial."""
    with Session(engine) as session:
        original = session.get(Item, item_id)
        if not original:
            return RedirectResponse(
                url=str(request.url_for("index")), status_code=303
            )

        new_serial = next_serial(session)

        new_item = Item(
            serial_number=new_serial,
            name=original.name,
            category=original.category,
            tags=original.tags,
            location=original.location,
            bin_number=original.bin_number,
            quantity=original.quantity,
            unit=original.unit,
            barcode=new_serial,
            second_serial_number=None,
            condition=original.condition,
            cook_date=None,
            use_by_date=None,
            use_within=None,
            notes=original.notes,
            photo_path=None,
            last_audit_date=None,
            depleted_at=None,
            depleted_reason=None,
            depleted_qty=None,
        )

        session.add(new_item)
        session.commit()
        session.refresh(new_item)

    show_url = str(request.url_for("show_item", item_id=new_item.id))
    return RedirectResponse(f"{show_url}?auto_edit=1", status_code=303)


# -------- Admin (Categories, Bins, Locations, UseWithin) ------
@app.api_route(
    "/admin", methods=["GET", "POST"], name="admin", response_class=HTMLResponse
)
async def admin(request: Request, response: Response):
    form = await request.form() if request.method == "POST" else {}

    with Session(engine, expire_on_commit=False) as session:
        stored_hash = get_admin_password_hash(session)
        cookie_token = request.cookies.get("admin_auth", "")
        authed = cookie_token == stored_hash
        login_error = ""
        pass_error = ""
        pass_success = ""

        if request.method == "POST" and "admin_password_attempt" in form:
            attempt = (form.get("admin_password_attempt") or "").strip()
            if _hash_pw(attempt) == stored_hash:
                authed = True
            else:
                login_error = "Incorrect password"

        if request.method == "POST" and form.get("lock_admin") == "1":
            # Clear cookie and force re-auth
            resp = templates.TemplateResponse(
                "admin_login.html",
                {"request": request, "error": ""},
                status_code=200,
            )
            resp.delete_cookie("admin_auth", path="/")
            return resp

        if not authed:
            # If not authed, render login form only
            next_dest = request.query_params.get("next", "")
            return templates.TemplateResponse(
                "admin_login.html",
                {"request": request, "error": login_error, "next": next_dest},
                status_code=401 if login_error else 200,
            )

        if request.method == "POST":
            # We infer the action from which fields are present.
            if "new_category" in form:
                name = (form.get("new_category") or "").strip()
                if name and not session.exec(
                    select(Category).where(Category.name == name)
                ).first():
                    session.add(Category(name=name))
                    session.commit()
                    save_category_order(session, [c.id for c in get_categories_ordered(session)])

            elif "new_bin" in form:
                name = (form.get("new_bin") or "").strip()
                if name and not session.exec(
                    select(Bin).where(Bin.name == name)
                ).first():
                    session.add(Bin(name=name))
                    session.commit()
                    save_bin_order(session, [b.id for b in get_bins_ordered(session)])

            elif "new_location" in form:
                name = (form.get("new_location") or "").strip()
                if name and not session.exec(
                    select(Location).where(Location.name == name)
                ).first():
                    session.add(Location(name=name))
                    session.commit()
                    save_location_order(session, [l.id for l in get_locations_ordered(session)])

            elif "new_use_within" in form:
                name = (form.get("new_use_within") or "").strip()
                if name and not session.exec(
                    select(UseWithin).where(UseWithin.name == name)
                ).first():
                    session.add(UseWithin(name=name))
                    session.commit()
                    # ensure new entries appear at end by updating order
                    save_usewithin_order(
                        session, [u.id for u in get_use_withins_ordered(session)]
                    )
            elif "new_unit" in form:
                name = (form.get("new_unit") or "").strip()
                adjustable = bool(form.get("new_unit_adjustable"))
                if name and not session.exec(
                    select(UnitOption).where(func.lower(UnitOption.name) == name.lower())
                ).first():
                    session.add(UnitOption(name=name, adjustable=adjustable))
                    session.commit()
                    save_unit_order(session, [u.id for u in get_units_ordered(session)])

            elif "delete_category_id" in form:
                cid = form.get("delete_category_id")
                if cid:
                    cat = session.get(Category, int(cid))
                    if cat:
                        items = session.exec(
                            select(Item).where(Item.category == cat.name)
                        ).all()
                        for it in items:
                            it.category = None
                        session.delete(cat)
                        session.commit()
                        save_category_order(session, [c.id for c in get_categories_ordered(session)])

            elif "edit_category_id" in form:
                cid = form.get("edit_category_id")
                new_name = (form.get("edit_category_name") or "").strip()
                if cid and new_name:
                    cat = session.get(Category, int(cid))
                    exists = session.exec(
                        select(Category).where(Category.name == new_name)
                    ).first()
                    if cat and not exists:
                        old = cat.name
                        cat.name = new_name
                        session.add(cat)
                        # update items
                        items = session.exec(select(Item).where(Item.category == old)).all()
                        for it in items:
                            it.category = new_name
                        session.commit()
                        save_category_order(session, [c.id for c in get_categories_ordered(session)])

            elif "delete_bin_id" in form:
                bid = form.get("delete_bin_id")
                if bid:
                    b = session.get(Bin, int(bid))
                    if b:
                        items = session.exec(
                            select(Item).where(Item.bin_number == b.name)
                        ).all()
                        for it in items:
                            it.bin_number = None
                        session.delete(b)
                        session.commit()
                        save_bin_order(session, [b.id for b in get_bins_ordered(session)])

            elif "edit_bin_id" in form:
                bid = form.get("edit_bin_id")
                new_name = (form.get("edit_bin_name") or "").strip()
                if bid and new_name:
                    b = session.get(Bin, int(bid))
                    exists = session.exec(
                        select(Bin).where(Bin.name == new_name)
                    ).first()
                    if b and not exists:
                        old = b.name
                        b.name = new_name
                        session.add(b)
                        items = session.exec(select(Item).where(Item.bin_number == old)).all()
                        for it in items:
                            it.bin_number = new_name
                        session.commit()
                        save_bin_order(session, [b.id for b in get_bins_ordered(session)])

            elif "delete_location_id" in form:
                lid = form.get("delete_location_id")
                if lid:
                    loc = session.get(Location, int(lid))
                    if loc:
                        items = session.exec(
                            select(Item).where(Item.location == loc.name)
                        ).all()
                        for it in items:
                            it.location = None
                        session.delete(loc)
                        session.commit()
                        save_location_order(session, [l.id for l in get_locations_ordered(session)])

            elif "edit_location_id" in form:
                lid = form.get("edit_location_id")
                new_name = (form.get("edit_location_name") or "").strip()
                if lid and new_name:
                    loc = session.get(Location, int(lid))
                    exists = session.exec(
                        select(Location).where(Location.name == new_name)
                    ).first()
                    if loc and not exists:
                        old = loc.name
                        loc.name = new_name
                        session.add(loc)
                        items = session.exec(select(Item).where(Item.location == old)).all()
                        for it in items:
                            it.location = new_name
                        session.commit()
                        save_location_order(session, [l.id for l in get_locations_ordered(session)])

            elif "delete_use_within_id" in form:
                uid = form.get("delete_use_within_id")
                if uid:
                    uw = session.get(UseWithin, int(uid))
                    if uw:
                        items = session.exec(
                            select(Item).where(Item.use_within == uw.name)
                        ).all()
                        for it in items:
                            it.use_within = None
                        session.delete(uw)
                        session.commit()
                        # prune from order
                        remaining_ids = [u.id for u in get_use_withins_ordered(session) if u.id != uw.id]
                        save_usewithin_order(session, remaining_ids)

            elif "edit_use_within_id" in form:
                uid = form.get("edit_use_within_id")
                new_name = (form.get("edit_use_within_name") or "").strip()
                if uid and new_name:
                    uw = session.get(UseWithin, int(uid))
                    exists = session.exec(
                        select(UseWithin).where(UseWithin.name == new_name)
                    ).first()
                    if uw and not exists:
                        old = uw.name
                        uw.name = new_name
                        session.add(uw)
                        items = session.exec(select(Item).where(Item.use_within == old)).all()
                        for it in items:
                            it.use_within = new_name
                        session.commit()
            elif "delete_unit_id" in form:
                uid = form.get("delete_unit_id")
                if uid:
                    unit_obj = session.get(UnitOption, int(uid))
                    if unit_obj:
                        items = session.exec(
                            select(Item).where(Item.unit == unit_obj.name)
                        ).all()
                        for it in items:
                            it.unit = None
                        session.delete(unit_obj)
                        session.commit()
                        save_unit_order(session, [u.id for u in get_units_ordered(session)])

            elif "edit_unit_id" in form:
                uid = form.get("edit_unit_id")
                new_name = (form.get("edit_unit_name") or "").strip()
                if uid and new_name:
                    unit_obj = session.get(UnitOption, int(uid))
                    exists = session.exec(
                        select(UnitOption).where(func.lower(UnitOption.name) == new_name.lower())
                    ).first()
                    if unit_obj and not exists:
                        old = unit_obj.name
                        unit_obj.name = new_name
                        session.add(unit_obj)
                        items = session.exec(select(Item).where(Item.unit == old)).all()
                        for it in items:
                            it.unit = new_name
                        session.commit()

            elif form.get("toggle_unit_id"):
                uid = form.get("toggle_unit_id")
                try:
                    unit_obj = session.get(UnitOption, int(uid))
                except Exception:
                    unit_obj = None
                if unit_obj:
                    value = form.get("unit_adjustable")
                    unit_obj.adjustable = value not in (None, "", "0", "false", "False")
                    session.add(unit_obj)
                    session.commit()

            elif form.get("display_fields_action") == "save":
                # Order comes as comma-separated keys; we only keep checked ones, in order.
                order_str = form.get("display_fields_order", "")
                ordered = [k for k in order_str.split(",") if k]
                checked = set(form.getlist("display_fields"))
                if ordered:
                    chosen = [k for k in ordered if k in checked]
                    # include any checked not in order at the end
                    for k in checked:
                        if k not in chosen:
                            chosen.append(k)
                else:
                    chosen = list(checked)
                save_display_field_keys(session, chosen)

            elif form.get("required_fields_action") == "save":
                chosen = form.getlist("required_fields")
                save_required_field_keys(session, list(chosen))

            elif form.get("theme_action") == "save":
                theme = form.get("theme") or THEME_DEFAULT
                save_theme(session, theme)

            elif form.get("usewithin_order_action") == "save":
                order_str = form.get("usewithin_order", "")
                try:
                    ids = [int(x) for x in order_str.split(",") if x]
                except Exception:
                    ids = []
                save_usewithin_order(session, ids)

            elif form.get("category_order_action") == "save":
                ids = [int(x) for x in (form.get("category_order", "") or "").split(",") if x]
                save_category_order(session, ids)

            elif form.get("bin_order_action") == "save":
                ids = [int(x) for x in (form.get("bin_order", "") or "").split(",") if x]
                save_bin_order(session, ids)

            elif form.get("location_order_action") == "save":
                ids = [int(x) for x in (form.get("location_order", "") or "").split(",") if x]
                save_location_order(session, ids)
            elif form.get("unit_order_action") == "save":
                ids = [int(x) for x in (form.get("unit_order", "") or "").split(",") if x]
                save_unit_order(session, ids)

            elif form.get("app_heading_action") == "save":
                heading = (form.get("app_heading_value") or "").strip()
                save_app_heading(session, heading)
            elif form.get("change_admin_password") == "1":
                current = (form.get("current_password") or "").strip()
                new1 = (form.get("new_password") or "").strip()
                new2 = (form.get("new_password2") or "").strip()
                if _hash_pw(current) != stored_hash:
                    pass_error = "Current password is incorrect."
                elif not new1 or not new2:
                    pass_error = "New password cannot be empty."
                elif new1 != new2:
                    pass_error = "New passwords do not match."
                else:
                    set_admin_password(session, new1)
                    stored_hash = get_admin_password_hash(session)
                    cookie_token = stored_hash
                    authed = True
                    pass_success = "Password updated."

        cats = get_categories_ordered(session)
        bins = get_bins_ordered(session)
        locations = get_locations_ordered(session)
        use_withins = get_use_withins_ordered(session)
        units = get_units_ordered(session)
        app_heading = get_app_heading(session)
        selected_display_fields = get_display_field_keys(session)
        display_fields_defs = DISPLAYABLE_FIELDS
        required_field_defs = REQUIRED_FIELD_OPTIONS
        selected_required_fields = get_required_field_keys(session)
        current_theme = get_theme(session)
        health = {
            "ipp_status": check_ipp_status(),
            "disk": get_disk_usage(DATA_DIR),
            "item_count": session.exec(select(func.count()).select_from(Item)).one(),
        }

    resp = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "cats": cats,
            "bins": bins,
            "locations": locations,
            "use_withins": use_withins,
            "units": units,
            "display_fields_defs": display_fields_defs,
            "selected_display_fields": selected_display_fields,
            "required_field_defs": required_field_defs,
            "selected_required_fields": selected_required_fields,
            "current_theme": current_theme,
            "health": health,
            "app_heading": app_heading,
            "pass_error": pass_error,
            "pass_success": pass_success,
        },
    )
    if authed:
        # Use root path "/" so ingress and direct accesses share the cookie
        resp.set_cookie("admin_auth", stored_hash, path="/", httponly=True)
        next_dest = request.query_params.get("next", "")
        if next_dest:
            # Map legacy/short names to actual route names
            if next_dest == "backup":
                next_dest = "backup_page"
            return RedirectResponse(
                url=str(request.url_for(next_dest)),
                status_code=303,
            )
    return resp


# -------- Assets (CSS) --------
@app.get("/assets/styles.css", include_in_schema=False)
def serve_styles_css():
    css_path = os.path.join(STATIC_DIR, "styles.css")
    exists = os.path.isfile(css_path)
    print(f"DEBUG CSS route hit: path={css_path} exists={exists}")

    if not exists:
        return Response(
            f"CSS file not found on server. Expected at: {css_path}",
            status_code=404,
            media_type="text/plain",
        )

    resp = FileResponse(css_path, media_type="text/css")
    # Encourage caching but allow busting via version param in link
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.get("/assets/icon.png", include_in_schema=False)
def serve_icon_png():
    icon_path = os.path.join(STATIC_DIR, "icon.png")
    if not os.path.isfile(icon_path):
        return Response(status_code=404)
    resp = FileResponse(icon_path, media_type="image/png")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.get("/assets/icon.svg", include_in_schema=False)
def serve_icon_svg():
    icon_path = os.path.join(STATIC_DIR, "icon.svg")
    if not os.path.isfile(icon_path):
        return Response(status_code=404)
    resp = FileResponse(icon_path, media_type="image/svg+xml")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


# -------- Utilities --------
@app.get("/health")
def health():
    return JSONResponse({"status": "ok", "version": APP_VERSION})


@app.get("/whoami")
def whoami(request: Request):
    # Admin-only debug endpoint; require admin cookie
    with Session(engine) as session:
        stored_hash = get_admin_password_hash(session)
        cookie_token = request.cookies.get("admin_auth", "")
        if cookie_token != stored_hash:
            return RedirectResponse(
                url=str(request.url_for("admin")) + "?next=whoami",
                status_code=303,
            )
    return JSONResponse(
        {
            "path": request.url.path,
            "query": request.url.query,
            "root_path": request.scope.get("root_path", ""),
            "x-ingress-path": request.headers.get("x-ingress-path"),
            "x-forwarded-prefix": request.headers.get("x-forwarded-prefix"),
            "version": APP_VERSION,
        }
    )


@app.get("/{_catch:path}", response_class=HTMLResponse)
def catchall(_catch: str, request: Request):
    print(f"DEBUG catchall hit: _catch={_catch}")

    if _catch.startswith(
        ("static/", "assets/", "label/", "photo/", "health", "whoami", "item/")
    ):
        return Response(status_code=404)

    return RedirectResponse(url=str(request.url_for("index")), status_code=307)
