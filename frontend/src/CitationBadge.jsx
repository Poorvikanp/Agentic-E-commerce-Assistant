// CitationBadge.jsx — shows which tool was used to answer the query
export default function CitationBadge({ toolName }) {
  const config = {
    search_products:  { label: "Product catalog", color: "#3B82F6" },
    check_order:      { label: "Order DB",         color: "#10B981" },
    get_policy:       { label: "Store policy",     color: "#8B5CF6" },
    recommend_bundle: { label: "Bundle logic",     color: "#F59E0B" },
  };

  const { label, color } = config[toolName] || { label: toolName, color: "#6B7280" };

  return (
    <span style={{
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: "999px",
      fontSize: "11px",
      fontWeight: 500,
      backgroundColor: color + "20",
      color: color,
      border: `1px solid ${color}40`,
      marginRight: "4px",
      marginTop: "4px",
    }}>
      {label}
    </span>
  );
}