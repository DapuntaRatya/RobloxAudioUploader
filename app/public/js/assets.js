import { getJson, postJson } from "./api.js";
import { escapeHtml } from "./app.js";

const tableBody = document.getElementById("assetsTableBody");
const refreshButton = document.getElementById("refreshAssetsButton");
const filterType = document.getElementById("filterType");
const selectToggleButton = document.getElementById("selectToggleButton");
const selectionCount = document.getElementById("selectionCount");
const assetsNote = document.getElementById("assetsNote");
const grantExperienceInput = document.getElementById("grantExperienceInput");
const grantAssetCount = document.getElementById("grantAssetCount");
const grantExperienceCount = document.getElementById("grantExperienceCount");
const grantButton = document.getElementById("grantButton");
const grantResultList = document.getElementById("grantResultList");
const clearGrantResultButton = document.getElementById("clearGrantResultButton");

let allAssets = [];
let filteredAssets = [];
let selectedAssetIds = new Set();

function assetUrl(assetId) {
  return `https://create.roblox.com/store/asset/${assetId}`;
}

function parseDate(value) {
  if (!value) return 0;
  const time = Date.parse(value);
  return Number.isFinite(time) ? time : 0;
}

function parseLength(value) {
  if (value === null || value === undefined || value === "") return -1;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : -1;
}

function getRadioValue(name) {
  return document.querySelector(`input[name="${name}"]:checked`)?.value || "";
}

function getExperienceIds() {
  return grantExperienceInput.value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item, index, arr) => arr.indexOf(item) === index);
}

function cssStatus(value) {
  return String(value || "unknown").toLowerCase().replaceAll("_", "-").replaceAll(" ", "-");
}

function allFilteredSelected() {
  if (!filteredAssets.length) return false;
  return filteredAssets.every((asset) => selectedAssetIds.has(String(asset.asset_id)));
}

function updateSelectionUi() {
  const selectedCount = selectedAssetIds.size;
  const filteredCount = filteredAssets.length;
  const isAllFilteredSelected = allFilteredSelected();

  selectionCount.textContent = `${selectedCount} selected`;
  grantAssetCount.textContent = String(selectedCount);
  grantExperienceCount.textContent = String(getExperienceIds().length);

  selectToggleButton.disabled = filteredCount === 0;
  selectToggleButton.classList.toggle("unselect-mode", isAllFilteredSelected);
  selectToggleButton.classList.toggle("select-mode", !isAllFilteredSelected);
  selectToggleButton.textContent = isAllFilteredSelected ? "Unselect all" : "Select all";
}

function applyFilters() {
  const type = filterType.value;
  const sortTime = getRadioValue("sortTime");
  const sortTitle = getRadioValue("sortTitle");
  const sortLength = getRadioValue("sortLength");

  filteredAssets = allAssets.filter((asset) => {
    if (type === "all") return true;
    if (type === "can_played") return Boolean(asset.can_played);
    if (type === "archived") return Boolean(asset.is_archived);
    if (type === "blocked") return Boolean(asset.is_blocked);
    return true;
  });

  filteredAssets.sort((a, b) => {
    if (sortTitle) {
      const result = String(a.title || "").localeCompare(String(b.title || ""));
      if (result !== 0) return sortTitle === "ascending" ? result : -result;
    }

    if (sortLength) {
      const result = parseLength(a.length_seconds) - parseLength(b.length_seconds);
      if (result !== 0) return sortLength === "ascending" ? result : -result;
    }

    const result = parseDate(a.created_time) - parseDate(b.created_time);
    return sortTime === "ascending" ? result : -result;
  });

  renderTable();
  updateSelectionUi();
}

async function copyText(value, label = "Copied") {
  try {
    await navigator.clipboard.writeText(String(value));
    showToast(label);
  } catch {
    showToast("Gagal copy");
  }
}

function showToast(message) {
  const old = document.querySelector(".copy-toast");
  if (old) old.remove();

  const toast = document.createElement("div");
  toast.className = "copy-toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 1200);
}

