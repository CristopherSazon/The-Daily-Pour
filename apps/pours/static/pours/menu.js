(function () {
  const data = document.getElementById("menu-data");
  const dialog = document.querySelector(".product-dialog");
  const orderDialog = document.querySelector(".order-dialog");
  if (!data || !dialog || !orderDialog || !dialog.showModal) return;

  const catalog = JSON.parse(data.textContent);
  const items = catalog.items;
  const bySlug = new Map(items.map((item) => [item.slug, item]));
  const filters = document.querySelector(".catalog-category-list");
  const search = document.querySelector(".catalog-search input");
  const results = document.querySelector(".catalog-results");
  const grid = document.querySelector(".catalog-product-grid");
  const empty = document.querySelector(".catalog-no-results");
  const photo = dialog.querySelector(".catalog-detail-image");
  const categoryLabel = dialog.querySelector(".product-dialog-category");
  const eyebrow = dialog.querySelector(".product-dialog-content > .eyebrow");
  const title = dialog.querySelector("#catalog-product-title");
  const description = dialog.querySelector(".product-dialog-description");
  const notes = dialog.querySelector(".product-dialog-notes");
  const price = dialog.querySelector(".product-dialog-price strong");
  const recipe = dialog.querySelector(".product-recipe ul");
  const method = dialog.querySelector(".product-method");
  const addLabel = dialog.querySelector(".product-dialog-done span");
  const openButton = document.querySelector(".catalog-order-button");
  const countLabel = openButton.querySelector(".order-count");
  const emptyState = orderDialog.querySelector(".order-empty");
  const emptyCopy = emptyState.querySelector("p");
  const bag = orderDialog.querySelector(".order-dialog-grid");
  const lineList = orderDialog.querySelector(".order-lines");
  const totalLabel = orderDialog.querySelector(".order-total-label");
  const totalPrice = orderDialog.querySelector(".order-total strong");
  const form = orderDialog.querySelector(".order-form");
  const note = orderDialog.querySelector(".order-note");
  const lineTemplate = document.getElementById("order-line-template");
  const baristaDialog = document.querySelector(".barista-dialog");
  const baristaLog = document.querySelector(".barista-log");
  const baristaForm = document.querySelector(".barista-form");
  const baristaInput = baristaForm.querySelector("input");
  const defaultEmpty = emptyCopy.textContent;
  const defaultNote = note.textContent;
  const modifierGroups = [
    ["milk", "Milk"],
    ["sweetness", "Sweetness"],
    ["temperature", "Served"],
  ];
  let cart = [];
  let currentSlug = "";
  let selectedModifiers = [];
  let guestPreferences = { milk: "", sweetness: "", temperature: "" };
  let transcript = [];
  let baristaReady = false;
  let baristaBusy = false;
  let category = "daily-classics";

  function peso(amount) {
    const value = Number(amount);
    return Number.isInteger(value) ? "₱" + value : "₱" + value.toFixed(2);
  }

  function sprite(item, className) {
    const frame = document.createElement("div");
    frame.className = "menu-product-sprite" + (className ? " " + className : "");
    frame.setAttribute("role", "img");
    frame.setAttribute("aria-label", item.image_alt || "");
    const image = document.createElement("img");
    image.className = "menu-product-sprite-image";
    image.alt = "";
    image.src = item.image;
    const column = item.image_index % 3;
    const row = Math.floor(item.image_index / 3);
    image.style.left = -100 * column + "%";
    image.style.top = -100 * row + "%";
    frame.append(image);
    return frame;
  }

  function lineKey(slug, modifiers) {
    return slug + "|" + (modifiers || []).slice().sort().join(",");
  }

  function unitPrice(item, modifiers) {
    const extra = (item.modifiers || [])
      .filter((modifier) => (modifiers || []).includes(modifier.slug))
      .reduce((sum, modifier) => sum + Number(modifier.price), 0);
    return Number(item.price) + extra;
  }

  function modifierLabels(item, modifiers) {
    return (item.modifiers || [])
      .filter((modifier) => (modifiers || []).includes(modifier.slug))
      .map((modifier) => modifier.label)
      .join(", ");
  }

  function visibleItems() {
    const query = search.value.trim().toLowerCase();
    return items.filter((item) => {
      const inCategory = category === "all" || item.category_slug === category;
      const matches = !query || (item.name + " " + item.description + " " + item.category).toLowerCase().includes(query);
      return inCategory && matches;
    });
  }

  function resultCopy(shown) {
    const query = search.value.trim();
    if (query) return shown.length + " " + (shown.length === 1 ? "result" : "results") + " for “" + query + "”";
    if (category === "all") return items.length + " drinks & bites, made fresh daily";
    const selected = catalog.categories.find((entry) => entry.slug === category);
    return shown.length + " favorites in " + (selected ? selected.name : "the menu");
  }

  function renderFilters() {
    filters.replaceChildren();
    const everything = document.createElement("button");
    everything.className = "catalog-category-button";
    everything.type = "button";
    everything.setAttribute("aria-pressed", String(category === "all"));
    everything.append("Everything ", countSpan(items.length));
    everything.addEventListener("click", () => {
      category = "all";
      renderFilters();
      renderGrid();
    });
    filters.append(everything);
    catalog.categories.forEach((entry) => {
      const button = document.createElement("button");
      button.className = "catalog-category-button";
      button.type = "button";
      button.setAttribute("aria-pressed", String(category === entry.slug));
      button.append(entry.name, countSpan(entry.count));
      button.addEventListener("click", () => {
        category = entry.slug;
        renderFilters();
        renderGrid();
      });
      filters.append(button);
    });
  }

  function countSpan(count) {
    const span = document.createElement("span");
    span.textContent = String(count);
    return span;
  }

  function renderGrid() {
    const shown = visibleItems();
    results.textContent = resultCopy(shown);
    grid.hidden = shown.length === 0;
    empty.hidden = shown.length > 0;
    grid.replaceChildren();
    shown.forEach((item) => {
      const card = document.createElement("article");
      card.className = "catalog-card";
      const details = document.createElement("button");
      details.className = "catalog-card-details";
      details.type = "button";
      details.setAttribute("aria-haspopup", "dialog");
      details.setAttribute("aria-label", "View " + item.name + ", " + item.price_label + ", and details");
      const image = document.createElement("span");
      image.className = "catalog-card-image";
      image.append(sprite(item));
      const index = document.createElement("span");
      index.className = "catalog-card-index";
      index.append(item.number + " ", icon("arrow-up-right"));
      image.append(index);
      const meta = document.createElement("span");
      meta.className = "catalog-card-meta";
      const metaCategory = document.createElement("span");
      metaCategory.textContent = item.category;
      const metaPrice = document.createElement("span");
      metaPrice.textContent = item.price_label;
      meta.append(metaCategory, metaPrice);
      const name = document.createElement("span");
      name.className = "catalog-card-name";
      name.textContent = item.name;
      const copy = document.createElement("span");
      copy.className = "catalog-card-description";
      copy.textContent = item.description;
      const view = document.createElement("span");
      view.className = "catalog-card-view";
      view.append("VIEW DETAILS ", icon("arrow-up-right"));
      details.append(image, meta, name, copy, view);
      details.addEventListener("click", () => openItem(item.slug));
      const add = document.createElement("button");
      add.className = "catalog-card-add";
      add.type = "button";
      add.setAttribute("aria-label", "Add " + item.name + " to your order");
      add.append(icon("plus"), document.createElement("span"));
      add.lastElementChild.textContent = "Add to order";
      add.addEventListener("click", () => addLine(item.slug, [], 1));
      card.append(details, add);
      grid.append(card);
    });
  }

  function icon(name) {
    const paths = name === "plus"
      ? ["M5 12h14", "M12 5v14"]
      : ["M7 7h10v10", "M7 17 17 7"];
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    paths.forEach((shape) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", shape);
      svg.append(path);
    });
    return svg;
  }

  function renderCart() {
    const count = cart.reduce((sum, line) => sum + line.quantity, 0);
    const total = cart.reduce((sum, line) => {
      const item = bySlug.get(line.slug);
      return item ? sum + unitPrice(item, line.modifiers) * line.quantity : sum;
    }, 0);
    countLabel.textContent = String(count);
    openButton.setAttribute(
      "aria-label",
      "Open order, " + count + " " + (count === 1 ? "item" : "items") + ", " + peso(total)
    );
    emptyState.hidden = count > 0;
    bag.hidden = count === 0;
    lineList.replaceChildren();
    cart.forEach((entry) => {
      const item = bySlug.get(entry.slug);
      if (!item) return;
      const line = lineTemplate.content.firstElementChild.cloneNode(true);
      const info = line.querySelectorAll(".order-line-info span, .order-line-info strong");
      const labels = modifierLabels(item, entry.modifiers);
      line.querySelector(".order-line-photo").append(sprite(item, "order-line-sprite"));
      info[0].textContent = item.category;
      info[1].textContent = item.name;
      info[2].hidden = !labels;
      info[2].textContent = labels;
      info[3].textContent = peso(unitPrice(item, entry.modifiers)) + " each";
      line.querySelector(".order-quantity > span").textContent = String(entry.quantity);
      line.querySelector('[data-step="-1"]').setAttribute("aria-label", "Remove one " + item.name);
      line.querySelector('[data-step="1"]').setAttribute("aria-label", "Add one " + item.name);
      line.querySelector(".order-quantity").setAttribute("aria-label", item.name + " quantity");
      line.querySelectorAll("[data-step]").forEach((button) => {
        button.addEventListener("click", () => changeQuantity(entry.key, Number(button.dataset.step)));
      });
      lineList.append(line);
    });
    totalLabel.textContent = "Subtotal · " + count + " " + (count === 1 ? "item" : "items");
    totalPrice.textContent = peso(total);
  }

  function changeQuantity(key, delta) {
    const entry = cart.find((line) => line.key === key);
    if (!entry) return;
    entry.quantity += delta;
    if (entry.quantity <= 0) cart = cart.filter((line) => line.key !== key);
    else entry.quantity = Math.min(entry.quantity, 99);
    renderCart();
  }

  function addLine(slug, modifiers, quantity) {
    const item = bySlug.get(slug);
    if (!item) return;
    const chosen = (item.modifiers || [])
      .map((modifier) => modifier.slug)
      .filter((modifier) => (modifiers || []).includes(modifier));
    const key = lineKey(slug, chosen);
    const entry = cart.find((line) => line.key === key);
    const amount = quantity || 1;
    if (entry) entry.quantity = Math.min(entry.quantity + amount, 99);
    else cart.push({ key: key, slug: slug, modifiers: chosen, quantity: Math.min(amount, 99) });
    renderCart();
  }

  function openItem(slug) {
    const item = bySlug.get(slug);
    if (!item) return;
    currentSlug = slug;
    selectedModifiers = ["milk", "sweetness", "temperature"]
      .map((group) => guestPreferences[group])
      .filter((modifier) => modifier && (item.modifiers || []).some((choice) => choice.slug === modifier));
    photo.querySelectorAll(".menu-product-sprite").forEach((frame) => frame.remove());
    photo.prepend(sprite(item, "catalog-detail-sprite"));
    categoryLabel.textContent = item.category;
    eyebrow.textContent = "THE DAILY POUR · " + item.number;
    title.textContent = item.name;
    description.textContent = item.description;
    notes.textContent = item.notes;
    renderModifiers(item);
    updateDialogPrice(item);
    recipe.replaceChildren();
    item.recipe.forEach((line) => {
      const entry = document.createElement("li");
      entry.textContent = line;
      recipe.append(entry);
    });
    method.textContent = item.method;
    dialog.showModal();
  }

  function renderModifiers(item) {
    const host = dialog.querySelector(".product-modifiers");
    host.replaceChildren();
    modifierGroups.forEach(([group, label]) => {
      const choices = (item.modifiers || []).filter((modifier) => modifier.group === group);
      if (!choices.length) return;
      const row = document.createElement("div");
      row.className = "modifier-row";
      const name = document.createElement("span");
      name.textContent = label;
      const options = document.createElement("div");
      options.className = "modifier-options";
      choices.forEach((modifier) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = modifier.label;
        button.setAttribute("aria-pressed", String(selectedModifiers.includes(modifier.slug)));
        button.addEventListener("click", () => {
          const remaining = selectedModifiers.filter((slug) => !choices.some((choice) => choice.slug === slug));
          selectedModifiers = selectedModifiers.includes(modifier.slug) ? remaining : remaining.concat(modifier.slug);
          renderModifiers(item);
          updateDialogPrice(item);
        });
        options.append(button);
      });
      row.append(name, options);
      host.append(row);
    });
  }

  function updateDialogPrice(item) {
    const label = peso(unitPrice(item, selectedModifiers));
    price.textContent = label;
    addLabel.textContent = "Add to order · " + label;
  }

  function csrfToken() {
    const input = form.querySelector("[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  search.addEventListener("input", () => {
    if (search.value.trim()) category = "all";
    renderFilters();
    renderGrid();
  });
  empty.querySelector("button").addEventListener("click", () => {
    search.value = "";
    category = "all";
    renderFilters();
    renderGrid();
  });
  dialog.querySelector(".product-dialog-close").addEventListener("click", () => dialog.close());
  dialog.querySelector(".product-dialog-done").addEventListener("click", () => {
    if (currentSlug) addLine(currentSlug, selectedModifiers, 1);
    if (dialog.open) dialog.close();
  });
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  openButton.addEventListener("click", () => orderDialog.showModal());
  orderDialog.querySelector(".product-dialog-close").addEventListener("click", () => orderDialog.close());
  orderDialog.querySelector(".order-back").addEventListener("click", () => orderDialog.close());
  orderDialog.addEventListener("click", (event) => {
    if (event.target === orderDialog) orderDialog.close();
  });
  orderDialog.addEventListener("close", () => {
    emptyCopy.textContent = defaultEmpty;
    note.textContent = defaultNote;
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!cart.length) return;
    note.textContent = defaultNote;
    const response = await fetch("/orders/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify({
        name: form.querySelector("#customer-name").value,
        phone: form.querySelector("#customer-phone").value,
        pickup: form.querySelector("#pickup-time").value,
        lines: cart.map((line) => ({
          slug: line.slug,
          quantity: line.quantity,
          modifiers: line.modifiers,
        })),
      }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      note.textContent = payload.error || "We couldn't save that order.";
      return;
    }
    cart = [];
    form.reset();
    emptyCopy.textContent = "We'll have it ready for pickup.";
    baristaReady = false;
    renderCart();
  });

  function prefill(name, phone, pickup) {
    const nameInput = form.querySelector("#customer-name");
    const phoneInput = form.querySelector("#customer-phone");
    const pickupInput = form.querySelector("#pickup-time");
    if (name && !nameInput.value) nameInput.value = name;
    if (phone && !phoneInput.value) phoneInput.value = phone;
    if (pickup && !pickupInput.value) pickupInput.value = pickup;
  }

  function appendExchange(userText, payload) {
    if (userText) {
      const mine = document.createElement("p");
      mine.className = "barista-user";
      mine.textContent = userText;
      baristaLog.append(mine);
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
    baristaLog.append(reply);
    baristaLog.scrollTop = baristaLog.scrollHeight;
  }

  function suggestionCard(suggestion) {
    const item = bySlug.get(suggestion.slug);
    const card = document.createElement("article");
    card.className = "barista-card";
    if (item) {
      const image = document.createElement("span");
      image.className = "barista-card-image";
      image.append(sprite(item));
      card.append(image);
    }
    const copy = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = suggestion.name;
    const reason = document.createElement("p");
    reason.textContent = suggestion.reason || "";
    const add = document.createElement("button");
    add.type = "button";
    add.className = "catalog-card-add";
    add.append(icon("plus"), document.createTextNode(" Add · " + (suggestion.unit_price_label || suggestion.price_label)));
    add.addEventListener("click", () => addLine(suggestion.slug, suggestion.selected_modifiers || [], 1));
    copy.append(name, reason, add);
    card.append(copy);
    return card;
  }

  async function loadBarista() {
    const response = await fetch("/barista/");
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (!baristaLog.childElementCount) appendExchange("", { say: payload.error || "The barista is away from the bar right now." });
      return;
    }
    guestPreferences = payload.preferences || guestPreferences;
    prefill(payload.name, payload.phone, "");
    if (!baristaLog.childElementCount) appendExchange("", payload);
    baristaReady = true;
  }

  async function send(message, confirmPhone) {
    if (baristaBusy) return;
    const history = transcript.slice(-8);
    if (message) transcript.push({ role: "user", content: message });
    baristaBusy = true;
    baristaForm.querySelector("button").disabled = true;
    try {
      const response = await fetch("/barista/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({
          message: message,
          history: history,
          cart: cart.map((line) => ({
            slug: line.slug,
            quantity: line.quantity,
            modifiers: line.modifiers,
          })),
          confirm_phone: confirmPhone || "",
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        appendExchange(message, { say: payload.error || "The barista is away from the bar right now." });
        return;
      }
      if (payload.say) transcript.push({ role: "assistant", content: payload.say });
      (payload.cart || []).forEach((line) => addLine(line.slug, line.modifiers || [], line.quantity || 1));
      if (payload.preferences) guestPreferences = payload.preferences;
      prefill(payload.name, payload.phone, payload.pickup);
      appendExchange(message, payload);
    } finally {
      baristaBusy = false;
      baristaForm.querySelector("button").disabled = false;
      baristaInput.focus();
    }
  }

  document.querySelector(".barista-open-button").addEventListener("click", async () => {
    baristaDialog.showModal();
    if (!baristaReady) await loadBarista();
    baristaInput.focus();
  });
  baristaDialog.querySelector(".product-dialog-close").addEventListener("click", () => baristaDialog.close());
  baristaDialog.addEventListener("click", (event) => {
    if (event.target === baristaDialog) baristaDialog.close();
  });
  baristaForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = baristaInput.value.trim();
    if (!message) return;
    baristaInput.value = "";
    send(message, "");
  });

  renderFilters();
  renderGrid();
  renderCart();
})();
