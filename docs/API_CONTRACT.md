# ChimeraC2 API Contract & Payload Specification

This document defines the communication standards between the ChimeraC2 Agent and the Teamserver.

## 1. Agent Registration
* **Endpoint:** `/api/v1/beacon/register`
* **Method:** `POST`
* **Payload Schema:**
  ```json
  {
    "agent_id": "str",
    "hostname": "str",
    "os": "str",
    "user": "str",
    "ip": "str"
  }