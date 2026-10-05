import sqlite3
import datetime
from pathlib import Path

DB_NAME = Path(__file__).resolve().parent.parent / "chimera_c2.db"


def utc_now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
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
            is_privileged INTEGER,
            last_seen TIMESTAMP
        )
        """
    )

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
    agent_id: str | None = None,
    task_id: str | None = None,
):
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
    agent_id: str | None = None,
    task_id: str | None = None,
    limit: int = 100,
):
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


def upsert_agent(agent_data: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO agents (
            agent_id,
            hostname,
            os,
            user,
            ip,
            is_privileged,
            last_seen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(agent_id) DO UPDATE SET
            hostname = excluded.hostname,
            os = excluded.os,
            user = excluded.user,
            ip = excluded.ip,
            is_privileged = excluded.is_privileged,
            last_seen = excluded.last_seen
        """,
        (
            agent_data["agent_id"],
            agent_data.get("hostname", "Unknown"),
            agent_data.get("os", "Unknown"),
            agent_data.get("user", "Unknown"),
            agent_data.get("ip", "Unknown"),
            1 if agent_data.get("is_privileged") else 0,
            agent_data.get("last_seen", utc_now()),
        ),
    )

    conn.commit()
    conn.close()


def create_task(task_id: str, agent_id: str, command: str):
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


def mark_task_running(task_id: str):
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


def complete_task(task_id: str, output: str, exit_code: int):
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


def get_task(task_id: str):
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


def get_tasks_for_agent(agent_id: str):
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