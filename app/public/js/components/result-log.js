import { escapeHtml } from "../app.js";

export class ResultLog {
  constructor(root) {
    this.root = root;
    this.entries = [];
    this.render();
  }

  clear() {
    this.entries = [];
    this.render();
  }

  add(event) {
    this.entries.push(event);
    this.render();
    this.root.scrollTop = this.root.scrollHeight;
  }

  render() {
    if (!this.entries.length) {
      this.root.innerHTML = `
        <div class="result-entry">
          <strong>Belum ada proses berjalan.</strong>
          <small>Setelah klik Start Upload, semua progress akan muncul di sini.</small>
        </div>
      `;
      return;
    }

    this.root.innerHTML = this.entries.map((entry) => {
      const level = entry.level || "info";
      const time = entry.created_at ? new Date(entry.created_at).toLocaleTimeString() : "";
      const data = entry.data ? JSON.stringify(entry.data) : "";

      return `
        <div class="result-entry ${escapeHtml(level)}">
          <strong>${escapeHtml(entry.message || entry.type)}</strong>
          <small>${escapeHtml(entry.type || "event")}${time ? " • " + escapeHtml(time) : ""}</small>
          ${data ? `<div class="result-data">${escapeHtml(data)}</div>` : ""}
        </div>
      `;
    }).join("");
  }
}
