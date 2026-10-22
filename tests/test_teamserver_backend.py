import base64
import os
import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from teamserver.app.main import app, connected_agents, task_queues, rehydrate_state
import teamserver.app.db as db


def run_tests():
    print("[*] Starting backend integration tests...")

    # Initialize fresh in-memory or temporary DB
    db.init_db()
    client = TestClient(app)

    # ---------------------------------------------------------
    # Deliverable 1: Schema Validation via Pydantic
    # ---------------------------------------------------------
    print("\n--- Testing Deliverable 1: Pydantic Validation ---")

    # 1.1: Missing required fields in register (expect 422)
    bad_register_payload = {
        "hostname": "test-box",
        "os": "Linux"
        # missing agent_id, user, ip
    }
    resp = client.post("/api/v1/beacon/register", json=bad_register_payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    print("[+] 422 properly returned for malformed register payload.")

    # 1.2: Valid registration with extended telemetry
    agent_id = "agent-t1"
    valid_register_payload = {
        "agent_id": agent_id,
        "hostname": "alpha-box",
        "os": "Linux",
        "os_release": "6.1.0-custom",
        "user": "root",
        "ip": "10.0.0.50",
        "is_privileged": True,
        "cpu_cores": 8,
        "total_ram_gb": 32.0,
        "available_ram_gb": 24.5,
        "sample_processes": [{"pid": 1, "name": "init"}, {"pid": 200, "name": "sshd"}]
    }
    resp = client.post("/api/v1/beacon/register", json=valid_register_payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    assert resp.json()["status"] == "registered"
    print("[+] 200 OK returned for valid register payload with telemetry.")

    # 1.3: Missing required agent_id in poll (expect 422)
    resp = client.post("/api/v1/beacon/poll", json={})
    assert resp.status_code == 422, f"Expected 422 for poll, got {resp.status_code}"
    print("[+] 422 properly returned for malformed poll payload.")

    # 1.4: Valid poll for registered agent
    resp = client.post("/api/v1/beacon/poll", json={"agent_id": agent_id})
    assert resp.status_code == 200
    assert resp.json()["task"] is None
    print("[+] 200 OK returned for valid poll request.")

    # 1.5: Missing fields in task result (expect 422)
    resp = client.post("/api/v1/beacon/result", json={"agent_id": agent_id})
    assert resp.status_code == 422
    print("[+] 422 properly returned for malformed task result payload.")

    # ---------------------------------------------------------
    # Deliverable 2: Persistence Alignment & Telemetry in SQLite
    # ---------------------------------------------------------
    print("\n--- Testing Deliverable 2: SQLite Schema & Telemetry Persistence ---")

    persisted_agent = db.get_agent(agent_id)
    assert persisted_agent is not None, "Agent was not saved to SQLite!"
    assert persisted_agent["os_release"] == "6.1.0-custom", f"Unexpected os_release: {persisted_agent['os_release']}"
    assert persisted_agent["cpu_cores"] == 8, f"Unexpected cpu_cores: {persisted_agent['cpu_cores']}"
    assert persisted_agent["total_ram_gb"] == 32.0, f"Unexpected total_ram_gb: {persisted_agent['total_ram_gb']}"
    assert persisted_agent["available_ram_gb"] == 24.5, f"Unexpected available_ram_gb: {persisted_agent['available_ram_gb']}"
    assert persisted_agent["is_privileged"] is True, f"Unexpected is_privileged: {persisted_agent['is_privileged']}"
    assert len(persisted_agent["sample_processes"]) == 2, f"Unexpected sample_processes: {persisted_agent['sample_processes']}"
    print("[+] Full extended telemetry successfully retrieved from SQLite.")

    # Verify that heartbeat upsert does not overwrite telemetry with nulls
    heartbeat_update = {
        "agent_id": agent_id,
        "last_seen": db.utc_now(),
        "status": "online"
    }
    db.upsert_agent(heartbeat_update)
    persisted_after_hb = db.get_agent(agent_id)
    assert persisted_after_hb["cpu_cores"] == 8, "COALESCE failed: cpu_cores was overwritten!"
    assert persisted_after_hb["total_ram_gb"] == 32.0, "COALESCE failed: total_ram_gb was overwritten!"
    print("[+] COALESCE upsert verified: heartbeat update preserved telemetry fields.")

    # ---------------------------------------------------------
    # Deliverable 3: In-Memory State Rehydration on Startup
    # ---------------------------------------------------------
    print("\n--- Testing Deliverable 3: Startup In-Memory Rehydration ---")

    # Queue a task directly in SQLite
    import uuid
    task_id = f"task-rehydrate-{uuid.uuid4().hex[:8]}"
    db.create_task(task_id, agent_id, "whoami /priv")

    # Simulate server reboot by wiping in-memory state
    connected_agents.clear()
    task_queues.clear()
    assert len(connected_agents) == 0
    assert len(task_queues) == 0
    print("[*] In-memory state cleared (simulating server crash/reboot).")

    # Run rehydration routine
    rehydrate_state()

    assert agent_id in connected_agents, "Agent not rehydrated into connected_agents!"
    assert agent_id in task_queues, "Agent task queue not initialized in rehydration!"
    assert len(task_queues[agent_id]) == 1, f"Pending task not restored to queue! Queue: {task_queues[agent_id]}"
    assert task_queues[agent_id][0]["task_id"] == task_id
    assert task_queues[agent_id][0]["command"] == "whoami /priv"
    print("[+] Rehydration verified: agent and pending task restored from SQLite.")

    # Poll after reboot: should seamlessly receive the restored task
    resp = client.post("/api/v1/beacon/poll", json={"agent_id": agent_id})
    assert resp.status_code == 200
    task_received = resp.json().get("task")
    assert task_received is not None, "Task was not delivered after reboot!"
    assert task_received["task_id"] == task_id
    print(f"[+] Agent polled and received restored task [{task_id}] after server reboot!")

    # ---------------------------------------------------------
    # Deliverable: Base64 Task Result Processing
    # ---------------------------------------------------------
    print("\n--- Testing Task Result & Base64 Decoding ---")
    raw_output = "root\nSeDebugPrivilege Enabled"
    encoded_output = base64.b64encode(raw_output.encode("utf-8")).decode("utf-8")

    result_payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "output": encoded_output,
        "exit_code": 0
    }
    resp = client.post("/api/v1/beacon/result", json=result_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    completed_task = db.get_task(task_id)
    assert completed_task["status"] == "COMPLETED"
    assert completed_task["output"] == raw_output, f"Expected decoded output, got: {completed_task['output']}"
    assert completed_task["exit_code"] == 0
    print("[+] Task result Base64 decoded and persisted as COMPLETED in SQLite.")

    print("\n==============================================")
    print(">>> ALL BACKEND DELIVERABLES PASSED 100%! <<<")
    print("==============================================")


if __name__ == "__main__":
    run_tests()
