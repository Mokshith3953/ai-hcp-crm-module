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
  suggestFollowUps,
  clearSuggestions,
} from "./features/interactionSlice";

const EMPTY_FORM = {
  hcp_name: "",
  topic: "",
  notes: "",
  channel: "structured",
  status: "Logged",
  interaction_type: "Meeting",
  interaction_date: "",
  interaction_time: "",
  attendees: [],
  materials_shared: [],
  samples_distributed: [],
  sentiment: "Neutral",
  outcomes: "",
  follow_up_actions: "",
};

const ALL_TOOLS = [
  "log_interaction",
  "edit_interaction",
  "summarize_interactions",
  "schedule_follow_up",
  "search_interactions",
];

const SENTIMENTS = [
  { value: "Positive", icon: "🙂" },
  { value: "Neutral", icon: "😐" },
  { value: "Negative", icon: "🙁" },
];

function ChipListField({ label, placeholder, addLabel, values, onChange }) {
  const [draft, setDraft] = useState("");

  const addChip = () => {
    const trimmed = draft.trim();
    if (!trimmed) return;
    onChange([...values, trimmed]);
    setDraft("");
  };

  const removeChip = (index) => {
    onChange(values.filter((_, i) => i !== index));
  };

  return (
    <div className="chip-field">
      <div className="chip-field-head">
        <span className="chip-field-label">{label}</span>
      </div>
      {values.length === 0 ? (
        <p className="chip-empty">None added.</p>
      ) : (
        <div className="chip-list">
          {values.map((value, index) => (
            <span key={`${value}-${index}`} className="chip">
              {value}
              <button
                type="button"
                className="chip-remove"
                onClick={() => removeChip(index)}
                aria-label={`Remove ${value}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="chip-input-row">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={placeholder}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addChip();
            }
          }}
        />
        <button type="button" className="secondary" onClick={addChip}>
          {addLabel}
        </button>
      </div>
    </div>
  );
}

function App() {
  const dispatch = useDispatch();
  const { interactions, status, error, editingId, chat, suggestions, suggestionsStatus } =
    useSelector((state) => state.interactions);

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
        interaction_type: record.interaction_type || "Meeting",
        interaction_date: record.interaction_date || "",
        interaction_time: record.interaction_time || "",
        attendees: record.attendees || [],
        materials_shared: record.materials_shared || [],
        samples_distributed: record.samples_distributed || [],
        sentiment: record.sentiment || "Neutral",
        outcomes: record.outcomes || "",
        follow_up_actions: record.follow_up_actions || "",
      });
    }
    dispatch(clearSuggestions());
  }, [editingId, interactions, dispatch]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = {
      ...formData,
      notes: formData.notes || formData.topic,
    };
    if (editingId) {
      dispatch(updateInteraction({ id: editingId, changes: payload }));
    } else {
      dispatch(submitInteraction(payload));
      setFormData(EMPTY_FORM);
    }
    dispatch(clearSuggestions());
  };

  const handleSuggest = () => {
    dispatch(
      suggestFollowUps({
        topic: formData.topic,
        notes: formData.topic,
        outcomes: formData.outcomes,
      }),
    );
  };

  const applySuggestion = (suggestion) => {
    setFormData((current) => ({
      ...current,
      follow_up_actions: current.follow_up_actions
        ? `${current.follow_up_actions}\n${suggestion}`
        : suggestion,
    }));
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
          <h1>Log HCP Interaction</h1>
          <p className="hero-copy">
            Field representatives can log structured updates or ask the
            LangGraph-powered assistant to manage the interaction workflow.
          </p>
        </div>
      </header>

      <main className="grid-layout">
        <section className="panel">
          <div className="panel-heading">
            <h2>Interaction Details</h2>
            <p>
              {editingId
                ? `Editing interaction #${editingId}.`
                : "Capture a new touchpoint that can be used later by the AI agent."}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="stack">
            <div className="field-row">
              <label>
                HCP Name
                <input
                  name="hcp_name"
                  value={formData.hcp_name}
                  onChange={handleChange}
                  placeholder="Search or select HCP..."
                  required
                />
              </label>
              <label>
                Interaction Type
                <select
                  name="interaction_type"
                  value={formData.interaction_type}
                  onChange={handleChange}
                >
                  <option value="Meeting">Meeting</option>
                  <option value="Call">Call</option>
                  <option value="Email">Email</option>
                  <option value="Conference">Conference</option>
                </select>
              </label>
            </div>

            <div className="field-row">
              <label>
                Date
                <input
                  type="date"
                  name="interaction_date"
                  value={formData.interaction_date}
                  onChange={handleChange}
                />
              </label>
              <label>
                Time
                <input
                  type="time"
                  name="interaction_time"
                  value={formData.interaction_time}
                  onChange={handleChange}
                />
              </label>
            </div>

            <ChipListField
              label="Attendees"
              placeholder="Enter name and press Add..."
              addLabel="Add"
              values={formData.attendees}
              onChange={(attendees) =>
                setFormData((current) => ({ ...current, attendees }))
              }
            />

            <label>
              Topics Discussed
              <textarea
                name="topic"
                rows="3"
                value={formData.topic}
                onChange={handleChange}
                placeholder="Enter key discussion points..."
                required
              />
            </label>

            <label>
              Notes / Summary
              <textarea
                name="notes"
                rows="3"
                value={formData.notes}
                onChange={handleChange}
                placeholder="Detailed notes or AI-generated summary (defaults to Topics Discussed if left blank)..."
              />
            </label>

            <div className="field-row">
              <ChipListField
                label="Materials Shared"
                placeholder="Search/add material..."
                addLabel="Search/Add"
                values={formData.materials_shared}
                onChange={(materials_shared) =>
                  setFormData((current) => ({ ...current, materials_shared }))
                }
              />
              <ChipListField
                label="Samples Distributed"
                placeholder="Add sample..."
                addLabel="Add Sample"
                values={formData.samples_distributed}
                onChange={(samples_distributed) =>
                  setFormData((current) => ({ ...current, samples_distributed }))
                }
              />
            </div>

            <div className="sentiment-field">
              <span className="chip-field-label">
                Observed/Inferred HCP Sentiment
              </span>
              <div className="sentiment-options">
                {SENTIMENTS.map(({ value, icon }) => (
                  <label key={value} className="sentiment-option">
                    <input
                      type="radio"
                      name="sentiment"
                      value={value}
                      checked={formData.sentiment === value}
                      onChange={handleChange}
                    />
                    <span>
                      {icon} {value}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <label>
              Outcomes
              <textarea
                name="outcomes"
                rows="2"
                value={formData.outcomes}
                onChange={handleChange}
                placeholder="Key outcomes or agreements..."
              />
            </label>

            <label>
              Follow-up Actions
              <textarea
                name="follow_up_actions"
                rows="2"
                value={formData.follow_up_actions}
                onChange={handleChange}
                placeholder="Enter next steps or tasks..."
              />
            </label>

            <div className="suggestions-box">
              <button
                type="button"
                className="secondary"
                onClick={handleSuggest}
                disabled={suggestionsStatus === "loading"}
              >
                {suggestionsStatus === "loading"
                  ? "Thinking..."
                  : "✨ AI Suggested Follow-ups"}
              </button>
              {suggestions.length > 0 ? (
                <ul className="suggestion-list">
                  {suggestions.map((s, idx) => (
                    <li key={idx}>
                      <button
                        type="button"
                        className="suggestion-item"
                        onClick={() => applySuggestion(s)}
                      >
                        + {s}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>

            <label>
              Channel
              <select name="channel" value={formData.channel} onChange={handleChange}>
                <option value="structured">Structured</option>
                <option value="chat">Chat</option>
                <option value="email">Email</option>
              </select>
            </label>
            <label>
              Status
              <select name="status" value={formData.status} onChange={handleChange}>
                <option value="Logged">Logged</option>
                <option value="Follow-up scheduled">Follow-up scheduled</option>
                <option value="Closed">Closed</option>
              </select>
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
            <h2>AI Assistant</h2>
            <p>
              Log interaction details here (e.g. “Met Dr. Smith, discussed
              Product X efficacy, positive sentiment, shared brochure”) or ask
              for help.
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

          <form onSubmit={handleChatSubmit} className="chat-input-row">
            <input
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              placeholder="Describe interaction..."
            />
            <button type="submit" disabled={chat.status === "loading"}>
              Log
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
