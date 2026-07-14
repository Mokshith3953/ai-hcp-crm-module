import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from app import crud
from app.database import SessionLocal
from app.llm import get_llm
from app.schemas import InteractionCreate, InteractionUpdate

EXTRACTION_PROMPT = """You are an entity-extraction assistant for a pharma CRM.
From the free-text note below, extract JSON with keys:
hcp_name, hcp_specialty, topic, sentiment (Positive/Neutral/Negative), notes (a cleaned-up
one or two sentence summary of the interaction), interaction_type (one of: Meeting, Call,
Email, Conference — best guess, default "Meeting"), attendees (array of person names
mentioned besides the HCP, [] if none), materials_shared (array of document/brochure/sample
names mentioned, [] if none), outcomes (a short sentence on what was agreed or decided, or
null).
If a field cannot be determined, use null (or [] for array fields). Respond with ONLY the
JSON object, no prose.

Note: {text}"""

SUMMARY_PROMPT = """You are a pharma field-rep assistant. Summarize the following HCP
interactions into a concise briefing (3-5 sentences) a rep could skim before their next visit.
Highlight sentiment trends and any open follow-ups.

Interactions:
{items}"""


def _extract_entities(free_text: str) -> dict:
    llm = get_llm()
    response = llm.invoke(
        [
            SystemMessage(content="You extract structured CRM data as strict JSON."),
            HumanMessage(content=EXTRACTION_PROMPT.format(text=free_text)),
        ]
    )
    content = response.content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.split("\n", 1)[-1] if "\n" in content else content
        content = content.replace("json\n", "", 1)
    try:
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return {}


@tool
def log_interaction(
    hcp_name: str = "",
    topic: str = "",
    notes: str = "",
    channel: str = "chat",
) -> str:
    """Log a new HCP interaction. Pass `notes` as the user's original message text
    VERBATIM (do not summarize or shorten it) — the tool runs its own LLM entity
    extraction (HCP name, specialty, topic, sentiment) over that raw text, so
    condensing it first will cause details to be lost. hcp_name/topic may be left
    blank if not explicitly stated; they will be inferred from notes.
    """
    extracted = _extract_entities(notes or f"{hcp_name} {topic}".strip())

    payload = InteractionCreate(
        hcp_name=hcp_name or extracted.get("hcp_name") or "Unknown HCP",
        hcp_specialty=extracted.get("hcp_specialty"),
        topic=topic or extracted.get("topic") or "General update",
        notes=extracted.get("notes") or notes or "No additional notes provided.",
        channel=channel,
        sentiment=extracted.get("sentiment"),
        interaction_type=extracted.get("interaction_type") or "Meeting",
        attendees=extracted.get("attendees") or [],
        materials_shared=extracted.get("materials_shared") or [],
        outcomes=extracted.get("outcomes"),
    )

    db = SessionLocal()
    try:
        interaction = crud.create_interaction(db, payload)
        return (
            f"Logged interaction #{interaction.id} with {interaction.hcp_name} "
            f"on '{interaction.topic}' (sentiment: {interaction.sentiment or 'n/a'})."
        )
    finally:
        db.close()


@tool
def edit_interaction(interaction_id: str, updates: str) -> str:
    """Edit an existing logged interaction. `interaction_id` is the numeric id (as a
    string, e.g. "1"), and `updates` is a short natural-language description of what
    to change (e.g. "set status to Follow-up scheduled" or "notes: discussed new
    dosage guidance"). The description is turned into structured field updates via
    the LLM.
    """
    try:
        interaction_id = int(interaction_id)
    except ValueError:
        return f"'{interaction_id}' is not a valid interaction id."

    llm = get_llm()
    prompt = (
        "Given this instruction, produce a JSON object with only the fields to update "
        "from this set: hcp_name, hcp_specialty, topic, notes, channel, sentiment, "
        "status, follow_up_date, interaction_type, interaction_date, interaction_time, "
        "outcomes, follow_up_actions (attendees/materials_shared/samples_distributed are "
        "arrays of strings if included). Respond with ONLY JSON.\n\nInstruction: " + updates
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip().strip("`")
    if content.startswith("json\n"):
        content = content[5:]
    try:
        fields = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        fields = {}

    db = SessionLocal()
    try:
        updated = crud.update_interaction(
            db, interaction_id, InteractionUpdate(**fields)
        )
        if updated is None:
            return f"No interaction found with id {interaction_id}."
        return f"Updated interaction #{updated.id}: {fields}"
    finally:
        db.close()


@tool
def summarize_interactions(hcp_name: str = "") -> str:
    """Summarize recent interactions, optionally filtered to a specific HCP name,
    using the LLM to produce a short briefing of themes, sentiment, and follow-ups.
    """
    db = SessionLocal()
    try:
        records = crud.recent_interactions_for_hcp(db, hcp_name or None, limit=8)
    finally:
        db.close()

    if not records:
        return "No interactions found to summarize."

    items = "\n".join(
        f"- {r.hcp_name} ({r.topic}, sentiment: {r.sentiment or 'n/a'}, "
        f"status: {r.status}): {r.notes}"
        for r in records
    )
    llm = get_llm()
    response = llm.invoke([HumanMessage(content=SUMMARY_PROMPT.format(items=items))])
    return response.content.strip()


@tool
def schedule_follow_up(interaction_id: str, follow_up_date: str, reason: str = "") -> str:
    """Schedule a follow-up reminder for a logged interaction by id (a string, e.g.
    "1"), setting a follow-up date (any human-readable date string) and marking its
    status.
    """
    try:
        interaction_id = int(interaction_id)
    except ValueError:
        return f"'{interaction_id}' is not a valid interaction id."

    db = SessionLocal()
    try:
        updated = crud.update_interaction(
            db,
            interaction_id,
            InteractionUpdate(
                follow_up_date=follow_up_date, status="Follow-up scheduled"
            ),
        )
        if updated is None:
            return f"No interaction found with id {interaction_id}."
        return (
            f"Follow-up scheduled for interaction #{updated.id} on {follow_up_date}."
            + (f" Reason: {reason}" if reason else "")
        )
    finally:
        db.close()


@tool
def search_interactions(query: str) -> str:
    """Search previously logged interactions by HCP name, topic, or notes keyword."""
    db = SessionLocal()
    try:
        results = crud.search_interactions(db, query)
    finally:
        db.close()

    if not results:
        return f"No interactions matched '{query}'."
    lines = [
        f"#{r.id} {r.hcp_name} — {r.topic} ({r.status})" for r in results
    ]
    return "Found matches:\n" + "\n".join(lines)


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    summarize_interactions,
    schedule_follow_up,
    search_interactions,
]
