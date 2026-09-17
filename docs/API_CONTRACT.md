# ChimeraC2 API Data Contract

### 1. Agent Registration
* **Endpoint:** `POST /api/v1/beacon/register`
* **Payload:**
```json
{
  "agent_id": "8-char-uuid",
  "hostname": "target-host",
  "os": "Linux / Windows",
  "user": "root / user",
  "ip": "192.168.1.50"
}
```
### 2. Task Polling

- **Endpoint:** `POST /api/v1/beacon/poll`
    
- **Payload:** `{"agent_id": "8-char-uuid"}`
    
- **Response:**
    

JSON

```
{
  "task": {
    "task_id": "t-101",
    "command": "whoami"
  }
}
```

### 3. Task Results

- **Endpoint:** `POST /api/v1/beacon/result`
    
- **Payload:**
    

JSON

```
{
  "task_id": "t-101",
  "agent_id": "8-char-uuid",
  "output": "cm9vdAo=",
  "exit_code": 0
}
```