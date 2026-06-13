import { useState, useRef, useEffect } from "react";
import CitationBadge from "./CitationBadge";

const API_URL = "http://localhost:8000";

const SUGGESTED_QUERIES = [
  "Do you have running shoes under ₹3000?",
  "What's the status of my order ORD-1002?",
  "What is your return policy?",
  "I'm buying a yoga mat, what else should I get?",
  "How long does express shipping take?",
];

// ── Single message bubble ─────────────────────────────────────────────────────
function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: "16px",
    }}>
      <div style={{
        maxWidth: "75%",
        backgroundColor: isUser ? "#3B82F6" : "#1F2937",
        color: isUser ? "#fff" : "#F9FAFB",
        borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
        padding: "12px 16px",
      }}>
        <p style={{ margin: 0, lineHeight: 1.6, fontSize: "14px" }}>{msg.content}</p>

        {/* Citation badges — which tool was used */}
        {msg.toolCalls && msg.toolCalls.length > 0 && (
          <div style={{ marginTop: "8px" }}>
            {msg.toolCalls.map((t, i) => <CitationBadge key={i} toolName={t} />)}
          </div>
        )}

        {/* Escalation warning */}
        {msg.escalate && (
          <p style={{ marginTop: "8px", fontSize: "12px", color: "#FCA5A5", margin: "8px 0 0" }}>
            ⚠ Escalated to human agent
          </p>
        )}
      </div>
    </div>
  );
}

// ── Typing indicator ──────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div style={{ display: "flex", gap: "6px", padding: "8px 0" }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: 8, height: 8, borderRadius: "50%", backgroundColor: "#6B7280",
          animation: `bounce 1s infinite ${i * 0.15}s`,
        }} />
      ))}
    </div>
  );
}

// ── Main ChatWindow component ─────────────────────────────────────────────────
export default function ChatWindow() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hi! I'm ShopMind 🛍️ Ask me about products, your orders, or our policies.",
      toolCalls: [],
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const bottomRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text) {
    const userMsg = text || input.trim();
    if (!userMsg || loading) return;

    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, session_id: sessionId }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.answer,
        toolCalls: data.tool_calls_made || [],
        escalate: data.escalate,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I couldn't connect to the server. Make sure the backend is running on port 8000.",
        toolCalls: [],
      }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, overflow: "hidden" }}>

      {/* Message list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Suggested queries — only shown before first user message */}
      {messages.length <= 1 && (
        <div style={{ padding: "0 24px 12px", display: "flex", flexWrap: "wrap", gap: "8px" }}>
          {SUGGESTED_QUERIES.map((q, i) => (
            <button key={i} onClick={() => sendMessage(q)} style={{
              padding: "6px 12px", borderRadius: "999px", fontSize: "12px",
              backgroundColor: "transparent", border: "1px solid #374151",
              color: "#9CA3AF", cursor: "pointer",
            }}>
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div style={{
        padding: "16px 24px", borderTop: "1px solid #374151",
        backgroundColor: "#1F2937", display: "flex", gap: "12px",
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && sendMessage()}
          placeholder="Ask about products, orders, or policies..."
          disabled={loading}
          style={{
            flex: 1, padding: "12px 16px", borderRadius: "12px",
            backgroundColor: "#374151", border: "1px solid #4B5563",
            color: "#F9FAFB", fontSize: "14px", outline: "none",
          }}
        />
        <button
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          style={{
            padding: "12px 20px", borderRadius: "12px", border: "none",
            backgroundColor: loading ? "#374151" : "#3B82F6",
            color: "#fff", cursor: loading ? "not-allowed" : "pointer",
            fontWeight: 600, fontSize: "14px",
          }}
        >
          Send
        </button>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  );
}