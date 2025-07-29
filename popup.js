// 🔁 Handle model switching
document.getElementById("model").addEventListener("change", function () {
  const selectedModel = this.value;
  chrome.storage.local.set({ selectedModel });
  console.log("🔁 Model switched to:", selectedModel);
});

// ✅ Load selected model when popup opens
chrome.storage.local.get("selectedModel", (data) => {
  if (data.selectedModel) {
    document.getElementById("model").value = data.selectedModel;
  }
});

// 📝 Handle feedback submission
document.getElementById("submitFeedback").addEventListener("click", function () {
  const message = document.getElementById("feedbackText").value.trim();
  const label = document.getElementById("feedbackLabel").value;

  if (!message) {
    alert("⚠️ Please enter a message.");
    return;
  }

  fetch("http://localhost:8000/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, label })
  })
    .then(res => {
      if (res.ok) {
        alert("✅ Feedback submitted successfully!");
        document.getElementById("feedbackText").value = "";
      } else {
        alert("❌ Failed to submit feedback.");
      }
    })
    .catch(err => {
      console.error("Feedback error:", err);
      alert("❌ Could not connect to feedback server.");
    });
});
