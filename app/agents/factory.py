from __future__ import annotations

from importlib.util import find_spec

from sqlalchemy.orm import Session

from app.agents.runtime import AgentRuntimeService
from app.core.config import Settings


def create_agent_runtime(db: Session, settings: Settings) -> AgentRuntimeService:  #创建是用基础的Agent还是Langgraph的Agent
    if wants_langgraph(settings) and langgraph_available():
        from app.agents.langgraph_runtime import LangGraphAgentRuntimeService

        return LangGraphAgentRuntimeService(db, settings)
    return AgentRuntimeService(db, settings)


def agent_framework_status(settings: Settings) -> dict:   #检查并且报告系统目前实际使用的是哪个 AI 框架
    requested = settings.agent_framework.lower()
    available = langgraph_available()
    active = "langgraph" if requested == "langgraph" and available else "custom"
    return {
        "requested": requested,    #配置想用的框架
        "active": active,          #实际使用的框架
        "langgraphAvailable": available,
        "fallback": active != requested,  # 是否发生了降级
    }


def wants_langgraph(settings: Settings) -> bool:
    return settings.agent_framework.lower() == "langgraph"


def langgraph_available() -> bool:
    return find_spec("langgraph") is not None
