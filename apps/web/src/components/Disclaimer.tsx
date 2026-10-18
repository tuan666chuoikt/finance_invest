// Literal in both languages on purpose (ux/app-shell.md "Disclaimer banner"): never translated, never dismissible.
export function Disclaimer() {
  return (
    <aside role="note" data-testid="disclaimer" style={{ padding: "8px 16px", background: "#fff8e1", fontSize: 14 }}>
      <span style={{ display: "inline-block" }}>Mô phỏng để học, không phải lời khuyên đầu tư</span>
      <span aria-hidden="true"> · </span>
      <span style={{ display: "inline-block" }}>Educational simulation, not investment advice</span>
    </aside>
  );
}
