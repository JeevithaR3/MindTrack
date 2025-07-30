console.log("✅ MindTrace content script loaded");

let keyTimes = [];
let lastKeyTime = null;

const blockedContacts = new Map();
const suspiciousCounts = new Map();
const permanentlyBlocked = new Set();

// 🔍 Identify platform
function getPlatform() {
  const url = window.location.href;
  if (url.includes("whatsapp")) return "WhatsApp";
  if (url.includes("instagram")) return "Instagram";
  if (url.includes("facebook")) return "Facebook";
  if (url.includes("twitter")) return "Twitter";
  if (url.includes("linkedin")) return "LinkedIn";
  return "Unknown";
}

// 🔎 Extract contact name from DOM
function getActiveContact(input) {
  const container = input.closest(".contact");
  return container ? container.getAttribute("data-contact") : "Unknown";
}

// 🧠 Determine if it's an unsaved contact
function isUnsavedContact(name) {
  if (!name || name === "Unknown") return true;
  return /^\+?\d+$/.test(name);  // purely digits or +91...
}

// 📊 Define suspicious threshold
function getAlertLimit(contact) {
  return isUnsavedContact(contact) ? 1 : 3;
}

// 🔔 Show visual alert
function showAlert(msg, contact = "Unknown") {
  const count = suspiciousCounts.get(contact) || 0;
  const limit = getAlertLimit(contact);
  if (count >= limit) {
    console.log(`🚫 No alert — limit (${limit}) reached for ${contact}`);
    return;
  }

  suspiciousCounts.set(contact, count + 1);

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

// 🔒 Lock input box
function blockInputBox(input) {
  if (!input) return;

  const contact = getActiveContact(input);
  if (permanentlyBlocked.has(contact)) return;

  blockedContacts.set(contact, true);
  permanentlyBlocked.add(contact);

  input.innerText = "⚠️ Blocked by MindTrace";
  input.setAttribute("contenteditable", "false");
  input.classList.add("blocked");
  input.style.pointerEvents = "none";
  input.style.border = "2px solid red";
  input.style.background = "#ffe6e6";
  input.style.color = "#000";
  input.style.fontWeight = "bold";

  const lock = document.createElement("span");
  lock.innerText = " 🔒";
  lock.className = "lock-icon";
  lock.style.color = "red";
  input.appendChild(lock);

  const container = input.closest(".contact");
  const contactName = getActiveContact(input);
  addResetButton(container, contactName, input);
}

// 🔓 Manual reset
function addResetButton(container, contact, input) {
  if (container.querySelector(".reset-btn")) return;

  const btn = document.createElement("button");
  btn.innerText = "❌ Reset Contact";
  btn.className = "reset-btn";
  btn.style.marginTop = "6px";
  btn.style.padding = "4px 8px";
  btn.style.background = "#ddd";
  btn.style.border = "1px solid #aaa";
  btn.style.borderRadius = "4px";
  btn.style.cursor = "pointer";
  btn.onclick = () => {
    blockedContacts.delete(contact);
    suspiciousCounts.set(contact, 0);
    permanentlyBlocked.delete(contact);
    input.setAttribute("contenteditable", "true");
    input.innerText = "";
    input.style.pointerEvents = "auto";
    input.classList.remove("blocked");
    input.style.border = "";
    input.style.background = "";
    input.style.color = "";
    input.style.fontWeight = "";
    const lock = input.querySelector(".lock-icon");
    if (lock) lock.remove();
    btn.remove();
    console.log(`🔓 Contact ${contact} unblocked`);
  };

  container.appendChild(btn);
}

// 🧠 NLP Model Risk Analysis
function analyzeMessageRisk(text, inputBox) {
  const contact = getActiveContact(inputBox);

  if (permanentlyBlocked.has(contact)) {
    blockInputBox(inputBox);
    return;
  }

  chrome.storage.local.get("selectedModel", (data) => {
    const model = data.selectedModel || "nb";

    fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, model })
    })
      .then(res => res.json())
      .then(data => {
        const { label, confidence } = data;
        console.log(`🧠 NLP Result for ${contact}:`, data);

        if (["honeytrap", "jobfraud", "scam"].includes(label)) {
          showAlert(`⚠️ ${label.toUpperCase()} from ${contact}\nConfidence: ${confidence}`, contact);

          const count = suspiciousCounts.get(contact) || 0;
          const limit = getAlertLimit(contact);

          if (count + 1 >= limit) {
            blockInputBox(inputBox);
          }
        }
      })
      .catch(err => console.error("❌ NLP Risk Analysis Failed:", err));
  });
}

// 🧪 Paste triggers risk analysis
document.addEventListener("paste", (e) => {
  const input = e.target;
  const pasted = (e.clipboardData || window.clipboardData).getData("text");
  const contact = getActiveContact(input);

  if (blockedContacts.get(contact)) {
    e.preventDefault();
    return;
  }

  analyzeMessageRisk(pasted, input);
});

// ⌨️ Typing Speed Tracking
document.addEventListener("keydown", (e) => {
  const input = e.target;
  const contact = getActiveContact(input);

  if (blockedContacts.get(contact)) {
    e.preventDefault();
    e.stopImmediatePropagation();
    return false;
  }

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

// Prevent input edits if blocked
document.addEventListener("input", (e) => {
  const input = e.target;
  const contact = getActiveContact(input);
  if (blockedContacts.get(contact)) {
    e.preventDefault();
    input.innerText = "⚠️ Blocked by MindTrace";
    return false;
  }
});

// 🧠 Typing speed to backend
function sendTypingSpeed(speed) {
  fetch("http://localhost:3000/typing-speed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ platform: getPlatform(), speed })
  })
    .then(res => res.json())
    .then(data => {
      if (data.thiefDetected) {
        showAlert("⚠️ Suspicious typing behavior detected!");
      }
    })
    .catch(err => console.error("❌ Typing Speed Error:", err));
}
