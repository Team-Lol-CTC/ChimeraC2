# ChimeraC2: Adversary Emulation Framework

A modular, lightweight Command & Control (C2) simulation system built for authorized post-exploitation and detection validation.

## Architecture & Work Allocation
- **Teamserver (`/teamserver`):** Lead Developer (FastAPI, SQLite, REST/WebSocket state)
- **Agent Core (`agent/agent.py`):** Member 2 (Beacon loop, task execution)
- **Host Triage (`agent/modules/triage.py`):** Member 3 (Host reconnaissance, process survey)
- **Stealth Transport & Docs (`agent/obfuscation.py`, `/docs`):** Nebiyu Mathewos (`@Neba_H9`) — Traffic masking, Base64 payload obfuscation, header rotation, and API contract documentation[cite: 4, 5].
- **Mission Control (`/mission-control`):** Member 5 (Operator UI & live stream dashboard)
- **Lab & Verification (`/lab-env`):** Member 6 (Docker containers, testing)

## Branching Guidelines
1. Never push directly to `main`.
2. Branch out from `main`: `git checkout -b feature/<your-module-name>`.
3. Push to your branch and submit a Pull Request to `main`.