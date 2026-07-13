from functools import lru_cache

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import Annotated, TypedDict

from app.agent.tools import ALL_TOOLS
from app.llm import get_llm

SYSTEM_PROMPT = """You are the AI assistant embedded in the Log Interaction screen of an
AI-first CRM for pharmaceutical field representatives calling on Healthcare Professionals
(HCPs). You help reps log, edit, summarize, and search interactions, and schedule
follow-ups, using the tools available to you. Always prefer calling a tool over just
describing what you would do. Call at most one tool per user request unless the first
call's result indicates it failed and must be retried — never call the same tool twice
for the same request. When logging an interaction, pass the user's message as `notes`
verbatim, unedited, so the tool's own extraction step has the full context. After a
tool runs: for log_interaction, edit_interaction, and schedule_follow_up, confirm the
outcome in one or two concise, friendly sentences. For summarize_interactions and
search_interactions, the tool result IS the answer the rep asked for — relay its full
content back to them (lightly reformatted for readability if helpful), don't just say
it happened."""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


@lru_cache
def _build_graph():
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def call_model(state: AgentState):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


def get_agent_graph():
    return _build_graph()
