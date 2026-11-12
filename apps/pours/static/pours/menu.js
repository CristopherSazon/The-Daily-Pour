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
  const openButton = document.querySelector(".order-open-button");
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
  const defaultEmpty = emptyCopy.textContent;
  const defaultNote = note.textContent;
  let cart = {};
  let currentSlug = "";
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

  function chosenItems() {
    return items.filter((item) => (cart[item.slug] || 0) > 0);
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
      add.addEventListener("click", () => addItem(item.slug));
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
    const chosen = chosenItems();
    const count = chosen.reduce((sum, item) => sum + cart[item.slug], 0);
    const total = chosen.reduce((sum, item) => sum + Number(item.price) * cart[item.slug], 0);
    countLabel.textContent = String(count);
    openButton.setAttribute(
      "aria-label",
      "Open order, " + count + " " + (count === 1 ? "item" : "items") + ", " + peso(total)
    );
    emptyState.hidden = count > 0;
    bag.hidden = count === 0;
    lineList.replaceChildren();
    chosen.forEach((item) => {
      const line = lineTemplate.content.firstElementChild.cloneNode(true);
      const info = line.querySelectorAll(".order-line-info span, .order-line-info strong");
      line.querySelector(".order-line-photo").append(sprite(item, "order-line-sprite"));
      info[0].textContent = item.category;
      info[1].textContent = item.name;
      info[2].textContent = item.price_label + " each";
      line.querySelector(".order-quantity > span").textContent = String(cart[item.slug]);
      line.querySelector('[data-step="-1"]').setAttribute("aria-label", "Remove one " + item.name);
      line.querySelector('[data-step="1"]').setAttribute("aria-label", "Add one " + item.name);
      line.querySelector(".order-quantity").setAttribute("aria-label", item.name + " quantity");
      line.querySelectorAll("[data-step]").forEach((button) => {
        button.addEventListener("click", () => changeQuantity(item.slug, Number(button.dataset.step)));
      });
      lineList.append(line);
    });
    totalLabel.textContent = "Subtotal · " + count + " " + (count === 1 ? "item" : "items");
    totalPrice.textContent = peso(total);
  }

  function changeQuantity(slug, delta) {
    const next = (cart[slug] || 0) + delta;
    if (next <= 0) delete cart[slug];
    else cart[slug] = Math.min(next, 99);
    renderCart();
  }

  function addItem(slug) {
    changeQuantity(slug, 1);
    if (dialog.open) dialog.close();
  }

  function openItem(slug) {
    const item = bySlug.get(slug);
    if (!item) return;
    currentSlug = slug;
    photo.querySelectorAll(".menu-product-sprite").forEach((frame) => frame.remove());
    photo.prepend(sprite(item, "catalog-detail-sprite"));
    categoryLabel.textContent = item.category;
    eyebrow.textContent = "THE DAILY POUR · " + item.number;
    title.textContent = item.name;
    description.textContent = item.description;
    notes.textContent = item.notes;
    price.textContent = item.price_label;
    addLabel.textContent = "Add to order · " + item.price_label;
    recipe.replaceChildren();
    item.recipe.forEach((line) => {
      const entry = document.createElement("li");
      entry.textContent = line;
      recipe.append(entry);
    });
    method.textContent = item.method;
    dialog.showModal();
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
    if (currentSlug) addItem(currentSlug);
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
    const chosen = chosenItems();
    if (!chosen.length) return;
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
        lines: chosen.map((item) => ({ slug: item.slug, quantity: cart[item.slug] })),
      }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      note.textContent = payload.error || "We couldn't save that order.";
      return;
    }
    cart = {};
    form.reset();
    emptyCopy.textContent = "We'll have it ready for pickup.";
    renderCart();
  });

  renderFilters();
  renderGrid();
  renderCart();
})();
