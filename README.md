# ChimeraC2: Distributed Node Telemetry & Remote Worker Orchestration Platform

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/Team-Lol-CTC/ChimeraC2)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.3+-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose_v2-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)

ChimeraC2 is an adversary emulation and distributed node orchestration platform designed for detection validation, security telemetry aggregation, and remote worker coordination. The system pairs an asynchronous **FastAPI** control plane with **SQLite WAL** persistence, a lightweight Python-based **telemetry worker agent**, and a modern **React 19 / Tailwind CSS** mission control dashboard.

---

## Table of Contents
- [System Architecture Overview](#system-architecture-overview)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [The Interactive Launcher (`launch.py`)](#the-interactive-launcher-launchpy)
- [Local Standalone Development Setup](#local-standalone-development-setup)
  - [1. Environment & Dependencies](#1-environment--dependencies)
  - [2. Start the Control Plane (Teamserver)](#2-start-the-control-plane-teamserver)
  - [3. Start Mission Control (Dashboard)](#3-start-mission-control-dashboard)
  - [4. Launch a Local Worker Node](#4-launch-a-local-worker-node)
- [Cross-OS & VirtualBox Kali Linux Testing Guide](#cross-os--virtualbox-kali-linux-testing-guide)
  - [1. Host Teamserver Listener (`0.0.0.0`)](#1-host-teamserver-listener-0000)
  - [2. VirtualBox Network Configuration](#2-virtualbox-network-configuration)
  - [3. Export Standalone Worker Bundle](#3-export-standalone-worker-bundle)
  - [4. Deploy & Run on Kali Linux](#4-deploy--run-on-kali-linux)
  - [5. Concurrent Multi-Worker Emulation](#5-concurrent-multi-worker-emulation)
- [Containerized Lab Execution](#containerized-lab-execution)
  - [Deterministic Healthcheck-Gated Startup](#deterministic-healthcheck-gated-startup)
  - [Starting the Container Lab](#starting-the-container-lab)
  - [Tearing Down the Lab](#tearing-down-the-lab)
- [Test Suite Execution](#test-suite-execution)
  - [Unit & Obfuscation Tests](#unit--obfuscation-tests)
  - [Backend Integration Tests](#backend-integration-tests)
  - [Frontend Lint & Production Build](#frontend-lint--production-build)
- [API & Wire Protocol Specification](#api--wire-protocol-specification)
- [Responsible Use Disclaimer](#responsible-use-disclaimer)

---

## System Architecture Overview

ChimeraC2 is structured into four decoupled, production-hardened subsystems:

```
┌─────────────────────────────────────────────────────────────┐
│                 Mission Control (React 19)                  │
│       Operator Web UI • WebSocket Dispatch • Live Stream    │
└──────────────────────────────▲──────────────────────────────┘
                               │
               WebSocket /ws/operator & REST API
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                  Teamserver (FastAPI / ASGI)                │
│       State Rehydration • Task Queuing • Audit Logging      │
└──────────────────────────────┬──────────────────────────────┘
                               │
               SQLite Database (WAL Mode, timeout=30s)
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Polling Worker Fleet                     │
│    HTTP Beacon Poll • System Telemetry • Subprocess Exec    │
│       [victim_alpha]      [victim_bravo]      [local]       │
└─────────────────────────────────────────────────────────────┘
```

1. **Control Plane (`teamserver/`):**
   - High-throughput asynchronous FastAPI core serving HTTP beacon endpoints and operator WebSockets.
   - Concurrent SQLite backend utilizing **Write-Ahead Logging (`PRAGMA journal_mode=WAL;`)**, 30-second busy handlers, and schema migration support.
   - Robust crash resilience with automatic in-memory queue and agent status rehydration upon startup.
   - Resilient Base64 task output decoding with error replacement (`errors='replace'`) preventing payload corruption.

2. **Worker Execution Engine (`agent/`):**
   - Headless, standalone agent running an event-driven beacon loop with configurable intervals and jitter.
   - Obfuscated HTTP communication featuring dynamic browser User-Agent rotation, custom headers, and Base64 encoded payload transport.
   - Isolated command execution via subprocess pipes with exit code and stdout/stderr capture.

3. **Telemetry & Host Triage (`agent/modules/triage.py`):**
   - Host profiling capturing OS distribution, kernel version, processor architecture, CPU logical cores, total/available RAM in GB, user privileges, and running processes.

4. **Operator Dashboard (`mission-control/`):**
   - Single-page application built on React 19, Vite, and Tailwind CSS.
   - Real-time bi-directional WebSocket interface (`/ws/operator`) for interactive command dispatch and instantaneous terminal streaming.
   - Centralized endpoint configuration (`config.js`) supporting environment overrides (`VITE_API_URL`, `VITE_WS_URL`) for remote deployments.

5. **Lab Environment (`lab-env/`):**
   - Multi-container Docker Compose lab orchestrating the teamserver alongside unprivileged Linux worker containers (`victim_linux_alpha`, `victim_linux_bravo`).
   - Zero-race startup governed by Docker healthchecks (`condition: service_healthy`).

---

## Repository Structure

```
ctc-project/
├── agent/                        # Polling worker agent implementation
│   ├── modules/
│   │   └── triage.py             # System profiling and telemetry survey
│   ├── agent.py                  # Beacon loop and task execution engine
│   └── obfuscation.py            # Header rotation and Base64 payload encoding
├── docs/
│   └── API_CONTRACT.md           # Formal HTTP/WebSocket protocol specification
├── lab-env/                      # Containerized deployment orchestration
│   ├── .env.example              # Lab environment variable template
│   ├── Dockerfile.worker         # Non-root unprivileged worker container image
│   └── docker-compose.yml        # Multi-node healthcheck-gated compose topology
├── mission-control/              # React 19 operator telemetry dashboard
│   ├── src/
│   │   ├── components/           # Fleet table, terminal, audit, triage views
│   │   ├── hooks/                # WebSocket streaming (useC2Stream.js)
│   │   ├── config.js             # Centralized API & WS endpoint resolver
│   │   └── App.jsx               # Main application view
│   ├── package.json              # Node dependencies & build scripts
│   └── vite.config.js            # Vite configuration
├── teamserver/                   # FastAPI control plane
│   ├── app/
│   │   ├── db.py                 # SQLite WAL connection manager & migrations
│   │   ├── main.py               # REST route handlers & WebSocket broadcaster
│   │   └── models.py             # Pydantic v2 schemas for telemetry & tasks
│   └── Dockerfile                # Production teamserver container image
├── tests/                        # Automated test suites
│   ├── test_obfuscation.py       # Obfuscation & stealth header unit tests
│   └── test_teamserver_backend.py# Backend integration & persistence tests
├── .gitignore                    # Git hygiene exclusion rules
├── requirements.txt              # Core Python runtime dependencies
├── launch.py                     # Cross-platform interactive operator launcher
└── README.md                     # Capstone runbook & project documentation
```

---

## Prerequisites

Before setting up ChimeraC2, ensure your development system satisfies the following prerequisites:

| Component | Minimum Version | Recommended | Notes |
|---|---|---|---|
| **Python** | 3.10+ | 3.11 or 3.13 | Required for Teamserver, Agent, and Tests |
| **Node.js** | 18.0.0+ | 20.x or 22.x LTS | Required for Mission Control dashboard |
| **npm** | 9.0.0+ | 10.x+ | Included with Node.js |
| **Docker** | 24.0+ | Latest | Required for multi-node container lab |
| **Docker Compose** | 2.20+ | Compose v2 | Included in Docker Desktop / Docker Engine |

---

## The Interactive Launcher (`launch.py`)

ChimeraC2 provides a zero-dependency, pure Python interactive terminal launcher (`launch.py`) that automates environment preparation, cross-network host binding, and deployment workflows:

```bash
python launch.py
```

```
   ____ _     _                             ____ ____  
  / ___| |__ (_)_ __ ___   ___ _ __ __ _   / ___|___ \ 
 | |   | '_ \| | '_ ` _ \ / _ \ '__/ _` | | |     __) |
 | |___| | | | | | | | | |  __/ | | (_| | | |___ / __/ 
  \____|_| |_|_|_| |_| |_|\___|_|  \__,_|  \____|_____|
  Distributed Node Telemetry & Remote Worker Orchestration Platform (v1.0.0)

  Detected Host LAN IP: 10.6.198.188  (Use this IP for external VM / Kali Linux worker connections)
  Platform: Windows 11 | Python: 3.13.5

Select a Component or Workflow to Launch:
  [1] Start Control Plane         (FastAPI Teamserver)
  [2] Start Operator Dashboard    (React Mission Control)
  [3] Run Local Worker Node       (agent/agent.py)
  [4] Export Standalone Worker    (dist_worker/ & dist_worker.zip)
  [5] Launch Containerized Lab    (Docker Compose)
  [6] Run Verification Suite      (pytest & ESLint)
  [7] Exit
```

### Core Launcher Features
1. **Automatic Host LAN IP Discovery:** Probes the primary network interface on boot and prints the IP address in the header banner, so operators immediately know what URL to supply to external virtual machines or remote nodes.
2. **Control Plane (`[1]`):** Prompts for bind interface (defaulting to `0.0.0.0` to permit remote agent connections) and port (default `8000`), displaying local and remote endpoints before launching Uvicorn.
3. **Operator Dashboard (`[2]`):** Checks for `mission-control/node_modules/` (automatically installing dependencies via `npm install` if missing), offers interactive `VITE_API_URL` overrides, and launches the Vite server.
4. **Local Worker Node (`[3]`):** Interactively prompts for target control plane URL and polling interval, setting `SERVER_URL` and `CHECKIN_INTERVAL` environment variables.
5. **Standalone Worker Packager (`[4]`):** Packages a minimal, self-contained worker bundle at `./dist_worker/` and `./dist_worker.zip` with a multi-session bootstrap launcher (`start_worker.py`), avoiding the need to clone the entire project on guest VMs.
6. **Containerized Lab Management (`[5]`):** Automatically initializes `.env` from template if missing, runs `docker compose up --build`, and cleanly handles `Ctrl+C` by offering automated container teardown.
7. **Unified Verification Suite (`[6]`):** Concurrently validates `pytest tests/test_obfuscation.py`, backend integration & SQLite WAL rehydration (`tests/test_teamserver_backend.py`), and frontend linting (`npm run lint`), displaying an aggregated summary table.

---

## Local Standalone Development Setup

Follow these steps to run each component natively on your workstation without containers.

### 1. Environment & Dependencies

Clone the repository and initialize a Python virtual environment:

```bash
# Clone the repository
git clone https://github.com/Team-Lol-CTC/ChimeraC2.git
cd ChimeraC2

# Create and activate a Python virtual environment
python -m venv venv

# On Linux / macOS:
source venv/bin/activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install runtime and testing dependencies
pip install -r requirements.txt
pip install pytest httpx
```

### 2. Start the Control Plane (Teamserver)

Launch the FastAPI teamserver using `uvicorn`. The database will automatically initialize at `teamserver/chimera_c2.db` in WAL mode:

```bash
# Navigate to the teamserver directory or launch from root:
cd teamserver
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

* The teamserver will begin listening on `http://127.0.0.1:8000`.
* Interactive OpenAPI/Swagger documentation is available at `http://127.0.0.1:8000/docs`.
* Healthcheck verification endpoint: `http://127.0.0.1:8000/health`.

### 3. Start Mission Control (Dashboard)

In a separate terminal, install the frontend dependencies and boot the Vite development server:

```bash
cd mission-control
npm install
npm run dev
```

* Mission Control will launch at `http://localhost:5173`.
* By default, it connects to the local control plane at `http://127.0.0.1:8000` (API) and `ws://127.0.0.1:8000/ws/operator` (WebSocket).
* To point Mission Control to a remote or non-standard server, define `VITE_API_URL`:
  ```bash
  # Optional: custom endpoint targeting
  VITE_API_URL="http://192.168.1.100:8000" npm run dev
  ```

### 4. Launch a Local Worker Node

In a third terminal with the virtual environment activated, start an agent worker node:

```bash
# Default beacon interval (5 seconds) pointing to localhost:8000
python agent/agent.py

# Or configure via environment variables:
SERVER_URL="http://127.0.0.1:8000" CHECKIN_INTERVAL="3.0" python agent/agent.py
```

Upon startup, the worker performs:
1. System survey and triage collection via `agent/modules/triage.py`.
2. Initial registration check-in at `/api/v1/beacon/register`.
3. Periodic polling loop at `/api/v1/beacon/poll`.

Check the Mission Control dashboard at `http://localhost:5173` to observe the newly registered agent appear in the **Active Target Fleet** with live telemetry!

---

## Cross-OS & VirtualBox Kali Linux Testing Guide

This guide details how to validate ChimeraC2 across physical and virtual network boundaries: hosting the Control Plane and Mission Control Dashboard on your primary host OS while executing live worker nodes inside a VirtualBox guest (such as Kali Linux).

```
┌────────────────────────────────────────────────────────┐
│                   Host Operating System                │
│  Teamserver (0.0.0.0:8000) ── Host LAN: 192.168.1.50   │
│  Mission Control Dashboard (http://localhost:5173)     │
└───────────────────────────▲────────────────────────────┘
                            │
             HTTP Polling & Telemetry (Port 8000)
                            │
┌───────────────────────────▼────────────────────────────┐
│              VirtualBox Guest (Kali Linux VM)          │
│  Standalone Bundle: dist_worker/                       │
│  Single or Concurrent Multi-Session Workers (1 to N)   │
└────────────────────────────────────────────────────────┘
```

### 1. Host Teamserver Listener (`0.0.0.0`)
Start the teamserver on your host machine bound to `0.0.0.0` so it accepts connections from the local virtual network interface:
```bash
python launch.py
# Select [1] Start Control Plane
# Bind Host IP [0.0.0.0]: <Press Enter>
# Port [8000]: <Press Enter>
```
Note the **Detected Host LAN IP** printed in the header banner (e.g. `192.168.1.50` or `10.6.198.188`).

### 2. VirtualBox Network Configuration
Ensure the Kali Linux VM can reach your host IP:
* **Option A — Bridged Adapter (Recommended):** In VirtualBox, open VM Settings → **Network** → **Adapter 1**, select **Bridged Adapter** attached to your physical Wi-Fi/Ethernet card. The VM receives an IP on your home/office subnet.
* **Option B — Host-Only Adapter:** Attach an adapter to VirtualBox's **Host-Only Ethernet Adapter** (e.g., `192.168.56.x`).
* **Connectivity Test:** From inside the Kali Linux terminal, verify communication:
  ```bash
  curl -I http://<HOST_LAN_IP>:8000/health
  # HTTP/1.1 200 OK
  ```

### 3. Export Standalone Worker Bundle
Rather than cloning the entire Git repository or installing Node.js inside the Kali VM, export the self-contained worker bundle:
```bash
python launch.py
# Select [4] Export Standalone Worker
```
This generates:
* `./dist_worker/` directory
* `./dist_worker.zip` archive containing:
  * `agent.py` — Beacon loop and subprocess execution core
  * `obfuscation.py` — Header rotation and Base64 mask engine
  * `modules/triage.py` — OS and hardware survey module
  * `requirements.txt` — Worker dependencies (`requests`, `psutil`)
  * `start_worker.py` — Interactive dependency-checking bootstrap launcher

### 4. Deploy & Run on Kali Linux
Transfer `dist_worker.zip` to the Kali VM (via SCP, shared folders, or a quick web server):

```bash
# Transfer archive via SCP from host:
scp dist_worker.zip kali@<KALI_VM_IP>:/home/kali/

# Inside Kali Linux terminal:
unzip dist_worker.zip -d worker
cd worker
python3 start_worker.py
```

The bootstrap script will:
1. Verify `requests` and `psutil` are installed, prompting to automatically install them via `pip` if missing.
2. Prompt for the Control Plane URL: enter `http://<HOST_LAN_IP>:8000`.
3. Survey host hardware and software telemetry (kernel release, CPU cores, RAM, privilege level, and processes).
4. Register with the control plane and begin the polling beacon loop.

### 5. Concurrent Multi-Worker Emulation
When running `start_worker.py`, the script asks:
```text
Number of concurrent worker sessions to spawn [default: 1]: 3
```
Specifying multiple sessions automatically spawns parallel, isolated worker processes. Each process is assigned an independent working environment (`session_1/`, `session_2/`, etc.) and a unique `.chimera_agent_id`, simulating multiple distinct compromised endpoints from a single VM!

Open Mission Control (`http://localhost:5173`) to observe each worker node appear live in the **Active Target Fleet** table.

---

## Containerized Lab Execution

ChimeraC2 provides a fully reproducible multi-node lab using Docker Compose. The lab simulates an enterprise environment with a central control plane and two separate Linux worker nodes running in dedicated containers.

### Deterministic Healthcheck-Gated Startup

Worker nodes depend on the teamserver being healthy before attempting registration. The control plane implements a lightweight Python-based healthcheck probe:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
  interval: 5s
  timeout: 3s
  retries: 5
  start_period: 10s
```

Worker nodes (`victim_linux_alpha` and `victim_linux_bravo`) declare `depends_on: { teamserver: { condition: service_healthy } }`, eliminating connection-refused startup races.

### Starting the Container Lab

1. Copy the environment configuration template:
   ```bash
   cp lab-env/.env.example lab-env/.env
   ```

2. Review or adjust variable settings in `lab-env/.env` if desired:
   ```env
   TEAMSERVER_PORT=8000
   SERVER_URL=http://teamserver:8000
   CHECKIN_INTERVAL=5.0
   ```

3. Build and launch all services:
   ```bash
   # From the project root:
   docker compose -f lab-env/docker-compose.yml up --build

   # Or from the lab-env directory:
   cd lab-env
   docker compose up --build
   ```

4. Verify container status:
   ```bash
   docker compose -f lab-env/docker-compose.yml ps
   ```

   You should observe three healthy/running containers:
   * `c2_teamserver`: Exposing port `8000` to the host.
   * `victim_alpha`: Unprivileged Linux worker beaconing every 5 seconds.
   * `victim_bravo`: Unprivileged Linux worker beaconing every 5 seconds.

5. Open `http://localhost:5173` in Mission Control to interact with both containerized workers simultaneously!

### Tearing Down the Lab

To gracefully stop and remove containers and virtual networks:

```bash
docker compose -f lab-env/docker-compose.yml down -v
```

---

## Test Suite Execution

ChimeraC2 includes comprehensive test coverage for backend schemas, SQLite persistence, rehydration routines, Base64 result handling, obfuscation, and frontend code quality.

### Unit & Obfuscation Tests

Run the test suite using `pytest`:

```bash
# Run obfuscation unit tests
pytest tests/test_obfuscation.py -v

# Run entire test suite
pytest tests/ -v
```

### Backend Integration Tests

Execute the full backend lifecycle integration script covering Pydantic validation, SQLite WAL migrations, COALESCE upserts, in-memory state rehydration across reboots, and Base64 output decoding:

```bash
python tests/test_teamserver_backend.py
```

Expected output:
```
[*] Starting backend integration tests...
--- Testing Deliverable 1: Pydantic Validation ---
[+] 422 properly returned for malformed register payload.
[+] 200 OK returned for valid register payload with telemetry.
[+] 422 properly returned for malformed poll payload.
[+] 200 OK returned for valid poll request.
[+] 422 properly returned for malformed task result payload.
--- Testing Deliverable 2: SQLite Schema & Telemetry Persistence ---
[+] Full extended telemetry successfully retrieved from SQLite.
[+] COALESCE upsert verified: heartbeat update preserved telemetry fields.
--- Testing Deliverable 3: Startup In-Memory Rehydration ---
[+] Rehydration verified: agent and pending task restored from SQLite.
[+] Agent polled and received restored task after server reboot!
--- Testing Task Result & Base64 Decoding ---
[+] Task result Base64 decoded and persisted as COMPLETED in SQLite.
==============================================
>>> ALL BACKEND DELIVERABLES PASSED 100%! <<<
==============================================
```

### Frontend Lint & Production Build

Verify that Mission Control satisfies all React 19 compiler hooks and ESLint rules:

```bash
cd mission-control

# Check ESLint rules (0 errors, 0 warnings expected)
npm run lint

# Validate production bundle compilation
npm run build
```

---

## API & Wire Protocol Specification

For complete payload schemas, error structures, and event models, consult [docs/API_CONTRACT.md](docs/API_CONTRACT.md).

| Method | Endpoint | Consumer | Description |
|---|---|---|---|
| `POST` | `/api/v1/beacon/register` | Worker Agent | Initial host triage and telemetry registration. |
| `POST` | `/api/v1/beacon/poll` | Worker Agent | Periodic beacon poll to fetch queued tasks. |
| `POST` | `/api/v1/beacon/result` | Worker Agent | Submits Base64 encoded task execution results. |
| `WS` | `/ws/operator` | Mission Control | Real-time bi-directional operator command dispatch & streaming. |
| `GET` | `/api/v1/tasks` | Mission Control | Queries persisted execution history with optional `agent_id` filter. |
| `GET` | `/api/v1/audit` | Mission Control | Queries system audit trail events with pagination (`limit`). |
| `GET` | `/health` | Docker / Ops | Healthcheck endpoint validating database responsiveness. |

---

## Responsible Use Disclaimer

> [!CAUTION]
> **ChimeraC2 is developed exclusively for authorized adversary emulation, defensive detection engineering, red/blue team security exercises, and educational research.**
> 
> Use of this software against targets without prior explicit written authorization from the system owner is illegal. Users are solely responsible for ensuring adherence to all applicable local, state, federal, and international cyber laws. The authors and contributors assume no liability for misuse or damage caused by this software.