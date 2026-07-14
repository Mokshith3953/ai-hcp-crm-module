import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

// In dev, Vite proxies relative /api requests to the local backend (see
// vite.config.js). In production the frontend and backend are separate
// deployments, so VITE_API_BASE_URL points at the deployed backend's origin.
const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

const initialState = {
  interactions: [],
  status: "idle",
  error: null,
  editingId: null,
  chat: {
    threadId: null,
    messages: [],
    status: "idle",
    allTools: [],
  },
};

export const fetchInteractions = createAsyncThunk(
  "interactions/fetchInteractions",
  async () => {
    const response = await fetch(`${API_BASE}/api/interactions`);
    if (!response.ok) throw new Error("Failed to load interactions");
    return response.json();
  },
);

export const submitInteraction = createAsyncThunk(
  "interactions/submitInteraction",
  async (payload) => {
    const response = await fetch(`${API_BASE}/api/interactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Failed to save interaction");
    return response.json();
  },
);

export const updateInteraction = createAsyncThunk(
  "interactions/updateInteraction",
  async ({ id, changes }) => {
    const response = await fetch(`${API_BASE}/api/interactions/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(changes),
    });
    if (!response.ok) throw new Error("Failed to update interaction");
    return response.json();
  },
);

export const sendAgentMessage = createAsyncThunk(
  "interactions/sendAgentMessage",
  async (message, { getState }) => {
    const { threadId } = getState().interactions.chat;
    const response = await fetch(`${API_BASE}/api/agent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, thread_id: threadId }),
    });
    if (!response.ok) throw new Error("Failed to reach agent");
    return response.json();
  },
);

const interactionSlice = createSlice({
  name: "interactions",
  initialState,
  reducers: {
    startEditing(state, action) {
      state.editingId = action.payload;
    },
    cancelEditing(state) {
      state.editingId = null;
    },
    chatMessageSent(state, action) {
      state.chat.messages.push({ role: "user", content: action.payload });
      state.chat.status = "loading";
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.interactions = action.payload;
        state.status = "succeeded";
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(submitInteraction.fulfilled, (state, action) => {
        state.interactions.unshift(action.payload);
        state.status = "succeeded";
      })
      .addCase(submitInteraction.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const idx = state.interactions.findIndex(
          (item) => item.id === action.payload.id,
        );
        if (idx !== -1) state.interactions[idx] = action.payload;
        state.editingId = null;
        state.status = "succeeded";
      })
      .addCase(updateInteraction.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(sendAgentMessage.fulfilled, (state, action) => {
        const { reply, thread_id, tools_used, tools } = action.payload;
        state.chat.threadId = thread_id;
        state.chat.allTools = tools;
        state.chat.messages.push({
          role: "assistant",
          content: reply,
          toolsUsed: tools_used,
        });
        state.chat.status = "succeeded";
      })
      .addCase(sendAgentMessage.rejected, (state, action) => {
        state.chat.status = "failed";
        state.error = action.error.message;
        state.chat.messages.push({
          role: "assistant",
          content: "Sorry, the agent could not process that request.",
          toolsUsed: [],
        });
      });
  },
});

export const { startEditing, cancelEditing, chatMessageSent } =
  interactionSlice.actions;
export default interactionSlice.reducer;
