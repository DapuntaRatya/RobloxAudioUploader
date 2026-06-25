import { escapeHtml } from "./app.js";

export class DynamicList {
  constructor({ root, placeholder, bulkPlaceholder, addLabel = "Add" }) {
    this.root = root;
    this.placeholder = placeholder;
    this.bulkPlaceholder = bulkPlaceholder;
    this.addLabel = addLabel;
    this.items = [];
    this.render();
  }

  getValues() {
    return [...this.items];
  }

  add(value) {
    const clean = String(value || "").trim();
    if (!clean) return;
    if (!this.items.includes(clean)) this.items.push(clean);
    this.render();
  }

  addMany(value) {
    const values = String(value || "")
      .split(/\r?\n|,/)
      .map((item) => item.trim())
      .filter(Boolean);

    values.forEach((item) => this.add(item));
  }

  remove(index) {
    this.items.splice(index, 1);
    this.render();
  }

  render() {
    const listHtml = this.items.length
      ? this.items.map((item, index) => `
          <div class="list-item">
            <div class="item-index">${index + 1}</div>
            <div class="item-text">${escapeHtml(item)}</div>
            <button class="remove-button" type="button" data-index="${index}" title="Remove">×</button>
          </div>
        `).join("")
      : `<div class="empty-list">Belum ada data. Tambahkan lewat input di atas.</div>`;

    this.root.innerHTML = `
      <div class="dynamic-list">
        <div class="list-input-row">
          <input class="single-input" placeholder="${escapeHtml(this.placeholder)}">
          <button class="ghost-button add-button" type="button">${escapeHtml(this.addLabel)}</button>
        </div>

        <div class="bulk-box">
          <textarea class="bulk-input" rows="4" placeholder="${escapeHtml(this.bulkPlaceholder)}"></textarea>
          <div class="bulk-help">Tips: bisa paste banyak data sekaligus, pisahkan dengan enter atau koma.</div>
          <button class="ghost-button bulk-button" type="button">Add Many</button>
        </div>

        <div class="item-list">${listHtml}</div>
      </div>
    `;

    const singleInput = this.root.querySelector(".single-input");
    const addButton = this.root.querySelector(".add-button");
    const bulkInput = this.root.querySelector(".bulk-input");
    const bulkButton = this.root.querySelector(".bulk-button");

    addButton.addEventListener("click", () => {
      this.add(singleInput.value);
      singleInput.value = "";
      singleInput.focus();
    });

    singleInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        addButton.click();
      }
    });

    bulkButton.addEventListener("click", () => {
      this.addMany(bulkInput.value);
      bulkInput.value = "";
    });

    this.root.querySelectorAll(".remove-button").forEach((button) => {
      button.addEventListener("click", () => this.remove(Number(button.dataset.index)));
    });
  }
}
