(function () {
  const data = document.getElementById("menu-data");
  const dialog = document.querySelector(".product-dialog");
  const orderDialog = document.querySelector(".order-dialog");
  if (!data || !dialog || !orderDialog || !dialog.showModal) return;

  const items = JSON.parse(data.textContent);
  const bySlug = new Map(items.map((item) => [item.slug, item]));
  const photo = dialog.querySelector(".product-dialog-photo");
  const category = dialog.querySelector(".product-dialog-category");
  const eyebrow = dialog.querySelector(".product-dialog-content > .eyebrow");
  const title = dialog.querySelector("#product-dialog-title");
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

  function peso(amount) {
    const value = Number(amount);
    return Number.isInteger(value) ? "₱" + value : "₱" + value.toFixed(2);
  }

  function lines() {
    return items.filter((item) => (cart[item.slug] || 0) > 0);
  }

  function renderCart() {
    const chosen = lines();
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
      line.querySelector("img").src = item.image;
      line.querySelector("img").alt = "";
      info[0].textContent = item.category_label;
      info[1].textContent = item.name;
      info[2].textContent = item.price_label + " each";
      const quantity = line.querySelector(".order-quantity > span");
      quantity.textContent = String(cart[item.slug]);
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

  function openItem(slug) {
    const item = bySlug.get(slug);
    if (!item) return;
    currentSlug = slug;
    photo.src = item.image;
    photo.alt = item.image_alt;
    category.textContent = item.category_label;
    eyebrow.textContent = item.number ? "A HOUSE FAVORITE · " + item.number : "A HOUSE FAVORITE";
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

  document.querySelectorAll("[data-item]").forEach((button) => {
    button.addEventListener("click", () => openItem(button.dataset.item));
  });
  dialog.querySelector(".product-dialog-close").addEventListener("click", () => dialog.close());
  dialog.querySelector(".product-dialog-done").addEventListener("click", () => {
    if (!currentSlug) return;
    changeQuantity(currentSlug, 1);
    dialog.close();
  });
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  openButton.addEventListener("click", () => orderDialog.showModal());
  orderDialog.querySelector(".product-dialog-close").addEventListener("click", () => orderDialog.close());
  orderDialog.querySelectorAll(".order-back").forEach((button) => {
    button.addEventListener("click", () => orderDialog.close());
  });
  orderDialog.addEventListener("click", (event) => {
    if (event.target === orderDialog) orderDialog.close();
  });
  orderDialog.addEventListener("close", () => {
    emptyCopy.textContent = defaultEmpty;
    note.textContent = defaultNote;
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const chosen = lines();
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

  renderCart();
})();
