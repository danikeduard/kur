const form = document.querySelector("#chat-form");
const input = document.querySelector("#chat-input");
const messages = document.querySelector("#messages");
const csrf = document.querySelector('meta[name="csrf-token"]')?.content;

function addMessage(role, text) {
  const element = document.createElement("div");
  element.className = `message ${role}`;
  element.textContent = text;
  messages.appendChild(element);
  element.scrollIntoView({ behavior: "smooth", block: "end" });
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = input.value.trim();
  if (!content) return;
  addMessage("user", content);
  input.value = "";
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(csrf ? { "X-CSRFToken": csrf } : {}) },
      body: JSON.stringify({ content }),
    });
    const data = await response.json();
    addMessage("assistant", response.ok ? data.reply : (data.error || "Something went wrong."));
  } catch {
    addMessage("assistant", "I could not connect right now. Please try again.");
  }
});
