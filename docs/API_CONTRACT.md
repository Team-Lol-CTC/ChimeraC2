# ChimeraC2 API Data Contract & Specification

This document defines the formal communication standards and payload contracts between the ChimeraC2 Agent, Central Teamserver, and Mission Control Dashboard.

---

## 1. Agent Registration
* **Endpoint:** `POST /api/v1/beacon/register`
* **Description:** Initial agent check-in containing host reconnaissance and hardware telemetry.
* **Headers:** `Content-Type: application/json`, realistic browser `User-Agent`.
* **Payload Schema:**
```json
{
  "agent_id": "8-char-uuid",
  "hostname": "target-host",
  "os": "Linux / Windows",
  "os_release": "6.1.0-28-amd64",
  "user": "root / user",
  "ip": "192.168.1.50",
  "cpu_cores": 4,
  "total_ram_gb": 16.0,
  "available_ram_gb": 11.2,
  "is_privileged": true,
  "sample_processes": [
    {"pid": 1, "name": "systemd"},
    {"pid": 412, "name": "sshd"}
  ]
}
```
* **Response (200 OK):**
```json
{
  "status": "registered",
  "agent_id": "8-char-uuid"
}
```

---

## 2. Task Polling / Beacon
* **Endpoint:** `POST /api/v1/beacon/poll`
* **Description:** Periodic heartbeat polling for queued commands.
* **Payload Schema:**
```json
{
  "agent_id": "8-char-uuid"
}
```
* **Response (200 OK):**
```json
{
  "task": {
    "task_id": "task-abc123",
    "command": "whoami"
  }
}
```
*If no task is queued:*
```json
{
  "task": null
}
```
*If agent is unrecognized (e.g., after server restart):*
```json
{
  "task": null,
  "error": "unknown agent_id"
}
```

---

## 3. Task Results
* **Endpoint:** `POST /api/v1/beacon/result`
* **Description:** Submits command execution output (Base64 encoded) and returncode.
* **Payload Schema:**
```json
{
  "task_id": "task-abc123",
  "agent_id": "8-char-uuid",
  "output": "cm9vdAo=",
  "exit_code": 0
}
```
* **Response (200 OK):**
```json
{
  "status": "accepted"
}
```

---

## 4. Operator WebSocket Dispatcher
* **Endpoint:** `WS /ws/operator`
* **Description:** Real-time bi-directional channel for operator command dispatch and live execution streaming.
* **Client Command Dispatch:**
```json
{
  "action": "exec",
  "agent_id": "8-char-uuid",
  "command": "whoami"
}
```
* **Server Broadcast Events:**
  - `AGENT_REGISTER`: Broadcast when an agent registers or reconnects.
  - `AGENT_HEARTBEAT`: Sent on each successful beacon poll.
  - `AGENT_DISCONNECT`: Sent when an agent exceeds the inactivity timeout.
  - `TASK_QUEUED`: Dispatched when an operator queues a command.
  - `TASK_RESULT`: Dispatched when an agent posts execution results.

---

## 5. History & Audit REST Endpoints
* **Task History:** `GET /api/v1/tasks?agent_id=<id>`
* **Audit Logs:** `GET /api/v1/audit?agent_id=<id>&task_id=<task>&limit=100`
* **Health Check:** `GET /health`