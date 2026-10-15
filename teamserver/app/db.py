import datetime
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_NAME = Path(__file__).resolve().parent.parent / "chimera_c2.db"


def utc_now() -> str:
    """Return the current UTC timestamp formatted as ISO 8601 string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    """Establish and return an active SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initialize SQLite database tables and apply automatic migrations
    to ensure schema alignment with all extended telemetry fields.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            hostname TEXT,
            os TEXT,
            user TEXT,
            ip TEXT,
            is_privileged INTEGER DEFAULT 0,
            last_seen TIMESTAMP,
            os_release TEXT DEFAULT 'Unknown',
            cpu_cores INTEGER DEFAULT 1,
            total_ram_gb REAL DEFAULT 0.0,
            available_ram_gb REAL DEFAULT 0.0,
            sample_processes TEXT DEFAULT '[]'
        )
        """
    )

    # Schema migration: ensure all extended telemetry columns exist in existing databases
    cur.execute("PRAGMA table_info(agents)")
    existing_cols = {row["name"] for row in cur.fetchall()}
    telemetry_columns = {
        "os_release": "TEXT DEFAULT 'Unknown'",
        "cpu_cores": "INTEGER DEFAULT 1",
        "total_ram_gb": "REAL DEFAULT 0.0",
        "available_ram_gb": "REAL DEFAULT 0.0",
        "sample_processes": "TEXT DEFAULT '[]'",
    }
    for col_name, col_def in telemetry_columns.items():
        if col_name not in existing_cols:
            cur.execute(f"ALTER TABLE agents ADD COLUMN {col_name} {col_def}")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            command TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            output TEXT DEFAULT '',
            exit_code INTEGER DEFAULT -1,
            created_at TIMESTAMP,
            completed_at TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            agent_id TEXT,
            task_id TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def add_audit_log(
    event_type: str,
    message: str,
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> None:
    """Record an audit event into persistent storage."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO audit_logs (
            event_type,
            agent_id,
            task_id,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event_type,
            agent_id,
            task_id,
            message,
            utc_now(),
        ),
    )

    conn.commit()
    conn.close()


