import { getJson, postJson } from "./api.js";
import { appState } from "./state.js";
import { escapeHtml, nowEvent } from "./app.js";
import { SourceSelector } from "./components/source-selector.js";
import { ProfileMenu } from "./components/profile-menu.js";
import { createAudioList } from "./components/audio-list.js";
import { createExperienceList } from "./components/experience-list.js";
import { ResultLog } from "./components/result-log.js";
import { UploadStream } from "./upload-stream.js";

const sourceSelectorRoot = document.getElementById("sourceSelector");
const audioListRoot = document.getElementById("audioList");
const experienceListRoot = document.getElementById("experienceList");
const startUploadButton = document.getElementById("startUploadButton");
const clearResultButton = document.getElementById("clearResultButton");
const clearUploadedButton = document.getElementById("clearUploadedButton");
const demoFillButton = document.getElementById("demoFillButton");
const parallelCheck = document.getElementById("parallelCheck");
const permissionCheck = document.getElementById("permissionCheck");
const progressList = document.getElementById("progressList");
const uploadedAssetsList = document.getElementById("uploadedAssetsList");

const resultLog = new ResultLog(document.getElementById("resultLog"));
let audioList = null;
let experienceList = null;

const progressState = new Map();
const uploadedAssets = new Map();

function audioNumberFromItemId(itemId) {
  const value = String(itemId || "");
  const match = value.match(/audio_(\d+)$/);
  return match ? Number(match[1]) : progressState.size + 1;
}

function ensureProgress(itemId, url = "") {
  if (!progressState.has(itemId)) {
    progressState.set(itemId, {
      itemId,
      index: audioNumberFromItemId(itemId),
      url,
      title: "-",
      stage: "Menunggu",
      percent: 0,
      status: "running",
    });
  }
  return progressState.get(itemId);
}

function setProgress(itemId, patch) {
  const item = ensureProgress(itemId, patch.url || "");
  Object.assign(item, patch);
  renderProgress();
}

function renderProgress() {
  const items = [...progressState.values()].sort((a, b) => a.index - b.index);

  if (!items.length) {
    progressList.innerHTML = `<div class="progress-empty">Belum ada progress. Klik Start Upload untuk mulai.</div>`;
    return;
  }

  progressList.innerHTML = items.map((item) => {
    const percent = Math.max(0, Math.min(100, Number(item.percent || 0)));
    const className = item.status === "failed" ? "failed" : item.status === "done" ? "done" : "";

    return `
      <div class="progress-item ${className}">
        <div class="progress-top">
          <div>
            <div class="progress-audio-name">Audio ${item.index}</div>
            <div class="progress-title"><strong>Judul:</strong> ${escapeHtml(item.title || item.url || "-")}</div>
          </div>
          <div class="progress-percent">${percent}%</div>
        </div>

        <div class="progress-stage">
          <span>Proses ${escapeHtml(item.stage || "Menunggu")}</span>
          <span>${escapeHtml(item.status || "running")}</span>
        </div>

        <div class="progress-bar">
          <div class="progress-bar-fill" style="width: ${percent}%"></div>
        </div>
      </div>
    `;
  }).join("");
}

function assetUrl(assetId) {
  return `https://create.roblox.com/store/asset/${assetId}`;
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

  setTimeout(() => toast.remove(), 1400);
}

function addUploadedAsset({ assetId, title, itemId, createdAt }) {
  if (!assetId) return;

  uploadedAssets.set(String(assetId), {
    assetId: String(assetId),
    title: title || "Untitled Audio",
    itemId,
    createdAt: createdAt || new Date().toISOString(),
  });

  renderUploadedAssets();
}

function renderUploadedAssets() {
  const assets = [...uploadedAssets.values()].reverse();

  if (!assets.length) {
    uploadedAssetsList.innerHTML = `<div class="assets-empty">Belum ada asset yang berhasil diupload pada sesi ini.</div>`;
    return;
  }

  uploadedAssetsList.innerHTML = assets.map((asset) => `
    <article class="asset-card" data-asset-id="${escapeHtml(asset.assetId)}">
      <div class="asset-title">${escapeHtml(asset.title)}</div>
      <div class="asset-meta">
        <span class="asset-id-pill">Asset ID: ${escapeHtml(asset.assetId)}</span>
        <span>${asset.createdAt ? escapeHtml(new Date(asset.createdAt).toLocaleTimeString()) : ""}</span>
      </div>
      <div class="asset-actions">
        <button class="ghost-button copy-id-button" type="button" data-copy="${escapeHtml(asset.assetId)}">Copy ID</button>
        <button class="ghost-button copy-title-button" type="button" data-copy="${escapeHtml(asset.title)}">Copy Judul</button>
        <button class="ghost-button open-asset-button" type="button" data-open="${escapeHtml(asset.assetId)}">Open Asset</button>
      </div>
    </article>
  `).join("");

  uploadedAssetsList.querySelectorAll(".asset-card").forEach((card) => {
    card.addEventListener("click", () => {
      window.open(assetUrl(card.dataset.assetId), "_blank", "noopener,noreferrer");
    });
  });

  uploadedAssetsList.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();

      if (button.dataset.open) {
        window.open(assetUrl(button.dataset.open), "_blank", "noopener,noreferrer");
        return;
      }

      if (button.dataset.copy) {
        copyText(button.dataset.copy, button.classList.contains("copy-id-button") ? "Asset ID copied" : "Judul copied");
      }
    });
  });
}

