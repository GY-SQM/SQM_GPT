import sqlite3

from backend.api.status_revert_api import (
    execute_status_revert,
    preview_status_revert,
)


def _db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE inventory (
            lot_no TEXT PRIMARY KEY,
            status TEXT,
            container_no TEXT,
            bl_no TEXT,
            inbound_date TEXT,
            sold_to TEXT,
            sale_ref TEXT,
            updated_at TEXT
        );
        CREATE TABLE inventory_tonbag (
            id INTEGER PRIMARY KEY,
            lot_no TEXT,
            status TEXT,
            container_no TEXT,
            bl_no TEXT,
            inbound_date TEXT,
            sale_ref TEXT,
            picked_to TEXT,
            pick_ref TEXT,
            weight REAL,
            updated_at TEXT
        );
        CREATE TABLE allocation_plan (
            id INTEGER PRIMARY KEY,
            lot_no TEXT,
            status TEXT,
            customer TEXT,
            sale_ref TEXT,
            picking_no TEXT,
            bl_no TEXT,
            cancelled_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE sold_table (
            id INTEGER PRIMARY KEY,
            lot_no TEXT,
            status TEXT,
            customer TEXT,
            sales_order_no TEXT,
            picking_no TEXT,
            bl_no TEXT,
            sold_date TEXT
        );
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY,
            event_type TEXT,
            event_data TEXT,
            user_note TEXT,
            created_by TEXT,
            created_at TEXT
        );
        """
    )
    return con


def _seed(con):
    con.executemany(
        "INSERT INTO inventory(lot_no,status,container_no,bl_no,inbound_date,sold_to,sale_ref) VALUES (?,?,?,?,?,?,?)",
        [
            ("LOT-A", "PICKED", "CONT-1", "BL-1", "2026-05-01", "Buyer", "SO-1"),
            ("LOT-B", "PICKED", "CONT-1", "BL-1", "2026-05-02", "Buyer", "SO-1"),
            ("LOT-C", "PICKED", "CONT-2", "BL-2", "2026-05-01", "Other", "SO-2"),
        ],
    )
    con.executemany(
        "INSERT INTO inventory_tonbag(lot_no,status,container_no,bl_no,inbound_date,sale_ref,picked_to,pick_ref,weight) VALUES (?,?,?,?,?,?,?,?,?)",
        [
            ("LOT-A", "PICKED", "CONT-1", "BL-1", "2026-05-01", "SO-1", "Buyer", "PK-1", 1000),
            ("LOT-A", "PICKED", "CONT-1", "BL-1", "2026-05-01", "SO-1", "Buyer", "PK-1", 1000),
            ("LOT-B", "PICKED", "CONT-1", "BL-1", "2026-05-02", "SO-1", "Buyer", "PK-1", 1000),
            ("LOT-C", "PICKED", "CONT-2", "BL-2", "2026-05-01", "SO-2", "Other", "PK-2", 1000),
        ],
    )
    con.executemany(
        "INSERT INTO allocation_plan(lot_no,status,customer,sale_ref,picking_no,bl_no) VALUES (?,?,?,?,?,?)",
        [
            ("LOT-A", "PICKED", "Buyer", "SO-1", "PK-1", "BL-1"),
            ("LOT-B", "PICKED", "Buyer", "SO-1", "PK-1", "BL-1"),
            ("LOT-C", "PICKED", "Other", "SO-2", "PK-2", "BL-2"),
        ],
    )
    con.commit()


def test_preview_uses_container_as_primary_scope_and_inbound_date_as_optional_filter():
    con = _db()
    _seed(con)

    result = preview_status_revert(
        con,
        {
            "from_status": "PICKED",
            "to_status": "RESERVED",
            "scope_type": "container_no",
            "scope_value": "CONT-1",
            "filters": {"inbound_date": "2026-05-01"},
        },
    )

    assert result["ok"] is True
    assert result["target_lot_count"] == 1
    assert result["target_tonbag_count"] == 2
    assert result["target_weight_mt"] == 2.0
    assert result["lots"] == ["LOT-A"]


def test_execute_reverts_only_resolved_lots_and_writes_audit_log():
    con = _db()
    _seed(con)

    result = execute_status_revert(
        con,
        {
            "from_status": "PICKED",
            "to_status": "RESERVED",
            "scope_type": "bl_no",
            "scope_value": "BL-1",
            "filters": {"lot_nos": ["LOT-B"]},
        },
    )

    assert result["ok"] is True
    assert result["data"]["lots"] == ["LOT-B"]
    assert con.execute("SELECT status FROM inventory WHERE lot_no='LOT-B'").fetchone()[0] == "RESERVED"
    assert con.execute("SELECT status FROM inventory_tonbag WHERE lot_no='LOT-B'").fetchone()[0] == "RESERVED"
    assert con.execute("SELECT status FROM inventory WHERE lot_no='LOT-A'").fetchone()[0] == "PICKED"
    assert con.execute("SELECT COUNT(*) FROM audit_log WHERE event_type='STATUS_REVERT'").fetchone()[0] == 1
