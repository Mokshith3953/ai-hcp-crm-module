import uuid

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.graph import get_agent_graph
from app.agent.tools import ALL_TOOLS
from app.schemas import AgentRequest, AgentResponse

router = APIRouter(prefix="/api/agent", tags=["agent"])

TOOL_NAMES = [t.name for t in ALL_TOOLS]


@router.post("", response_model=AgentResponse)
def run_agent(request: AgentRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(400, "Message cannot be empty")

    thread_id = request.thread_id or str(uuid.uuid4())
    graph = get_agent_graph()
    config = {"configurable": {"thread_id": thread_id}}

    prior_state = graph.get_state(config)
    prior_count = len(prior_state.values.get("messages", [])) if prior_state.values else 0

    result = graph.invoke(
        {"messages": [HumanMessage(content=message)], "tool_hops": 0}, config=config
    )
    new_messages = result["messages"][prior_count:]

    tools_used = [
        m.name
        for m in new_messages
        if isinstance(m, ToolMessage) and m.name in TOOL_NAMES
    ]
    reply = next(
        (
            m.content
            for m in reversed(new_messages)
            if isinstance(m, AIMessage) and m.content
        ),
        "The agent completed the request.",
    )

    return AgentResponse(
        reply=reply,
        thread_id=thread_id,
        tools_used=tools_used,
        tools=TOOL_NAMES,
    )
