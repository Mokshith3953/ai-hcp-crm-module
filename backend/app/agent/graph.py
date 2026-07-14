import operator
from functools import lru_cache

from langchain_core.messages import SystemMessage, ToolMessage
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
follow-ups, using the tools available to you.

Only call a tool when the rep's message contains an actual, actionable CRM request
(e.g. describes an HCP interaction to log, references an existing interaction to edit
or follow up on, or asks to search/summarize). If the message is a greeting, small
talk, a vague fragment, or otherwise has no real interaction content (e.g. "hi",
"hello", "test", "what can you do"), do NOT call any tool — just reply conversationally
and, if helpful, prompt the rep for the details you'd need to log something. Never
create a log_interaction record from input that doesn't actually describe an HCP
interaction.

Never call the same tool twice for one request — each tool may run at most once per
request; a repeated call will be skipped. If a request needs more than one action,
call the tools that don't depend on each other's output together in one round; if one
action depends on a result from another (e.g. scheduling a follow-up for an interaction
you are logging in the same request needs the new interaction's id, which only exists
after log_interaction returns it), call the first tool, wait for its result, then call
the second tool using that result in a later round. When logging an interaction, pass
the user's message as `notes` verbatim, unedited, so the tool's own extraction step has
the full context. After a tool runs: for log_interaction, edit_interaction, and
schedule_follow_up, confirm the outcome in one or two concise, friendly sentences. For
summarize_interactions and search_interactions, the tool result IS the answer the rep
asked for — relay its full content back to them (lightly reformatted for readability if
helpful), don't just say it happened."""

MAX_TOOL_HOPS = 4


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    called_tools: Annotated[list, operator.add]
    tool_hops: int


@lru_cache
def _build_graph():
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    tool_node = ToolNode(ALL_TOOLS)

    def call_model(state: AgentState):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def run_tools(state: AgentState):
        last = state["messages"][-1]
        already_called = set(state.get("called_tools", []))
        tool_calls = getattr(last, "tool_calls", None) or []

        keep = [tc for tc in tool_calls if tc["name"] not in already_called]
        skip = [tc for tc in tool_calls if tc["name"] in already_called]

        result_messages = []
        if keep:
            patched_last = last.model_copy(update={"tool_calls": keep})
            patched_state = {**state, "messages": state["messages"][:-1] + [patched_last]}
            tool_result = tool_node.invoke(patched_state)
            result_messages.extend(tool_result["messages"])

        # Every tool_call must get a matching ToolMessage back, or the next LLM
        # call can be rejected as malformed — so skipped duplicates still get one.
        for tc in skip:
            result_messages.append(
                ToolMessage(
                    content=(
                        f"Skipped: {tc['name']} was already called for this "
                        "request — reuse its earlier result instead of calling it again."
                    ),
                    tool_call_id=tc["id"],
                    name=tc["name"],
                )
            )

        return {
            "messages": result_messages,
            "called_tools": [tc["name"] for tc in keep],
            "tool_hops": state.get("tool_hops", 0) + 1,
        }

    def route_after_agent(state: AgentState):
        # Safety net against infinite loops — normal requests resolve in 1-2 hops.
        if state.get("tool_hops", 0) >= MAX_TOOL_HOPS:
            return END
        return tools_condition(state)

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", run_tools)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


def get_agent_graph():
    return _build_graph()
