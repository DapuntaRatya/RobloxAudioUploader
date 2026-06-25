export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function nowEvent(type, level, message, data = null) {
  return {
    type,
    level,
    message,
    data,
    created_at: new Date().toISOString(),
  };
}
