(function () {
  const data = document.getElementById("menu-data");
  const dialog = document.querySelector(".product-dialog");
  if (!data || !dialog || !dialog.showModal) return;

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

  function openItem(slug) {
    const item = bySlug.get(slug);
    if (!item) return;
    photo.src = item.image;
    photo.alt = item.image_alt;
    category.textContent = item.category_label;
    eyebrow.textContent = item.number ? "A HOUSE FAVORITE · " + item.number : "A HOUSE FAVORITE";
    title.textContent = item.name;
    description.textContent = item.description;
    notes.textContent = item.notes;
    price.textContent = item.price_label;
    recipe.replaceChildren();
    item.recipe.forEach((line) => {
      const entry = document.createElement("li");
      entry.textContent = line;
      recipe.append(entry);
    });
    method.textContent = item.method;
    dialog.showModal();
  }

  document.querySelectorAll("[data-item]").forEach((button) => {
    button.addEventListener("click", () => openItem(button.dataset.item));
  });
  dialog.querySelector(".product-dialog-close").addEventListener("click", () => dialog.close());
  dialog.querySelector(".product-dialog-done").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
})();
