export class SourceSelector {
  constructor({ root, sources, selected = "youtube", onChange }) {
    this.root = root;
    this.sources = sources?.length ? sources : [
      { key: "youtube", label: "YouTube", enabled: true },
      { key: "soundcloud", label: "SoundCloud", enabled: true },
      { key: "spotify", label: "Spotify", enabled: false },
    ];
    this.selected = selected;
    this.onChange = onChange;
    this.render();
  }

  render() {
    this.root.innerHTML = `
      <div class="source-tabs">
        ${this.sources.map((source) => `
          <button
            class="source-tab ${source.key === this.selected ? "active" : ""}"
            type="button"
            data-source="${source.key}"
            ${source.enabled ? "" : "disabled"}
          >
            ${source.label}${source.enabled ? "" : " (soon)"}
          </button>
        `).join("")}
      </div>
    `;

    this.root.querySelectorAll(".source-tab").forEach((button) => {
      button.addEventListener("click", () => {
        const key = button.dataset.source;
        this.selected = key;
        this.onChange?.(key);
        this.render();
      });
    });
  }
}
