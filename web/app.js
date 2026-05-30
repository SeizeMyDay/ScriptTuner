const MAX_INPUT_CHARS = 4000;
const POLL_MS = 1200;

const scriptInput = document.querySelector("#scriptInput");
const counter = document.querySelector("#counter");
const convertButton = document.querySelector("#convertButton");
const convertLabel = document.querySelector("#convertLabel");
const clearButton = document.querySelector("#clearButton");
const copyButton = document.querySelector("#copyButton");
const resultBox = document.querySelector("#resultBox");
const statusText = document.querySelector("#statusText");
const serverPill = document.querySelector("#serverPill");
const elapsedText = document.querySelector("#elapsedText");
const tokenForm = document.querySelector("#tokenForm");
const tokenInput = document.querySelector("#tokenInput");

let modelReady = false;
let tuning = false;
let latestResult = "";
let awaitingToken = false;

function selectedStyle() {
  return document.querySelector("input[name='style']:checked").value;
}

function setButtonLoading(isLoading, label) {
  convertButton.classList.toggle("loading", isLoading);
  convertLabel.textContent = label;
}

function updateCounter() {
  counter.textContent = `${scriptInput.value.length} / ${MAX_INPUT_CHARS}`;
}

function updateConvertState() {
  const hasText = scriptInput.value.trim().length > 0;
  convertButton.disabled = !modelReady || !hasText || tuning;
  if (tuning) {
    setButtonLoading(true, "변환 중");
  } else if (awaitingToken) {
    setButtonLoading(false, "토큰 필요");
  } else if (!modelReady) {
    setButtonLoading(true, "모델 준비 중");
  } else {
    setButtonLoading(false, "변환");
  }
}

function setStatus(message, kind = "normal") {
  statusText.textContent = message || "";
  statusText.classList.toggle("error", kind === "error");
}

function setResult(text) {
  latestResult = text;
  copyButton.disabled = !text;
  if (!text) {
    resultBox.innerHTML = '<p class="empty-state">변환된 스크립트가 여기에 표시됩니다.</p>';
    return;
  }
  resultBox.textContent = text;
}

async function pollStatus() {
  try {
    const response = await fetch("/status", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const status = await response.json();
    const model = status.model || {};

    if (model.error) {
      modelReady = false;
      serverPill.textContent = "Model error";
      serverPill.className = "server-pill error";
      setStatus(model.error, "error");
      awaitingToken = false;
      tokenForm.hidden = true;
    } else if (model.stage === "awaiting_token") {
      modelReady = false;
      awaitingToken = true;
      tokenForm.hidden = false;
      serverPill.textContent = "Token required";
      serverPill.className = "server-pill";
      setStatus(`${model.message || "Enter Hugging Face token"} · ${model.progress || 5}%`);
    } else if (model.ready) {
      const wasReady = modelReady;
      modelReady = true;
      awaitingToken = false;
      tokenForm.hidden = true;
      serverPill.textContent = "Model ready";
      serverPill.className = "server-pill ready";
      setStatus(wasReady ? "" : "Model ready");
      if (!wasReady) setTimeout(() => setStatus(""), 1500);
    } else {
      modelReady = false;
      awaitingToken = false;
      tokenForm.hidden = true;
      serverPill.textContent = "Loading model";
      serverPill.className = "server-pill";
      const progress = Number.isFinite(model.progress) ? ` · ${model.progress}%` : "";
      setStatus(`${model.message || "Preparing model"}${progress}`);
    }
  } catch (error) {
    modelReady = false;
    serverPill.textContent = "Backend offline";
    serverPill.className = "server-pill error";
    setStatus("Local backend is not reachable.", "error");
  } finally {
    updateConvertState();
    window.setTimeout(pollStatus, POLL_MS);
  }
}

async function tuneScript() {
  const script = scriptInput.value.trim();
  if (!script || !modelReady || tuning) return;

  tuning = true;
  elapsedText.textContent = "";
  setStatus("Generating tuned script...");
  updateConvertState();

  try {
    const response = await fetch("/tune", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script, style: selectedStyle() }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    setResult(payload.tuned_script || "");
    elapsedText.textContent = payload.elapsed_seconds ? `${payload.elapsed_seconds}s` : "";
    setStatus("");
  } catch (error) {
    setStatus(error.message || String(error), "error");
  } finally {
    tuning = false;
    updateConvertState();
  }
}

async function copyResult() {
  if (!latestResult) return;
  try {
    await navigator.clipboard.writeText(latestResult);
    const previous = copyButton.textContent;
    copyButton.textContent = "복사됨";
    window.setTimeout(() => {
      copyButton.textContent = previous;
    }, 1200);
  } catch {
    setStatus("Clipboard permission was blocked.", "error");
  }
}

async function submitToken(event) {
  event.preventDefault();
  const token = tokenInput.value.trim();
  if (!token) {
    setStatus("Hugging Face token is required.", "error");
    return;
  }

  tokenInput.disabled = true;
  tokenForm.querySelector("button").disabled = true;
  setStatus("Saving Hugging Face token...");

  try {
    const response = await fetch("/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    tokenInput.value = "";
    tokenForm.hidden = true;
    awaitingToken = false;
    setStatus("Hugging Face token saved for this session · 8%");
  } catch (error) {
    setStatus(error.message || String(error), "error");
  } finally {
    tokenInput.disabled = false;
    tokenForm.querySelector("button").disabled = false;
    updateConvertState();
  }
}

scriptInput.addEventListener("input", () => {
  updateCounter();
  updateConvertState();
});

clearButton.addEventListener("click", () => {
  scriptInput.value = "";
  updateCounter();
  updateConvertState();
  scriptInput.focus();
});

convertButton.addEventListener("click", tuneScript);
copyButton.addEventListener("click", copyResult);
tokenForm.addEventListener("submit", submitToken);

updateCounter();
updateConvertState();
pollStatus();
