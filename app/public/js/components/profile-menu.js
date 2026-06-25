import { postJson } from "../api.js";

export class ProfileMenu {
  constructor({ session }) {
    this.session = session || {};
    this.profileButton = document.getElementById("profileButton");
    this.sidebar = document.getElementById("profileSidebar");
    this.profileInitial = document.getElementById("profileInitial");
    this.profileInitialLarge = document.getElementById("profileInitialLarge");
    this.profileUserId = document.getElementById("profileUserId");
    this.profileKeyName = document.getElementById("profileKeyName");
    this.viewApiKeyButton = document.getElementById("viewApiKeyButton");
    this.apiKeyView = document.getElementById("apiKeyView");
    this.viewUploadedAssetsButton = document.getElementById("viewUploadedAssetsButton");
    this.logoutButton = document.getElementById("logoutButton");
    this.render();
    this.bind();
  }

  render() {
    const userId = this.session?.authorized_user_id || "-";
    const keyName = this.session?.api_key_name || "-";
    const initial = String(userId).slice(0, 1) || "R";
    this.profileInitial.textContent = initial;
    this.profileInitialLarge.textContent = initial;
    this.profileUserId.textContent = `User ID: ${userId}`;
    this.profileKeyName.textContent = keyName;
    this.apiKeyView.textContent = this.session?.api_key_masked || "-";
  }

  bind() {
    this.profileButton.addEventListener("click", (event) => {
      event.stopPropagation();
      this.sidebar.classList.toggle("hidden");
    });

    this.viewApiKeyButton.addEventListener("click", () => {
      this.apiKeyView.classList.toggle("hidden");
    });

    this.viewUploadedAssetsButton?.addEventListener("click", () => {
      window.location.href = "/assets";
    });

    this.logoutButton.addEventListener("click", async () => {
      await postJson("/api/logout", {});
      window.location.href = "/login";
    });

    document.addEventListener("click", (event) => {
      const root = document.getElementById("profileMenuRoot");
      if (!root.contains(event.target)) this.sidebar.classList.add("hidden");
    });
  }
}
