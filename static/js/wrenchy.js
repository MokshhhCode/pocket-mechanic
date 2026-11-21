/**
 * WRENCHY AI: Frontend Assistant & Animation Controller
 */

class WrenchyAssistant {
  constructor() {
    this.modal = document.getElementById("wrenchyChatModal");
    this.avatarBtn = document.getElementById("wrenchyAvatarBtn");
    this.characterSvg = document.getElementById("wrenchySvg");
    this.messagesBox = document.getElementById("wrenchyMessagesBox");
    this.input = document.getElementById("wrenchyInput");
    this.sendBtn = document.getElementById("wrenchySendBtn");
    this.speechBubble = document.getElementById("wrenchyBubble");
    this.activeConvId = null;

    if (this.avatarBtn) {
      this.initEvents();
      this.initSpeechHints();
    }
  }

  initEvents() {
    this.avatarBtn.addEventListener("click", () => this.toggleModal());

    const closeBtn = document.getElementById("wrenchyCloseModalBtn");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => this.toggleModal(false));
    }

    if (this.sendBtn && this.input) {
      this.sendBtn.addEventListener("click", () => this.sendMessage());
      this.input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }
  }

  toggleModal(forceState) {
    if (!this.modal) return;
    const isVisible = forceState !== undefined ? !forceState : this.modal.style.display === "flex";
    this.modal.style.display = isVisible ? "none" : "flex";
    if (!isVisible) {
      if (this.speechBubble) this.speechBubble.style.display = "none";
      if (this.input) this.input.focus();
    }
  }

  setSpeaking(isSpeaking) {
    if (!this.characterSvg) return;
    if (isSpeaking) {
      this.characterSvg.classList.add("speaking");
    } else {
      this.characterSvg.classList.remove("speaking");
    }
  }

  sendMessage() {
    const text = this.input.value.trim();
    if (!text) return;

    this.appendMessage("user", text);
    this.input.value = "";
    if (this.input) this.input.disabled = true;
    if (this.sendBtn) this.sendBtn.disabled = true;
    this.setSpeaking(true);
    this.showLoading();

    fetch("/api/wrenchy/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        conversation_id: this.activeConvId
      })
    })
      .then((r) => r.json())
      .then((data) => {
        this.removeLoading();
        this.setSpeaking(false);
        if (this.input) { this.input.disabled = false; this.input.focus(); }
        if (this.sendBtn) this.sendBtn.disabled = false;

        if (data.reply) {
          this.activeConvId = data.conversation_id;
          this.appendMessage("assistant", data.reply, data.suggested_action);
        } else if (data.error) {
          this.appendMessage("assistant", `Error: ${data.error}`);
        }
      })
      .catch((err) => {
        this.removeLoading();
        this.setSpeaking(false);
        if (this.input) { this.input.disabled = false; this.input.focus(); }
        if (this.sendBtn) this.sendBtn.disabled = false;
        this.appendMessage("assistant", "Sorry, I encountered a communication problem with the server.");
        console.error("Wrenchy error:", err);
      });
  }

  showLoading() {
    this.removeLoading();
    if (!this.messagesBox) return;
    const div = document.createElement("div");
    div.id = "wrenchyWidgetThinking";
    div.className = "wrenchy-msg assistant d-flex align-items-center gap-2";
    div.innerHTML = `
      <span class="spinner-border spinner-border-sm text-cyan" role="status" style="width: 0.85rem; height: 0.85rem; border-width: 2px;"></span>
      <div class="wrenchy-thinking-dots me-1">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
      <span class="text-secondary small fst-italic">Thinking...</span>
    `;
    this.messagesBox.appendChild(div);
    this.messagesBox.scrollTop = this.messagesBox.scrollHeight;
  }

  removeLoading() {
    const el = document.getElementById("wrenchyWidgetThinking");
    if (el) el.remove();
  }

  appendMessage(sender, text, action) {
    if (!this.messagesBox) return;

    const div = document.createElement("div");
    div.className = `wrenchy-msg ${sender}`;

    // Simple markdown formatting for bold, lists and headings
    let formatted = text
      .replace(/\n\n/g, "<br><br>")
      .replace(/\n/g, "<br>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/### (.*?)<br>/g, "<div class='fw-bold text-cyan mt-1 mb-1'>$1</div>");

    div.innerHTML = formatted;

    if (action && action.action === "NAVIGATE_TO_DIAGNOSTICS") {
      const actBtn = document.createElement("a");
      actBtn.href = "/diagnostics";
      actBtn.className = "btn btn-sm btn-pm-primary mt-2 d-inline-block text-white";
      actBtn.innerText = action.label || "Proceed to Diagnostics";
      div.appendChild(document.createElement("br"));
      div.appendChild(actBtn);
    }

    this.messagesBox.appendChild(div);
    this.messagesBox.scrollTop = this.messagesBox.scrollHeight;
  }

  initSpeechHints() {
    const tips = [
      "Tip: Cold tyre pressures should be checked before every ride!",
      "I'm keeping an eye on your engine telemetry in real-time.",
      "Need advice on unusual noises or chain slack? Ask me!",
      "Always torque axle fasteners to manufacturer specifications."
    ];
    let tipIdx = 0;

    setInterval(() => {
      if (this.speechBubble && this.modal && this.modal.style.display !== "flex") {
        this.speechBubble.innerText = tips[tipIdx % tips.length];
        this.speechBubble.style.display = "block";
        tipIdx++;
        setTimeout(() => {
          if (this.speechBubble) this.speechBubble.style.display = "none";
        }, 5500);
      }
    }, 25000);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.wrenchy = new WrenchyAssistant();
});
