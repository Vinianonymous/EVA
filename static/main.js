/* Progressive enhancement: all writes remain ordinary CSRF-protected Flask forms. */
(() => {
  "use strict";

  const normalize = (text) => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
  const money = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  document.querySelectorAll("[data-catalog], [data-filter-list]").forEach((root) => {
    const search = root.querySelector("[data-search]");
    const status = root.querySelector("[data-status]:is(select)");
    const sort = root.querySelector("[data-sort]");
    const items = Array.from(root.querySelectorAll("[data-item]"));
    const count = root.querySelector("[data-result-count]");
    const empty = root.querySelector("[data-no-results]");
    const originalCount = count?.textContent;
    const apply = () => {
      const query = normalize(search?.value.trim() || "");
      let visible = 0;
      items.forEach((item) => {
        item.hidden = !normalize(item.dataset.searchText || "").includes(query) ||
          (status && status.value !== "all" && item.dataset.status !== status.value);
        if (!item.hidden) visible += 1;
      });
      if (count) count.textContent = query || (status && status.value !== "all")
        ? `${visible} de ${items.length} resultados` : originalCount;
      if (empty) empty.hidden = visible > 0 || items.length === 0;
      if (sort) {
        const ordered = [...items].sort((a, b) => {
          if (sort.value === "price-asc") return Number(a.dataset.price) - Number(b.dataset.price);
          if (sort.value === "price-desc") return Number(b.dataset.price) - Number(a.dataset.price);
          return a.dataset.name.localeCompare(b.dataset.name, "es");
        });
        ordered.forEach((item) => item.parentElement.append(item));
      }
    };
    search?.addEventListener("input", apply);
    status?.addEventListener("change", apply);
    sort?.addEventListener("change", apply);
    root.querySelector("[data-filter-form]")?.addEventListener("submit", (event) => event.preventDefault());
    root.querySelector("[data-reset-filters]")?.addEventListener("click", () => {
      if (search) search.value = "";
      if (status) status.value = "all";
      if (sort) sort.value = "name";
      apply();
      search?.focus();
    });
    apply();
  });

  const sale = document.querySelector("[data-sale-form]");
  if (sale) {
    const quantities = Array.from(sale.querySelectorAll("[data-sale-quantity]"));
    const error = sale.querySelector("[data-sale-error]");
    // Use integer cents for the preview; the server remains authoritative (Decimal).
    const cents = (price) => {
      const [whole, fraction = ""] = price.split(".");
      return Number(whole) * 100 + Number(fraction.padEnd(2, "0").slice(0, 2));
    };
    const refresh = () => {
      let total = 0;
      let units = 0;
      const selection = sale.querySelector("[data-sale-selection]");
      selection.replaceChildren();
      quantities.forEach((input) => {
        const quantity = Number(input.value);
        if (!input.validity.valid || quantity <= 0) return;
        units += quantity;
        const subtotal = quantity * cents(input.dataset.price);
        total += subtotal;
        const item = document.createElement("li");
        const name = document.createElement("span");
        const amount = document.createElement("b");
        name.textContent = `${quantity} × ${input.dataset.name}`;
        amount.textContent = money.format(subtotal / 100);
        item.append(name, amount);
        selection.append(item);
      });
      sale.querySelector("[data-sale-total]").textContent = Number.isSafeInteger(total)
        ? money.format(total / 100) : "Se calculará al confirmar";
      sale.querySelector("[data-sale-count]").textContent = units > 0
        ? `${units} ${units === 1 ? "unidad seleccionada" : "unidades seleccionadas"}`
        : "Seleccioná al menos un producto.";
      error.hidden = true;
    };
    quantities.forEach((input) => input.addEventListener("input", refresh));
    // Do not let search's Enter key submit a sale accidentally.
    sale.querySelector("[data-search]")?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") event.preventDefault();
    });
    sale.addEventListener("submit", (event) => {
      const invalid = quantities.find((input) => !input.validity.valid);
      const selected = quantities.some((input) => Number(input.value) > 0);
      if (invalid || !selected) {
        event.preventDefault();
        error.textContent = invalid ? "Revisá las cantidades: deben ser enteras y no superar el stock." : "Ingresá al menos una cantidad mayor que cero.";
        error.hidden = false;
        // A search may hide the row that needs correction.
        const target = invalid || quantities[0];
        const search = sale.querySelector("[data-search]");
        if (search) { search.value = ""; search.dispatchEvent(new Event("input")); }
        target.focus();
      }
    });
    refresh();
  }

  document.querySelectorAll("form[method='post']").forEach((form) => {
    // Own validation lets a hidden filtered sale row be revealed before focusing it.
    if (form.matches("[data-sale-form]")) form.noValidate = true;
    form.addEventListener("submit", (event) => {
      if (event.defaultPrevented) return;
      if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
        event.preventDefault();
        return;
      }
      form.querySelectorAll("button[type='submit']").forEach((button) => {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = "Guardando…";
      });
    });
  });
  window.addEventListener("pageshow", () => {
    document.querySelectorAll("button[data-original-text]").forEach((button) => {
      button.disabled = false;
      button.textContent = button.dataset.originalText;
      delete button.dataset.originalText;
    });
  });
  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => button.closest(".mensaje").remove());
  });
})();
