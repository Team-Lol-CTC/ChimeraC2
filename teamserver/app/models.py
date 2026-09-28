from pydantic import BaseModel, Field
from typing import Optional, List, Any


class AgentRegisterSchema(BaseModel):
    agent_id: str
    hostname: str
    os: str
    user: str
    ip: str
    os_release: Optional[str] = "Unknown"
    is_privileged: Optional[bool] = False
    cpu_cores: Optional[int] = 1
    total_ram_gb: Optional[float] = 0.0
    sample_processes: Optional[List[Any]] = []


class PollRequestSchema(BaseModel):
    agent_id: str


class TaskDispatchSchema(BaseModel):
    agent_id: str
    command: str


class TaskResultSchema(BaseModel):
    task_id: str
    agent_id: str
    output: str
    exit_code: int