function renderTable() {
  if (!filteredAssets.length) {
    tableBody.innerHTML = `<tr><td colspan="10"><div class="assets-empty">Tidak ada asset sesuai filter.</div></td></tr>`;
    return;
  }

  tableBody.innerHTML = filteredAssets.map((asset) => {
    const assetId = String(asset.asset_id);
    const checked = selectedAssetIds.has(assetId) ? "checked" : "";
    const created = asset.created_time ? new Date(asset.created_time).toLocaleString() : "-";
    const storeYes = Boolean(asset.on_creator_store);
    const moderationState = asset.moderation_state || "Unknown";
    const assetState = asset.asset_state || "Unknown";
    const title = asset.title || asset.display_name || "Untitled Audio";

    return `
      <tr data-asset-id="${escapeHtml(assetId)}">
        <td>
          <input class="asset-check" type="checkbox" data-asset-id="${escapeHtml(assetId)}" ${checked}>
        </td>
        <td class="asset-id-cell" title="${escapeHtml(assetId)}">${escapeHtml(assetId)}</td>
        <td>
          <a class="asset-title-link" title="${escapeHtml(title)}" href="${escapeHtml(asset.asset_url || assetUrl(assetId))}" target="_blank" rel="noreferrer">
            ${escapeHtml(title)}
          </a>
        </td>
        <td>
          <div class="asset-desc-cell" title="${escapeHtml(asset.description || "-")}">${escapeHtml(asset.description || "-")}</div>
        </td>
        <td>${escapeHtml(asset.length || "-")}</td>
        <td class="asset-created-cell">${escapeHtml(created)}</td>
        <td>
          <span class="status-badge ${escapeHtml(cssStatus(moderationState))}">
            ${escapeHtml(moderationState)}
          </span>
        </td>
        <td>
          <span class="status-badge ${escapeHtml(cssStatus(assetState))}">
            ${escapeHtml(assetState)}
          </span>
        </td>
        <td>
          <span class="store-badge ${storeYes ? "yes" : ""}">
            ${storeYes ? "Yes" : escapeHtml(asset.on_creator_store_label || "No")}
          </span>
        </td>
        <td>
          <button class="copy-mini copy-id" data-copy="${escapeHtml(assetId)}" type="button">ID</button>
          <button class="copy-mini copy-title" data-copy="${escapeHtml(title)}" type="button">Title</button>
          <button class="copy-mini open-asset" data-open="${escapeHtml(assetId)}" type="button">Open</button>
        </td>
      </tr>
    `;
  }).join("");

  tableBody.querySelectorAll(".asset-check").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const id = checkbox.dataset.assetId;
      if (checkbox.checked) selectedAssetIds.add(id);
      else selectedAssetIds.delete(id);
      updateSelectionUi();
    });
  });

  tableBody.querySelectorAll(".copy-id").forEach((button) => {
    button.addEventListener("click", () => copyText(button.dataset.copy, "Asset ID copied"));
  });

  tableBody.querySelectorAll(".copy-title").forEach((button) => {
    button.addEventListener("click", () => copyText(button.dataset.copy, "Title copied"));
  });

  tableBody.querySelectorAll(".open-asset").forEach((button) => {
    button.addEventListener("click", () => {
      window.open(assetUrl(button.dataset.open), "_blank", "noopener,noreferrer");
    });
  });
}

async function loadAssets() {
  tableBody.innerHTML = `<tr><td colspan="10"><div class="assets-empty">Loading assets...</div></td></tr>`;
  refreshButton.disabled = true;
  refreshButton.textContent = "Refreshing";

  try {
    const data = await getJson("/api/assets");
    allAssets = data.assets || [];
    assetsNote.textContent = data.note || "";
    selectedAssetIds = new Set([...selectedAssetIds].filter((id) => allAssets.some((asset) => String(asset.asset_id) === id)));
    applyFilters();
  } catch (error) {
    if (error.payload?.error?.code === "UNAUTHENTICATED") {
      window.location.href = "/login";
      return;
    }

    tableBody.innerHTML = `<tr><td colspan="10"><div class="assets-empty">Gagal load assets: ${escapeHtml(error.message)}</div></td></tr>`;
  } finally {
    refreshButton.disabled = false;
    refreshButton.textContent = "Refresh";
  }
}

function renderGrantResults(results, summary = null) {
  if (!results?.length) {
    grantResultList.innerHTML = `<div class="assets-empty">Tidak ada result.</div>`;
    return;
  }

  const summaryHtml = summary
    ? `<div class="grant-result-item">
        <strong>Summary</strong>
        <div>Success: ${summary.success_count} | Failed: ${summary.failed_count}</div>
      </div>`
    : "";

  grantResultList.innerHTML = summaryHtml + results.map((item) => `
    <div class="grant-result-item ${escapeHtml(item.status)}">
      <strong>${escapeHtml(item.status === "success" ? "Berhasil" : "Gagal")} - Asset ${escapeHtml(item.asset_id)} - Experience ${escapeHtml(item.universe_id)}</strong>
      <div>${escapeHtml(item.message || "-")}</div>
      ${item.details ? `<pre>${escapeHtml(JSON.stringify(item.details))}</pre>` : ""}
    </div>
  `).join("");
}

async function grantSelectedAssets() {
  const assetIds = [...selectedAssetIds];
  const experienceIds = getExperienceIds();

  if (!assetIds.length) {
    showToast("Pilih minimal 1 asset");
    return;
  }

  if (!experienceIds.length) {
    showToast("Isi minimal 1 experience");
    return;
  }

  grantButton.disabled = true;
  grantButton.textContent = "Granting";
  grantResultList.innerHTML = `<div class="assets-empty">Processing grant...</div>`;

  try {
    const data = await postJson("/api/assets/grant", {
      asset_ids: assetIds,
      experience_ids: experienceIds,
    });

    renderGrantResults(data.results || [], data);
  } catch (error) {
    grantResultList.innerHTML = `
      <div class="grant-result-item failed">
        <strong>Grant request gagal</strong>
        <div>${escapeHtml(error.message)}</div>
        ${error.payload ? `<pre>${escapeHtml(JSON.stringify(error.payload))}</pre>` : ""}
      </div>
    `;
  } finally {
    grantButton.disabled = false;
    grantButton.textContent = "Grant Selected";
  }
}

refreshButton.addEventListener("click", loadAssets);
filterType.addEventListener("change", applyFilters);

document.querySelectorAll('input[name="sortTime"], input[name="sortTitle"], input[name="sortLength"]').forEach((input) => {
  input.addEventListener("change", applyFilters);
});

selectToggleButton.addEventListener("click", () => {
  if (allFilteredSelected()) {
    filteredAssets.forEach((asset) => selectedAssetIds.delete(String(asset.asset_id)));
  } else {
    filteredAssets.forEach((asset) => selectedAssetIds.add(String(asset.asset_id)));
  }

  renderTable();
  updateSelectionUi();
});

grantExperienceInput.addEventListener("input", updateSelectionUi);
grantButton.addEventListener("click", grantSelectedAssets);

clearGrantResultButton.addEventListener("click", () => {
  grantResultList.innerHTML = `<div class="assets-empty">Belum ada proses grant.</div>`;
});

loadAssets();
