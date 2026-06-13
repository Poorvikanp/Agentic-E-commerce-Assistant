import ChatWindow from "./ChatWindow";

export default function App() {
  return (
    <div style={{
      display: "flex", flexDirection: "column", height: "100vh",
      backgroundColor: "#111827", fontFamily: "system-ui, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        padding: "16px 24px", borderBottom: "1px solid #374151",
        backgroundColor: "#1F2937", display: "flex", alignItems: "center", gap: "12px",
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: "50%",
          backgroundColor: "#3B82F6", display: "flex", alignItems: "center",
          justifyContent: "center", fontSize: "18px",
        }}>🛍️</div>
        <div>
          <div style={{ color: "#F9FAFB", fontWeight: 600, fontSize: "16px" }}>ShopMind</div>
          <div style={{ color: "#9CA3AF", fontSize: "12px" }}>AI Shopping Assistant · Powered by LangGraph</div>
        </div>
      </div>

      {/* Chat area */}
      <ChatWindow />
    </div>
  );
}