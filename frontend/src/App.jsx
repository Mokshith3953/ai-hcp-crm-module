import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchInteractions,
  submitInteraction,
  updateInteraction,
  sendAgentMessage,
  chatMessageSent,
  startEditing,
  cancelEditing,
} from "./features/interactionSlice";

const EMPTY_FORM = {
  hcp_name: "",
  topic: "",
  notes: "",
  channel: "structured",
  status: "Logged",
};

const ALL_TOOLS = [
  "log_interaction",
  "edit_interaction",
  "summarize_interactions",
  "schedule_follow_up",
  "search_interactions",
];

function App() {
  const dispatch = useDispatch();
  const { interactions, status, error, editingId, chat } = useSelector(
    (state) => state.interactions,
  );

  const [formData, setFormData] = useState(EMPTY_FORM);
  const [chatInput, setChatInput] = useState("");

  useEffect(() => {
    dispatch(fetchInteractions());
  }, [dispatch]);

  useEffect(() => {
    if (!editingId) {
      setFormData(EMPTY_FORM);
      return;
    }
    const record = interactions.find((item) => item.id === editingId);
    if (record) {
      setFormData({
        hcp_name: record.hcp_name || "",
        topic: record.topic || "",
        notes: record.notes || "",
        channel: record.channel || "structured",
        status: record.status || "Logged",
      });
    }
  }, [editingId, interactions]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (editingId) {
      dispatch(updateInteraction({ id: editingId, changes: formData }));
    } else {
      dispatch(submitInteraction(formData));
      setFormData(EMPTY_FORM);
    }
  };

  const handleChatSubmit = (event) => {
    event.preventDefault();
    if (!chatInput.trim()) return;
    dispatch(chatMessageSent(chatInput));
    dispatch(sendAgentMessage(chatInput));
    setChatInput("");
  };

  const toolsSeen = chat.allTools.length ? chat.allTools : ALL_TOOLS;

  return (
    <div className="page-shell">
      <header className="hero-card">
        <div>
          <p className="eyebrow">AI-first CRM • HCP module</p>
          <h1>
            Log interactions faster with a guided form and conversational AI
          </h1>
          <p className="hero-copy">
            Field representatives can log structured updates or ask the
            LangGraph-powered assistant to manage the interaction workflow.
          </p>
        </div>
      </header>

      <main className="grid-layout">
        <section className="panel">
          <div className="panel-heading">
            <h2>{editingId ? "Edit interaction" : "Log interaction"}</h2>
            <p>
              {editingId
                ? `Editing interaction #${editingId}.`
                : "Capture a new touchpoint that can be used later by the AI agent."}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="stack">
            <label>
              HCP name
              <input
                name="hcp_name"
                value={formData.hcp_name}
                onChange={handleChange}
                required
              />
            </label>
            <label>
              Topic
              <input
                name="topic"
                value={formData.topic}
                onChange={handleChange}
                required
              />
            </label>
            <label>
              Channel
              <select
                name="channel"
                value={formData.channel}
                onChange={handleChange}
              >
                <option value="structured">Structured</option>
                <option value="chat">Chat</option>
                <option value="email">Email</option>
              </select>
            </label>
            <label>
              Status
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
              >
                <option value="Logged">Logged</option>
                <option value="Follow-up scheduled">Follow-up scheduled</option>
                <option value="Closed">Closed</option>
              </select>
            </label>
            <label>
              Notes
              <textarea
                name="notes"
                rows="4"
                value={formData.notes}
                onChange={handleChange}
                required
              />
            </label>
            <div className="button-row">
              <button type="submit" disabled={status === "loading"}>
                {status === "loading"
                  ? "Saving..."
                  : editingId
                    ? "Update interaction"
                    : "Save interaction"}
              </button>
              {editingId ? (
                <button
                  type="button"
                  className="secondary"
                  onClick={() => dispatch(cancelEditing())}
                >
                  Cancel
                </button>
              ) : null}
            </div>
          </form>
          {error ? <p className="error">{error}</p> : null}
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>AI assistant</h2>
            <p>
              Try prompts such as “log a follow-up with Dr. Rao about the new
              cardiology trial”, “edit interaction 1, set status to closed”,
              or “summarize all interactions”.
            </p>
          </div>

          <div className="chat-thread">
            {chat.messages.length === 0 ? (
              <p className="chat-empty">
                No messages yet — start a conversation with the agent.
              </p>
            ) : (
              chat.messages.map((msg, idx) => (
                <div key={idx} className={`chat-bubble chat-${msg.role}`}>
                  <p>{msg.content}</p>
                  {msg.toolsUsed && msg.toolsUsed.length > 0 ? (
                    <span className="tool-tag">
                      tool: {msg.toolsUsed.join(", ")}
                    </span>
                  ) : null}
                </div>
              ))
            )}
            {chat.status === "loading" ? (
              <div className="chat-bubble chat-assistant">
                <p>Thinking…</p>
              </div>
            ) : null}
          </div>

          <form onSubmit={handleChatSubmit} className="stack">
            <textarea
              rows="3"
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              placeholder="Describe the interaction or ask the agent to act"
            />
            <button type="submit" disabled={chat.status === "loading"}>
              Send to agent
            </button>
          </form>

          <div className="tool-list">
            <h3>LangGraph tools</h3>
            <ul>
              {toolsSeen.map((toolName) => (
                <li key={toolName}>{toolName}</li>
              ))}
            </ul>
          </div>

          <div className="history-list">
            <h3>Recent interactions</h3>
            {interactions.slice(0, 8).map((entry) => (
              <article
                key={entry.id}
                className={`history-item ${entry.id === editingId ? "history-item-active" : ""}`}
                onClick={() => dispatch(startEditing(entry.id))}
              >
                <div className="history-item-head">
                  <strong>{entry.hcp_name}</strong>
                  <span className="badge">{entry.status}</span>
                </div>
                <span>{entry.topic}</span>
                <p>{entry.notes}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
