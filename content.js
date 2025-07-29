console.log("✅ MindTrace content script loaded");

let keyTimes = [];
let lastKeyTime = null;

function getPlatform() {
  const url = window.location.href;
  if (url.includes("whatsapp")) return "WhatsApp";
  if (url.includes("instagram")) return "Instagram";
  if (url.includes("facebook")) return "Facebook";
  if (url.includes("twitter")) return "Twitter";
  if (url.includes("linkedin")) return "LinkedIn";
  return "Unknown";
}

// 🔔 Popup alert
function showAlert(msg) {
  const div = document.createElement("div");
  div.innerText = msg;
  div.style = `
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 9999;
    background: yellow;
    color: black;
    padding: 12px;
    border: 2px solid black;
    border-radius: 8px;
    font-weight: bold;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
  `;
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 6000);
}

// 🚫 Block risky input
function blockInputBox(input) {
  if (!input) return;

  input.value = "⚠️ Message blocked by MindTrace";
  input.disabled = true;
  input.style.border = "2px solid red";
  input.style.background = "#ffe6e6";
  input.style.color = "#000";
  input.style.fontWeight = "bold";
  input.classList.add("blocked");

  const lock = document.createElement("span");
  lock.innerText = "🔒";
  lock.style.marginLeft = "8px";
  lock.style.color = "red";
  input.parentElement?.appendChild(lock);
}

// 🧠 Risk analysis using selected model
function analyzeMessageRisk(text, inputBox) {
  chrome.storage.local.get("selectedModel", (data) => {
    const model = data.selectedModel || "nb";

    fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, model })
    })
      .then(res => res.json())
      .then(data => {
        const label = data.label;
        const confidence = data.confidence;
        const shouldBlock = data.block;

        console.log("🧠 NLP Result:", data);

        if (["honeytrap", "jobfraud", "scam"].includes(label)) {
          showAlert(`⚠️ ${label.toUpperCase()} detected\nConfidence: ${confidence}`);
          if (shouldBlock && inputBox) {
            blockInputBox(inputBox);
          }
        }
      })
      .catch(err => console.error("❌ Risk analysis failed:", err));
  });
}

// ⌨️ Typing speed detection
document.addEventListener("keydown", (e) => {
  const input = e.target;
  if (!input || input.classList?.contains("blocked")) return;

  const now = Date.now();
  if (lastKeyTime !== null) keyTimes.push(now - lastKeyTime);
  lastKeyTime = now;

  if (keyTimes.length >= 10) {
    const avgSpeed = keyTimes.reduce((a, b) => a + b, 0) / keyTimes.length;
    sendTypingSpeed(avgSpeed);
    keyTimes = [];
    lastKeyTime = null;
  }
});

// 📋 Paste triggers NLP
document.addEventListener("paste", (e) => {
  const input = e.target;
  const pasted = (e.clipboardData || window.clipboardData).getData("text");
  console.log("📋 Pasted:", pasted);
  analyzeMessageRisk(pasted, input);
});

// 🧠 Send typing speed to local server
function sendTypingSpeed(speed) {
  fetch("http://localhost:3000/typing-speed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ platform: getPlatform(), speed: speed })
  })
    .then(res => res.json())
    .then(data => {
      if (data.thiefDetected) {
        showAlert("⚠️ Suspicious typing behavior detected!");
      }
    })
    .catch(err => console.error("❌ Typing Speed Error:", err));
}
