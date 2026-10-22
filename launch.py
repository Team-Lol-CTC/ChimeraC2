#!/usr/bin/env python3
"""
ChimeraC2 — Cross-Platform Interactive Operator & Developer Launcher

Provides an interactive console interface to configure, launch, and package:
  [1] Start Control Plane (FastAPI Teamserver)
  [2] Start Operator Dashboard (React Mission Control)
  [3] Run Local Worker Node (agent/agent.py)
  [4] Export Standalone Worker Bundle (dist_worker/ & dist_worker.zip)
  [5] Launch Containerized Lab (docker compose)
  [6] Run Automated Verification Suite (pytest & ESLint)
  [7] Exit

Written in pure Python using only standard library modules.
"""

import os
import pathlib
import platform
import shutil
import socket
import subprocess
import sys
import time

# Ensure UTF-8 output encoding on Windows if supported
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Resolve project root relative to this script
ROOT_DIR = pathlib.Path(__file__).resolve().parent
TEAMSERVER_DIR = ROOT_DIR / "teamserver"
AGENT_DIR = ROOT_DIR / "agent"
MISSION_CONTROL_DIR = ROOT_DIR / "mission-control"
LAB_ENV_DIR = ROOT_DIR / "lab-env"
TESTS_DIR = ROOT_DIR / "tests"
DIST_WORKER_DIR = ROOT_DIR / "dist_worker"

# Terminal styling (ANSI escape codes)
USE_COLOR = (
    sys.stdout.isatty()
    and (
        platform.system() != "Windows"
        or os.environ.get("WT_SESSION")
        or os.environ.get("TERM")
        or os.environ.get("ANSICON")
    )
)


