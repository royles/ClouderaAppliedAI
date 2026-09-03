import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchConfig,
  fetchHealth,
  fetchModels,
  sendChat,
  updateConfig,
} from "./api";
import "./App.css";

const REGIONS = [
  "us-east-1",
  "us-west-2",
  "eu-west-1",
  "eu-central-1",
  "ap-northeast-1",
  "ap-southeast-1",
];

export default function App() {
  const [models, setModels] = useState([]);
  const [config, setConfig] = useState(null);
  const [health, setHealth] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const loadInitialData = useCallback(async () => {
    try {
      const [modelsData, configData, healthData] = await Promise.all([
        fetchModels(),
        fetchConfig(),
        fetchHealth(),
      ]);
      setModels(modelsData);
      setConfig(configData);
      setHealth(healthData);
      setError(null);
    } catch (err) {
      setError(err.message || "Failed to connect to the API.");
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const handleModelChange = async (modelId) => {
    try {
      const updated = await updateConfig({ model_id: modelId });
      setConfig(updated);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRegionChange = async (region) => {
    try {
      const updated = await updateConfig({ aws_region: region });
      setConfig(updated);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMessage = { role: "user", content: trimmed };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await sendChat({
        messages: nextMessages,
        model_id: config?.model_id,
        system_prompt: systemPrompt.trim() || undefined,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.content },
      ]);
    } catch (err) {
      setError(err.message);
      // Remove the optimistic user message on failure so they can retry.
      setMessages(messages);
      setInput(trimmed);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const awsReady = health?.aws_configured;
  const apiReady = health?.status === "ok";

  return (
    <div className="app">
      <header className="header">
        <h1>Bedrock Playground</h1>
        <p>Experiment with AWS Bedrock models through a simple chat interface.</p>
      </header>

      <div className="status-bar">
        <span
          className={`status-dot ${apiReady ? "ok" : "error"}`}
          aria-hidden="true"
        />
        <span>
          API:{" "}
          <span className="status-label">
            {apiReady ? "Connected" : "Unavailable"}
          </span>
        </span>
        <span
          className={`status-dot ${awsReady ? "ok" : "warn"}`}
          aria-hidden="true"
        />
        <span>
          AWS:{" "}
          <span className="status-label">
            {awsReady ? "Configured" : "Not configured"}
          </span>
        </span>
        {config?.credential_source && (
          <span className="status-label mono">
            creds: {config.credential_source}
          </span>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="controls">
        <div className="control-group">
          <label htmlFor="model-select">Model</label>
          <select
            id="model-select"
            value={config?.model_id ?? ""}
            onChange={(e) => handleModelChange(e.target.value)}
            disabled={!models.length}
          >
            {models.map((m) => (
              <option key={m.model_id} value={m.model_id}>
                {m.display_name} ({m.provider})
              </option>
            ))}
          </select>
        </div>
        <div className="control-group">
          <label htmlFor="region-select">Region</label>
          <select
            id="region-select"
            value={config?.aws_region ?? "us-east-1"}
            onChange={(e) => handleRegionChange(e.target.value)}
          >
            {REGIONS.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="chat-area">
        <div className="messages">
          {messages.length === 0 && !loading && (
            <div className="empty-state">
              Send a message to start chatting with{" "}
              {config?.model_id?.split(".")[1] ?? "your selected model"}.
              {!awsReady && (
                <>
                  <br />
                  <br />
                  Configure AWS credentials on the backend to enable requests.
                </>
              )}
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <span className="message-role">{msg.role}</span>
              <div className="message-bubble">{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <span className="message-role">assistant</span>
              <div className="message-bubble loading-dots">Thinking</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <button
            type="button"
            className="system-prompt-toggle"
            onClick={() => setShowSystemPrompt((v) => !v)}
          >
            {showSystemPrompt ? "− Hide system prompt" : "+ System prompt (optional)"}
          </button>
          {showSystemPrompt && (
            <textarea
              className="system-prompt-input"
              placeholder="Set behavior instructions for the model..."
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={2}
            />
          )}
          <div className="input-row">
            <textarea
              ref={inputRef}
              className="prompt-input"
              placeholder={
                awsReady
                  ? "Type a message… (Enter to send, Shift+Enter for newline)"
                  : "Configure AWS credentials on the backend first"
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading || !awsReady}
              rows={1}
            />
            <button
              type="button"
              className="send-btn"
              onClick={handleSend}
              disabled={loading || !input.trim() || !awsReady}
            >
              {loading ? "…" : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
