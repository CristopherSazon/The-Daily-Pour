(function () {
  const panel = document.querySelector(".barista-panel");
  const launcher = document.querySelector(".barista-launcher");
  const log = document.querySelector(".barista-log");
  const form = document.querySelector(".barista-compose");
  const welcome = document.querySelector(".barista-welcome");
  const status = document.querySelector(".barista-status");
  const restart = document.querySelector(".barista-restart");
  if (!panel || !launcher || !log || !form || !welcome || !status) return;

  const input = form.querySelector('input[type="text"]');
  const sendButton = form.querySelector(".barista-send");
  const pendingKey = "daily-pour-pending";
  const starters = ["Something not too sweet", "An iced pick-me-up", "Coffee and a little treat"];
  let transcript = [];
  let knownGuest = false;
  let busy = false;
  let request = null;
  let lastAttempt = null;

  function csrfToken() {
    const field = form.querySelector("[name=csrfmiddlewaretoken]");
    return field ? field.value : "";
  }

  function setOpen(open) {
    panel.hidden = !open;
    launcher.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) input.focus();
  }

  function updateSend() {
    sendButton.disabled = busy || !input.value.trim();
    input.disabled = busy;
    welcome.querySelectorAll("button").forEach((button) => {
      button.disabled = busy;
    });
  }

  function clearStatus() {
    status.replaceChildren();
  }

  function showStatus(text, actionLabel, onAction) {
    clearStatus();
    const note = document.createElement("span");
    note.textContent = text;
    const action = document.createElement("button");
    action.type = "button";
    action.textContent = actionLabel;
    action.addEventListener("click", onAction);
    status.append(note, action);
  }

  function remember(line) {
    const pending = JSON.parse(sessionStorage.getItem(pendingKey) || "[]");
    pending.push(line);
    sessionStorage.setItem(pendingKey, JSON.stringify(pending));
  }

  function addSuggestion(slug, modifiers, quantity, goToMenu) {
    const line = { slug: slug, modifiers: modifiers || [], quantity: quantity || 1 };
    if (window.DailyPour && DailyPour.addLine) {
      DailyPour.addLine(line.slug, line.modifiers, line.quantity);
      return;
    }
    remember(line);
    if (goToMenu) window.location.href = "/menu/";
  }

  function messageArticle(role, text) {
    const article = document.createElement("article");
    article.className = "barista-message barista-message-" + role;
    const sender = document.createElement("span");
    sender.className = "barista-message-sender";
    sender.textContent = role === "user" ? "YOU" : "THE BARISTA";
    const body = document.createElement("p");
    body.textContent = text;
    article.append(sender, body);
    return article;
  }

  function offerButtons(choices) {
    if (!choices.length) return;
    const group = document.createElement("div");
    group.className = "barista-suggestions";
    choices.forEach((choice) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = choice.label;
      button.addEventListener("click", choice.onClick);
      group.append(button);
    });
    log.append(group);
  }

  function revealConversation() {
    welcome.hidden = true;
    if (restart) restart.hidden = false;
  }

  function appendReply(message, payload) {
    if (message) {
      revealConversation();
      log.append(messageArticle("user", message));
    }
    if (payload.say) log.append(messageArticle("assistant", payload.say));
    const choices = (payload.items || []).map((suggestion) => ({
      label: "Add " + suggestion.name + (suggestion.unit_price_label || suggestion.price_label ? " · " + (suggestion.unit_price_label || suggestion.price_label) : ""),
      onClick: () => addSuggestion(suggestion.slug, suggestion.selected_modifiers || [], 1, true),
    }));
    if (payload.recall && payload.recall.phone) {
      choices.push({
        label: payload.recall.prompt,
        onClick: () => send("", payload.recall.phone, false),
      });
    }
    offerButtons(choices);
    log.scrollTop = log.scrollHeight;
  }

  function applyGuest(payload) {
    if (payload.preferences && window.DailyPour && DailyPour.setPreferences) {
      DailyPour.setPreferences(payload.preferences);
    }
    if (window.DailyPour && DailyPour.prefill) {
      DailyPour.prefill(payload.name, payload.phone, payload.pickup);
    }
  }

  async function loadGuest() {
    if (knownGuest) return;
    knownGuest = true;
    const response = await fetch("/barista/");
    const payload = await response.json().catch(() => ({}));
    if (response.ok) applyGuest(payload);
  }

  async function send(message, confirmPhone, echo) {
    if (busy) return;
    const history = transcript.slice(-8);
    if (message) transcript.push({ role: "user", content: message });
    if (echo !== false && message) appendReply(message, {});
    lastAttempt = { message: message, confirmPhone: confirmPhone || "" };
    busy = true;
    updateSend();
    request = new AbortController();
    showStatus("Finding a good fit…", "Stop", () => request.abort());
    try {
      const cart = window.DailyPour && DailyPour.lines ? DailyPour.lines() : [];
      const response = await fetch("/barista/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({
          message: message,
          history: history,
          cart: cart,
          confirm_phone: confirmPhone || "",
        }),
        signal: request.signal,
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        showStatus(payload.error || "I couldn't connect just now. Please try again.", "Try again", () => send(lastAttempt.message, lastAttempt.confirmPhone, false));
        return;
      }
      clearStatus();
      if (payload.say) transcript.push({ role: "assistant", content: payload.say });
      (payload.cart || []).forEach((line) => addSuggestion(line.slug, line.modifiers || [], line.quantity || 1, false));
      applyGuest(payload);
      appendReply("", payload);
    } catch (error) {
      if (error.name === "AbortError") {
        clearStatus();
        return;
      }
      showStatus("I couldn't connect just now. Please try again.", "Try again", () => send(lastAttempt.message, lastAttempt.confirmPhone, false));
    } finally {
      busy = false;
      request = null;
      updateSend();
      input.focus();
    }
  }

  function resetChat() {
    if (request) request.abort();
    transcript = [];
    lastAttempt = null;
    log.querySelectorAll(".barista-message, :scope > .barista-suggestions").forEach((node) => node.remove());
    welcome.hidden = false;
    if (restart) restart.hidden = true;
    clearStatus();
    input.value = "";
    updateSend();
    input.focus();
  }

  launcher.addEventListener("click", () => {
    const open = panel.hidden;
    setOpen(open);
    if (open) loadGuest();
  });
  panel.querySelector(".barista-close").addEventListener("click", () => setOpen(false));
  if (restart) restart.addEventListener("click", resetChat);
  panel.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
    }
  });
  welcome.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      if (!starters.includes(button.textContent)) return;
      input.value = "";
      updateSend();
      send(button.textContent, "", true);
    });
  });
  input.addEventListener("input", updateSend);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || busy) return;
    input.value = "";
    updateSend();
    send(message, "", true);
  });
})();
