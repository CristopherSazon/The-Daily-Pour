(function () {
  const dialog = document.querySelector(".barista-dialog");
  const launcher = document.querySelector(".barista-launcher");
  const log = document.querySelector(".barista-log");
  const form = document.querySelector(".barista-form");
  if (!dialog || !launcher || !log || !form || !dialog.show) return;

  const input = form.querySelector('input[type="text"]');
  const pendingKey = "daily-pour-pending";
  let transcript = [];
  let ready = false;
  let busy = false;

  function csrfToken() {
    const field = form.querySelector("[name=csrfmiddlewaretoken]");
    return field ? field.value : "";
  }

  function sprite(item) {
    if (!item.image) return null;
    const frame = document.createElement("div");
    frame.className = "menu-product-sprite";
    frame.setAttribute("role", "img");
    frame.setAttribute("aria-label", item.image_alt || "");
    const image = document.createElement("img");
    image.className = "menu-product-sprite-image";
    image.alt = "";
    image.src = item.image;
    const index = Number(item.image_index) || 0;
    image.style.left = -100 * (index % 3) + "%";
    image.style.top = -100 * Math.floor(index / 3) + "%";
    frame.append(image);
    return frame;
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

  function suggestionCard(suggestion) {
    const card = document.createElement("article");
    card.className = "barista-card";
    const image = sprite(suggestion);
    if (image) {
      const frame = document.createElement("span");
      frame.className = "barista-card-image";
      frame.append(image);
      card.append(frame);
    }
    const copy = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = suggestion.name;
    const reason = document.createElement("p");
    reason.textContent = suggestion.reason || "";
    const add = document.createElement("button");
    add.type = "button";
    add.className = "catalog-card-add";
    add.textContent = "Add · " + (suggestion.unit_price_label || suggestion.price_label || "");
    add.addEventListener("click", () => addSuggestion(suggestion.slug, suggestion.selected_modifiers || [], 1, true));
    copy.append(name, reason, add);
    card.append(copy);
    return card;
  }

  function appendExchange(userText, payload) {
    if (userText) {
      const mine = document.createElement("p");
      mine.className = "barista-user";
      mine.textContent = userText;
      log.append(mine);
    }
    const reply = document.createElement("div");
    reply.className = "barista-reply";
    const say = document.createElement("p");
    say.textContent = payload.say || "";
    reply.append(say);
    (payload.items || []).forEach((suggestion) => reply.append(suggestionCard(suggestion)));
    if (payload.recall && payload.recall.phone) {
      const confirm = document.createElement("button");
      confirm.type = "button";
      confirm.className = "barista-recall";
      confirm.textContent = payload.recall.prompt;
      confirm.addEventListener("click", () => send("", payload.recall.phone));
      reply.append(confirm);
    }
    log.append(reply);
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

  async function loadBarista() {
    const response = await fetch("/barista/");
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (!log.childElementCount) appendExchange("", { say: payload.error || "The barista is away from the bar right now." });
      return;
    }
    applyGuest(payload);
    if (!log.childElementCount) appendExchange("", payload);
    ready = true;
  }

  async function send(message, confirmPhone) {
    if (busy) return;
    const history = transcript.slice(-8);
    if (message) transcript.push({ role: "user", content: message });
    busy = true;
    form.querySelector("button").disabled = true;
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
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        appendExchange(message, { say: payload.error || "The barista is away from the bar right now." });
        return;
      }
      if (payload.say) transcript.push({ role: "assistant", content: payload.say });
      (payload.cart || []).forEach((line) => addSuggestion(line.slug, line.modifiers || [], line.quantity || 1, false));
      applyGuest(payload);
      appendExchange(message, payload);
    } finally {
      busy = false;
      form.querySelector("button").disabled = false;
      input.focus();
    }
  }

  async function openPanel() {
    if (dialog.open) {
      dialog.close();
      return;
    }
    dialog.show();
    launcher.setAttribute("aria-expanded", "true");
    if (!ready) await loadBarista();
    input.focus();
  }

  launcher.addEventListener("click", openPanel);
  dialog.querySelector(".product-dialog-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => launcher.setAttribute("aria-expanded", "false"));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && dialog.open) dialog.close();
  });
  document.addEventListener("daily-pour-ordered", () => {
    ready = false;
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    send(message, "");
  });
})();