def get_audit_logs(
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Query audit logs filtered by agent_id or task_id with limit."""
    conn = get_connection()
    cur = conn.cursor()

    if agent_id and task_id:
        cur.execute(
            """
            SELECT *
            FROM audit_logs
            WHERE agent_id = ?
              AND task_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (agent_id, task_id, limit),
        )
    elif agent_id:
        cur.execute(
            """
            SELECT *
            FROM audit_logs
            WHERE agent_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (agent_id, limit),
        )
    elif task_id:
        cur.execute(
            """
            SELECT *
            FROM audit_logs
            WHERE task_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (task_id, limit),
        )
    else:
        cur.execute(
            """
            SELECT *
            FROM audit_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def upsert_agent(agent_data: Dict[str, Any]) -> None:
    """
    Insert or update an agent record in SQLite.
    Persists core identity and extended hardware/OS telemetry.
    Uses COALESCE on conflict so heartbeat updates do not overwrite
    existing telemetry with null/default values.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Format sample_processes safely as JSON string
    raw_procs = agent_data.get("sample_processes")
    if isinstance(raw_procs, (list, dict)):
        sample_procs_json = json.dumps(raw_procs)
    elif isinstance(raw_procs, str):
        sample_procs_json = raw_procs
    else:
        sample_procs_json = None

    cur.execute(
        """
        INSERT INTO agents (
            agent_id,
            hostname,
            os,
            user,
            ip,
            is_privileged,
            last_seen,
            os_release,
            cpu_cores,
            total_ram_gb,
            available_ram_gb,
            sample_processes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(agent_id) DO UPDATE SET
            hostname = COALESCE(excluded.hostname, agents.hostname),
            os = COALESCE(excluded.os, agents.os),
            user = COALESCE(excluded.user, agents.user),
            ip = COALESCE(excluded.ip, agents.ip),
            is_privileged = COALESCE(excluded.is_privileged, agents.is_privileged),
            last_seen = excluded.last_seen,
            os_release = COALESCE(excluded.os_release, agents.os_release),
            cpu_cores = COALESCE(excluded.cpu_cores, agents.cpu_cores),
            total_ram_gb = COALESCE(excluded.total_ram_gb, agents.total_ram_gb),
            available_ram_gb = COALESCE(excluded.available_ram_gb, agents.available_ram_gb),
            sample_processes = COALESCE(excluded.sample_processes, agents.sample_processes)
        """,
        (
            agent_data["agent_id"],
            agent_data.get("hostname"),
            agent_data.get("os"),
            agent_data.get("user"),
            agent_data.get("ip"),
            1 if agent_data.get("is_privileged") else (0 if "is_privileged" in agent_data else None),
            agent_data.get("last_seen", utc_now()),
            agent_data.get("os_release"),
            agent_data.get("cpu_cores"),
            agent_data.get("total_ram_gb"),
            agent_data.get("available_ram_gb"),
            sample_procs_json,
        ),
    )

    conn.commit()
    conn.close()


def _format_agent_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Helper to deserialize sample_processes and convert privilege flags."""
    agent_dict = dict(row)
    raw_procs = agent_dict.get("sample_processes")
    if isinstance(raw_procs, str):
        try:
            agent_dict["sample_processes"] = json.loads(raw_procs)
        except Exception:
            agent_dict["sample_processes"] = []
    elif raw_procs is None:
        agent_dict["sample_processes"] = []

    agent_dict["is_privileged"] = bool(agent_dict.get("is_privileged", 0))
    return agent_dict


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single agent by ID from SQLite with parsed JSON fields."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM agents
        WHERE agent_id = ?
        """,
        (agent_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return _format_agent_row(row)


def get_all_agents() -> List[Dict[str, Any]]:
    """Retrieve all registered agents from SQLite with parsed JSON telemetry."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM agents
        ORDER BY last_seen DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [_format_agent_row(row) for row in rows]


def create_task(task_id: str, agent_id: str, command: str) -> None:
    """Insert a new pending task into persistent storage."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tasks (
            task_id,
            agent_id,
            command,
            status,
            output,
            exit_code,
            created_at,
            completed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            agent_id,
            command,
            "PENDING",
            "",
            -1,
            utc_now(),
            None,
        ),
    )

    conn.commit()
    conn.close()


def mark_task_running(task_id: str) -> None:
    """Transition task status to RUNNING."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE tasks
        SET status = ?
        WHERE task_id = ?
        """,
        ("RUNNING", task_id),
    )

    conn.commit()
    conn.close()


def complete_task(task_id: str, output: str, exit_code: int) -> None:
    """Record execution completion and update task outcome."""
    conn = get_connection()
    cur = conn.cursor()

    status = "COMPLETED" if exit_code == 0 else "FAILED"

    cur.execute(
        """
        UPDATE tasks
        SET
            status = ?,
            output = ?,
            exit_code = ?,
            completed_at = ?
        WHERE task_id = ?
        """,
        (
            status,
            output,
            exit_code,
            utc_now(),
            task_id,
        ),
    )

    conn.commit()
    conn.close()


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve task details by task ID."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM tasks
        WHERE task_id = ?
        """,
        (task_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def get_pending_tasks() -> List[Dict[str, Any]]:
    """Retrieve all tasks in PENDING status ordered by creation timestamp."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT task_id, agent_id, command
        FROM tasks
        WHERE status = 'PENDING'
        ORDER BY created_at ASC
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_tasks_for_agent(agent_id: str) -> List[Dict[str, Any]]:
    """Retrieve all tasks associated with a given agent ID."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM tasks
        WHERE agent_id = ?
        ORDER BY created_at ASC
        """,
        (agent_id,),
    )
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]