class Style:
    RESET = "\033[0m" if USE_COLOR else ""
    BOLD = "\033[1m" if USE_COLOR else ""
    DIM = "\033[2m" if USE_COLOR else ""
    CYAN = "\033[36m" if USE_COLOR else ""
    GREEN = "\033[32m" if USE_COLOR else ""
    YELLOW = "\033[33m" if USE_COLOR else ""
    RED = "\033[31m" if USE_COLOR else ""
    MAGENTA = "\033[35m" if USE_COLOR else ""
    BLUE = "\033[34m" if USE_COLOR else ""


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def get_local_ip() -> str:
    """
    Detect the primary LAN IP address of this host machine.
    Uses a non-blocking dummy UDP probe without transmitting packets.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def print_banner():
    """Display the ChimeraC2 ASCII banner with detected host telemetry."""
    lan_ip = get_local_ip()
    banner = f"""{Style.CYAN}{Style.BOLD}
   ____ _     _                             ____ ____  
  / ___| |__ (_)_ __ ___   ___ _ __ __ _   / ___|___ \\ 
 | |   | '_ \\| | '_ ` _ \\ / _ \\ '__/ _` | | |     __) |
 | |___| | | | | | | | | |  __/ | | (_| | | |___ / __/ 
  \\____|_| |_|_|_| |_| |_|\\___|_|  \\__,_|  \\____|_____|
{Style.RESET}{Style.DIM}  Distributed Node Telemetry & Remote Worker Orchestration Platform (v1.0.0){Style.RESET}

  {Style.BOLD}Detected Host LAN IP:{Style.RESET} {Style.GREEN}{Style.BOLD}{lan_ip}{Style.RESET}  {Style.DIM}(Use this IP for external VM / Kali Linux worker connections){Style.RESET}
  {Style.DIM}Platform: {platform.system()} {platform.release()} | Python: {platform.python_version()}{Style.RESET}
"""
    print(banner)


def prompt_input(prompt_text: str, default: str = "") -> str:
    """Prompt the user with an optional default value."""
    if default:
        formatted = f"{Style.BOLD}{prompt_text}{Style.RESET} [{Style.GREEN}{default}{Style.RESET}]: "
    else:
        formatted = f"{Style.BOLD}{prompt_text}{Style.RESET}: "

    try:
        user_input = input(formatted).strip()
        return user_input if user_input else default
    except (KeyboardInterrupt, EOFError):
        print()
        return default


def pause():
    """Wait for user confirmation before returning."""
    try:
        input(f"\n{Style.DIM}Press Enter to return to main menu...{Style.RESET}")
    except (KeyboardInterrupt, EOFError):
        pass


# ─────────────────────────────────────────────────────────────
# Option 1: Start Control Plane (FastAPI Teamserver)
# ─────────────────────────────────────────────────────────────
def run_teamserver():
    clear_screen()
    print_banner()
    print(f"{Style.BOLD}=== [1] Start Control Plane (FastAPI Teamserver) ==={Style.RESET}\n")

    lan_ip = get_local_ip()
    print(f"{Style.DIM}Configuring network listener. Defaulting to 0.0.0.0 allows connections{Style.RESET}")
    print(f"{Style.DIM}from both this host machine and external virtual machines (e.g., VirtualBox Kali Linux).{Style.RESET}\n")

    host = prompt_input("Bind Host IP", default="0.0.0.0")
    port = prompt_input("Port", default="8000")

    print(f"\n{Style.GREEN}{Style.BOLD}[+] Control Plane Listener Configured:{Style.RESET}")
    print(f"  * Local Access URL:     {Style.CYAN}http://127.0.0.1:{port}{Style.RESET}")
    print(f"  * Remote Worker URL:    {Style.GREEN}{Style.BOLD}http://{lan_ip}:{port}{Style.RESET}")
    print(f"  * Interactive Swagger:  {Style.CYAN}http://127.0.0.1:{port}/docs{Style.RESET}")
    print(f"\n{Style.YELLOW}[!] Press Ctrl + C to stop the teamserver and return to menu.{Style.RESET}\n")

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        port,
        "--reload",
    ]

    try:
        subprocess.run(cmd, cwd=str(TEAMSERVER_DIR))
    except KeyboardInterrupt:
        print(f"\n\n{Style.YELLOW}[*] Teamserver stopped by user.{Style.RESET}")
        time.sleep(1)


# ─────────────────────────────────────────────────────────────
# Option 2: Start Operator Dashboard (React Mission Control)
# ─────────────────────────────────────────────────────────────
def run_mission_control():
    clear_screen()
    print_banner()
    print(f"{Style.BOLD}=== [2] Start Operator Dashboard (React Mission Control) ==={Style.RESET}\n")

    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_path:
        print(f"{Style.RED}[!] 'npm' was not found on your system PATH.{Style.RESET}")
        print("Please install Node.js 18+ to run the Mission Control dashboard.")
        pause()
        return

    node_modules = MISSION_CONTROL_DIR / "node_modules"
    if not node_modules.exists():
        print(f"{Style.YELLOW}[!] 'node_modules' not detected in mission-control/.{Style.RESET}")
        print(f"{Style.CYAN}[*] Automatically running 'npm install'...{Style.RESET}\n")
        try:
            subprocess.run([npm_path, "install"], cwd=str(MISSION_CONTROL_DIR), check=True)
            print(f"\n{Style.GREEN}[+] Dependencies installed successfully.{Style.RESET}\n")
        except Exception as e:
            print(f"{Style.RED}[!] npm install failed: {e}{Style.RESET}")
            pause()
            return

    # Prompt user for optional VITE_API_URL override
    lan_ip = get_local_ip()
    print(f"{Style.DIM}Configure backend API URL targeted by the operator interface:{Style.RESET}")
    api_url = prompt_input("VITE_API_URL", default="http://127.0.0.1:8000")

    env = os.environ.copy()
    env["VITE_API_URL"] = api_url.rstrip("/")

    print(f"\n{Style.GREEN}[+] Launching Vite development server...{Style.RESET}")
    print(f"  * Dashboard URL: {Style.CYAN}http://localhost:5173{Style.RESET}")
    print(f"  * Targeted API:  {Style.CYAN}{env['VITE_API_URL']}{Style.RESET}")
    print(f"\n{Style.YELLOW}[!] Press Ctrl + C to stop the dashboard and return to menu.{Style.RESET}\n")

    cmd = [npm_path, "run", "dev"]
    try:
        subprocess.run(cmd, cwd=str(MISSION_CONTROL_DIR), env=env)
    except KeyboardInterrupt:
        print(f"\n\n{Style.YELLOW}[*] Mission Control stopped by user.{Style.RESET}")
        time.sleep(1)


# ─────────────────────────────────────────────────────────────
# Option 3: Run Local Worker Node (agent/agent.py)
# ─────────────────────────────────────────────────────────────
def run_agent():
    clear_screen()
    print_banner()
    print(f"{Style.BOLD}=== [3] Run Local Worker Node (agent/agent.py) ==={Style.RESET}\n")

    lan_ip = get_local_ip()
    print(f"Host LAN IP Reference: {Style.CYAN}{lan_ip}{Style.RESET}")
    print(f"{Style.DIM}If connecting to a remote teamserver or VM control plane, enter that URL below.{Style.RESET}\n")

    server_url = prompt_input("Enter Target Control Plane URL", default="http://127.0.0.1:8000")
    interval = prompt_input("Enter Check-in Interval in seconds", default="5.0")

    env = os.environ.copy()
    env["SERVER_URL"] = server_url.rstrip("/")
    env["CHECKIN_INTERVAL"] = interval

    print(f"\n{Style.GREEN}{Style.BOLD}[+] Worker Configuration Active:{Style.RESET}")
    print(f"  * Target URL: {Style.CYAN}{env['SERVER_URL']}{Style.RESET}")
    print(f"  * Interval:   {Style.CYAN}{env['CHECKIN_INTERVAL']}s{Style.RESET}")
    print(f"\n{Style.YELLOW}[!] Press Ctrl + C to stop the worker and return to menu.{Style.RESET}\n")

    cmd = [sys.executable, "agent.py"]
    try:
        subprocess.run(cmd, cwd=str(AGENT_DIR), env=env)
    except KeyboardInterrupt:
        print(f"\n\n{Style.YELLOW}[*] Worker stopped by user.{Style.RESET}")
        time.sleep(1)


# ─────────────────────────────────────────────────────────────
# Option 4: Export Standalone Worker Bundle (dist_worker/)
# ─────────────────────────────────────────────────────────────
def export_worker_bundle():
    clear_screen()
    print_banner()
    print(f"{Style.BOLD}=== [4] Export Standalone Worker Bundle ==={Style.RESET}\n")
    print(f"{Style.DIM}Packaging a clean, lightweight agent bundle so test machines (like a VirtualBox{Style.RESET}")
    print(f"{Style.DIM}Kali Linux VM) do not need to clone the entire repository.{Style.RESET}\n")

    # 1. Clean and initialize dist_worker directory
    if DIST_WORKER_DIR.exists():
        shutil.rmtree(DIST_WORKER_DIR)
    DIST_WORKER_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Copy worker runtime files
    shutil.copy2(AGENT_DIR / "agent.py", DIST_WORKER_DIR / "agent.py")
    shutil.copy2(AGENT_DIR / "obfuscation.py", DIST_WORKER_DIR / "obfuscation.py")
    shutil.copytree(AGENT_DIR / "modules", DIST_WORKER_DIR / "modules")

    # 3. Write requirements.txt
    requirements_content = "requests>=2.31.0\npsutil>=5.9.0\n"
    (DIST_WORKER_DIR / "requirements.txt").write_text(requirements_content, encoding="utf-8")

    # 4. Generate start_worker.py bootstrap runner
    bootstrap_code = '''#!/usr/bin/env python3
"""
ChimeraC2 — Standalone Worker Node Bootstrap Launcher
Automatically checks dependencies, resolves target Control Plane URL,
and supports spawning one or multiple concurrent worker sessions.
"""

import os
import pathlib
import subprocess
import sys
import time

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent

def check_dependencies():
    missing = []
    try:
        import requests
    except ImportError:
        missing.append("requests")
    try:
        import psutil
    except ImportError:
        missing.append("psutil")

    if missing:
        print(f"[!] Missing required runtime dependencies: {', '.join(missing)}")
        req_file = SCRIPT_DIR / "requirements.txt"
        ans = input("Install dependencies automatically via pip? [Y/n]: ").strip().lower()
        if ans in ("", "y", "yes"):
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
            subprocess.run(cmd, check=True)
            print("[+] Dependencies successfully installed!\\n")
        else:
            print("[!] Cannot continue without requests and psutil.")
            sys.exit(1)

def main():
    check_dependencies()

    print("=" * 60)
    print(" ChimeraC2 Standalone Worker Node Launcher")
    print("=" * 60)

    # Target URL resolution
    server_url = os.environ.get("SERVER_URL")
    if not server_url:
        server_url = input("\\nEnter Target Control Plane URL [default: http://127.0.0.1:8000]: ").strip()
        if not server_url:
            server_url = "http://127.0.0.1:8000"

    checkin = os.environ.get("CHECKIN_INTERVAL")
    if not checkin:
        checkin = input("Enter Check-in Interval in seconds [default: 5.0]: ").strip()
        if not checkin:
            checkin = "5.0"

    # Multi-session prompt
    count_str = input("Number of concurrent worker sessions to spawn [default: 1]: ").strip()
    try:
        count = int(count_str) if count_str else 1
    except ValueError:
        count = 1

    if count <= 1:
        print(f"\\n[+] Launching single worker -> {server_url} (interval {checkin}s)...")
        print("[!] Press Ctrl + C to terminate worker.\\n")
        env = os.environ.copy()
        env["SERVER_URL"] = server_url.rstrip("/")
        env["CHECKIN_INTERVAL"] = str(checkin)
        try:
            subprocess.run([sys.executable, "agent.py"], cwd=str(SCRIPT_DIR), env=env)
        except KeyboardInterrupt:
            print("\\n[*] Worker terminated.")
    else:
        print(f"\\n[+] Spawning {count} concurrent isolated worker instances -> {server_url}...")
        print("[!] Press Ctrl + C to terminate all worker instances.\\n")
        processes = []
        try:
            for i in range(1, count + 1):
                session_dir = SCRIPT_DIR / f"session_{i}"
                session_dir.mkdir(parents=True, exist_ok=True)
                env = os.environ.copy()
                env["SERVER_URL"] = server_url.rstrip("/")
                env["CHECKIN_INTERVAL"] = str(checkin)
                env["CHIMERA_AGENT_ID_FILE"] = str(session_dir / ".chimera_agent_id")
                env["HOME"] = str(session_dir)
                env["USERPROFILE"] = str(session_dir)

                proc = subprocess.Popen(
                    [sys.executable, "agent.py"],
                    cwd=str(SCRIPT_DIR),
                    env=env
                )
                processes.append(proc)
                print(f"  [+] Spawned Worker Instance #{i} (PID: {proc.pid})")
                time.sleep(0.5)

            # Wait for all processes
            for proc in processes:
                proc.wait()
        except KeyboardInterrupt:
            print("\\n[*] Terminating all worker instances...")
            for proc in processes:
                proc.terminate()
            for proc in processes:
                proc.wait()
            print("[+] All worker instances stopped.")

if __name__ == "__main__":
    main()
'''
    (DIST_WORKER_DIR / "start_worker.py").write_text(bootstrap_code, encoding="utf-8")

    # 5. Create zip archive
    zip_archive_path = ROOT_DIR / "dist_worker"
    archive_file = shutil.make_archive(str(zip_archive_path), "zip", str(DIST_WORKER_DIR))

    lan_ip = get_local_ip()
    print(f"{Style.GREEN}{Style.BOLD}[+] Worker Bundle Created Successfully!{Style.RESET}")
    print(f"  * Directory: {Style.CYAN}{DIST_WORKER_DIR}{Style.RESET}")
    print(f"  * Zip File:  {Style.GREEN}{Style.BOLD}{archive_file}{Style.RESET}")
    print(f"\n{Style.BOLD}Deployment to Kali Linux VM / External Node:{Style.RESET}")
    print(f"  1. Copy {Style.CYAN}dist_worker.zip{Style.RESET} to target machine (e.g., via SCP or shared folder):")
    print(f"     {Style.DIM}scp dist_worker.zip kali@192.168.X.X:/home/kali/{Style.RESET}")
    print(f"  2. Unzip and run the bootstrap script:")
    print(f"     {Style.DIM}unzip dist_worker.zip -d worker && cd worker{Style.RESET}")
    print(f"     {Style.CYAN}python3 start_worker.py{Style.RESET}")
    print(f"  3. When prompted, enter your Host LAN URL: {Style.GREEN}http://{lan_ip}:8000{Style.RESET}")

    pause()


# ─────────────────────────────────────────────────────────────
# Option 5: Launch Containerized Lab (docker compose)
# ─────────────────────────────────────────────────────────────
def run_docker_lab():
    clear_screen()
    print_banner()
    print(f"{Style.BOLD}=== [5] Launch Containerized Lab (docker compose) ==={Style.RESET}\n")

    docker_path = shutil.which("docker")
    if not docker_path:
        print(f"{Style.RED}[!] 'docker' was not found on your system PATH.{Style.RESET}")
        print("Please install Docker & Docker Compose to run the containerized lab.")
        pause()
        return

    # Check for .env file in lab-env
    env_file = LAB_ENV_DIR / ".env"
    env_example = LAB_ENV_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        print(f"{Style.YELLOW}[!] 'lab-env/.env' does not exist.{Style.RESET}")
        shutil.copy(env_example, env_file)
        print(f"{Style.GREEN}[+] Created lab-env/.env from .env.example template.{Style.RESET}\n")

    print(f"{Style.CYAN}[*] Starting multi-node lab via Docker Compose...{Style.RESET}")
    print(f"{Style.YELLOW}[!] Press Ctrl + C to stop the lab.{Style.RESET}\n")

    compose_file = LAB_ENV_DIR / "docker-compose.yml"
    cmd = [docker_path, "compose", "-f", str(compose_file), "up", "--build"]

    try:
        subprocess.run(cmd, cwd=str(ROOT_DIR))
    except KeyboardInterrupt:
        print(f"\n\n{Style.YELLOW}[*] Lab stopped by user.{Style.RESET}")
        down_choice = prompt_input("Run 'docker compose down -v' to clean up containers? (Y/n)", default="Y").lower()
        if down_choice in ("", "y", "yes"):
            print(f"{Style.CYAN}[*] Cleaning up containers and virtual networks...{Style.RESET}")
            subprocess.run([docker_path, "compose", "-f", str(compose_file), "down", "-v"], cwd=str(ROOT_DIR))
            print(f"{Style.GREEN}[+] Cleanup complete.{Style.RESET}")
        time.sleep(1)


# ─────────────────────────────────────────────────────────────
# Option 6: Run Automated Verification Suite
# ─────────────────────────────────────────────────────────────
def run_verification_suite():
    clear_screen()
    print_banner()
    print(f"{Style.BOLD}=== [6] Run Automated Verification Suite ==={Style.RESET}\n")

    results = []

    # 1. Obfuscation & Unit Tests (pytest)
    print(f"{Style.CYAN}[1/3] Running Unit & Obfuscation Tests (pytest)...{Style.RESET}")
    pytest_path = shutil.which("pytest")
    cmd_pytest = [pytest_path or sys.executable, "tests/test_obfuscation.py", "-v"] if pytest_path else [sys.executable, "-m", "pytest", "tests/test_obfuscation.py", "-v"]
    res_unit = subprocess.run(cmd_pytest, cwd=str(ROOT_DIR))
    results.append(("Unit & Obfuscation (pytest)", res_unit.returncode == 0))

    # 2. Backend Integration & SQLite Rehydration Tests
    print(f"\n{Style.CYAN}[2/3] Running Backend Integration & Rehydration Tests...{Style.RESET}")
    backend_script = TESTS_DIR / "test_teamserver_backend.py"
    cmd_backend = [sys.executable, str(backend_script)]
    res_backend = subprocess.run(cmd_backend, cwd=str(ROOT_DIR))
    results.append(("Backend Integration & SQLite", res_backend.returncode == 0))

    # 3. Frontend ESLint Verification
    print(f"\n{Style.CYAN}[3/3] Running Frontend ESLint Verification (npm run lint)...{Style.RESET}")
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_path and (MISSION_CONTROL_DIR / "node_modules").exists():
        cmd_lint = [npm_path, "run", "lint"]
        res_lint = subprocess.run(cmd_lint, cwd=str(MISSION_CONTROL_DIR))
        results.append(("Frontend Linter (ESLint)", res_lint.returncode == 0))
    else:
        print(f"{Style.YELLOW}[!] Skipping ESLint (node_modules not installed).{Style.RESET}")
        results.append(("Frontend Linter (ESLint)", None))

    # Summary Table
    print("\n" + "=" * 56)
    print(f" {Style.BOLD}AUTOMATED VERIFICATION SUMMARY{Style.RESET}")
    print("=" * 56)
    all_passed = True
    for name, status in results:
        if status is True:
            badge = f"{Style.GREEN}[PASSED]{Style.RESET}"
        elif status is False:
            badge = f"{Style.RED}[FAILED]{Style.RESET}"
            all_passed = False
        else:
            badge = f"{Style.YELLOW}[SKIPPED]{Style.RESET}"
        print(f"  * {name:<36} {badge}")
    print("=" * 56)

    if all_passed:
        print(f"{Style.GREEN}{Style.BOLD}[+] ALL TEST SUITES PASSED CLEANLY!{Style.RESET}")
    else:
        print(f"{Style.RED}{Style.BOLD}[!] ONE OR MORE TEST SUITES REPORTED ISSUES.{Style.RESET}")

    pause()


# ─────────────────────────────────────────────────────────────
# Main Interactive Menu Loop
# ─────────────────────────────────────────────────────────────
def main():
    while True:
        try:
            clear_screen()
            print_banner()

            print(f"{Style.BOLD}Select a Component or Workflow to Launch:{Style.RESET}")
            print(f"  {Style.CYAN}[1]{Style.RESET} {Style.BOLD}Start Control Plane{Style.RESET}         (FastAPI Teamserver)")
            print(f"  {Style.CYAN}[2]{Style.RESET} {Style.BOLD}Start Operator Dashboard{Style.RESET}    (React Mission Control)")
            print(f"  {Style.CYAN}[3]{Style.RESET} {Style.BOLD}Run Local Worker Node{Style.RESET}       (agent/agent.py)")
            print(f"  {Style.CYAN}[4]{Style.RESET} {Style.BOLD}Export Standalone Worker{Style.RESET}    (dist_worker/ & dist_worker.zip)")
            print(f"  {Style.CYAN}[5]{Style.RESET} {Style.BOLD}Launch Containerized Lab{Style.RESET}    (Docker Compose)")
            print(f"  {Style.CYAN}[6]{Style.RESET} {Style.BOLD}Run Verification Suite{Style.RESET}      (pytest & ESLint)")
            print(f"  {Style.CYAN}[7]{Style.RESET} Exit\n")

            choice = prompt_input("Select Option [1-7]", default="1")

            if choice == "1":
                run_teamserver()
            elif choice == "2":
                run_mission_control()
            elif choice == "3":
                run_agent()
            elif choice == "4":
                export_worker_bundle()
            elif choice == "5":
                run_docker_lab()
            elif choice == "6":
                run_verification_suite()
            elif choice in ("7", "q", "quit", "exit"):
                print(f"\n{Style.GREEN}Exiting ChimeraC2 Launcher. Happy Hacking!{Style.RESET}\n")
                sys.exit(0)
            else:
                print(f"\n{Style.RED}[!] Invalid choice. Please enter 1-7.{Style.RESET}")
                time.sleep(1)

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{Style.GREEN}Exiting ChimeraC2 Launcher. Goodbye!{Style.RESET}\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