function handleProgressEvent(event) {
  const itemId = event.item_id;
  if (!itemId) return;

  if (event.type === "item_started") {
    setProgress(itemId, {
      url: event.data?.url,
      stage: "Persiapan",
      percent: 5,
      status: "running",
    });
  }

  if (event.type === "download_started") {
    setProgress(itemId, {
      url: event.data?.url,
      stage: "Download",
      percent: 15,
      status: "running",
    });
  }

  if (event.type === "download_done") {
    setProgress(itemId, {
      title: event.data?.title || "-",
      stage: "Download Selesai",
      percent: 35,
      status: "running",
    });
  }

  if (event.type === "upload_started") {
    setProgress(itemId, {
      title: event.data?.display_name || ensureProgress(itemId).title,
      stage: "Upload",
      percent: 55,
      status: "running",
    });
  }

  if (event.type === "operation_polling") {
    setProgress(itemId, {
      stage: "Moderasi / Processing",
      percent: 75,
      status: "running",
    });
  }

  if (event.type === "upload_done") {
    const item = ensureProgress(itemId);
    setProgress(itemId, {
      stage: "Upload Selesai",
      percent: 90,
      status: "running",
    });

    addUploadedAsset({
      assetId: event.data?.asset_id,
      title: item.title || event.data?.display_name || "Untitled Audio",
      itemId,
      createdAt: event.created_at,
    });
  }

  if (event.type === "permission_started") {
    setProgress(itemId, {
      stage: "Grant Permission",
      percent: 95,
      status: "running",
    });
  }

  if (event.type === "permission_done") {
    setProgress(itemId, {
      stage: "Permission Selesai",
      percent: 100,
      status: "done",
    });
  }

  if (event.type === "item_done") {
    setProgress(itemId, {
      stage: "Selesai",
      percent: 100,
      status: "done",
    });
  }

  if (event.type === "item_failed") {
    setProgress(itemId, {
      stage: "Gagal",
      percent: 100,
      status: "failed",
    });
  }
}

async function boot() {
  renderProgress();
  renderUploadedAssets();

  audioList = createAudioList(audioListRoot);
  experienceList = createExperienceList(experienceListRoot);

  try {
    appState.session = await getJson("/api/session");
    new ProfileMenu({ session: appState.session });
  } catch (error) {
    window.location.href = "/login";
    return;
  }

  let sources = [
    { key: "youtube", label: "YouTube", enabled: true },
    { key: "soundcloud", label: "SoundCloud", enabled: true },
    { key: "spotify", label: "Spotify", enabled: false },
  ];

  try {
    const sourcesResponse = await getJson("/api/sources");
    if (sourcesResponse.sources?.length) sources = sourcesResponse.sources;
  } catch (error) {
    resultLog.add(nowEvent("sources_warning", "warning", "Gagal membaca source dari backend. Memakai fallback source.", error.payload || error.message));
  }

  new SourceSelector({
    root: sourceSelectorRoot,
    sources,
    selected: appState.selectedSource,
    onChange: (key) => appState.selectedSource = key,
  });
}

async function startUpload() {
  const audioLinks = audioList.getValues();
  const experienceIds = experienceList.getValues();

  if (!audioLinks.length) {
    resultLog.add(nowEvent("validation", "error", "Minimal masukkan 1 link audio."));
    return;
  }

  if (permissionCheck.checked && !experienceIds.length) {
    resultLog.add(nowEvent("validation", "error", "Minimal masukkan 1 experience ID jika grant permission aktif."));
    return;
  }

  progressState.clear();
  uploadedAssets.clear();
  renderProgress();
  renderUploadedAssets();

  startUploadButton.disabled = true;
  startUploadButton.textContent = "Queued...";

  try {
    const response = await postJson("/api/upload", {
      source_type: appState.selectedSource,
      audio_links: audioLinks,
      experience_ids: experienceIds,
      options: {
        parallel: parallelCheck.checked,
        grant_permission: permissionCheck.checked,
        cleanup_temp: true,
      },
    });

    resultLog.add(nowEvent("job_queued", "success", `Job masuk queue: ${response.job_id}`, response));

    if (appState.activeStream) appState.activeStream.close();

    appState.activeStream = new UploadStream({
      streamUrl: response.stream_url,
      onEvent: (event) => {
        resultLog.add(event);
        handleProgressEvent(event);
      },
      onClose: () => {
        startUploadButton.disabled = false;
        startUploadButton.textContent = "Start Upload";
      },
      onError: () => {
        resultLog.add(nowEvent("stream_error", "warning", "Stream error/reconnect. Kalau job masih berjalan, browser akan mencoba reconnect."));
      },
    });

    appState.activeStream.start();
  } catch (error) {
    resultLog.add(nowEvent("request_failed", "error", error.message, error.payload || null));
    startUploadButton.disabled = false;
    startUploadButton.textContent = "Start Upload";
  }
}

startUploadButton.addEventListener("click", startUpload);
clearResultButton.addEventListener("click", () => resultLog.clear());
clearUploadedButton.addEventListener("click", () => {
  uploadedAssets.clear();
  renderUploadedAssets();
});

demoFillButton.addEventListener("click", () => {
  audioList.add("https://youtu.be/nLu_3C3nc0w");
  experienceList.add("9711918317");
  resultLog.add(nowEvent("demo_fill", "success", "Demo data ditambahkan. Ganti dengan link dan experience asli."));
});

boot().catch((error) => {
  resultLog.add(nowEvent("boot_failed", "error", "Dashboard gagal dimuat.", error.message));
});
