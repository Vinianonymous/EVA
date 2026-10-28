/* Optional, read-only browser checks against a running EVA instance.
 * Install playwright and @axe-core/playwright outside the application; see README.
 */
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
const AxeBuilder = require("@axe-core/playwright").default;

const base = process.env.EVA_URL || "http://127.0.0.1:5000";
const paths = ["/", "/admin", "/productos", "/proveedores", "/ventas",
  "/ventas/nueva", "/productos/nuevo", "/proveedores/nuevo", "/missing"];

(async () => {
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors = [];
    const writes = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("request", (request) => {
      if (request.method() === "POST") writes.push(request.url());
    });

    for (const width of [1440, 390, 320, 768]) {
      await page.setViewportSize({ width, height: 900 });
      for (const path of paths) {
        const response = await page.goto(base + path);
        assert.equal(response.status(), path === "/missing" ? 404 : 200, path);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
          false, `${width}px ${path}: page overflow`);
        if (width === 1440 || width === 390) {
          const result = await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
          assert.deepEqual(result.violations.map((violation) => ({
            id: violation.id, targets: violation.nodes.map((node) => node.target),
          })), [], `${width}px ${path}: accessibility`);
        }
      }
      console.log(`PASS responsive layout: ${width}px`);
    }

    await page.goto(base + "/");
    const search = page.getByRole("searchbox");
    if (await search.count()) {
      const count = await page.locator("[data-item]").count();
      await search.fill("__eva_no_match_8392__");
      assert.equal(await page.locator("[data-item]:visible").count(), 0);
      assert.equal(await page.locator("[data-no-results]").isVisible(), true);
      await page.getByRole("button", { name: "Limpiar filtros" }).click();
      assert.equal(await page.locator("[data-item]:visible").count(), count);
      await page.locator("[data-sort]").selectOption("price-desc");
      const prices = await page.locator("[data-item]").evaluateAll((items) =>
        items.map((item) => Number(item.dataset.price)));
      assert.deepEqual(prices, [...prices].sort((a, b) => b - a));
      console.log("PASS catalog search, reset, price sorting");
    }

    await page.goto(base + "/ventas/nueva");
    const quantities = page.locator("[data-sale-quantity]");
    if (await quantities.count()) {
      await page.getByRole("button", { name: "Confirmar venta ↗" }).click();
      assert.match(await page.locator("[data-sale-error]").innerText(), /al menos/);
      const input = quantities.first();
      await input.fill("1");
      const price = Number(await input.getAttribute("data-price"));
      const expected = new Intl.NumberFormat("en-US", {
        minimumFractionDigits: 2, maximumFractionDigits: 2,
      }).format(price);
      assert.equal(await page.locator("[data-sale-total]").innerText(), expected);
      await page.getByRole("searchbox").fill("__eva_no_match_8392__");
      assert.equal(await page.locator("[data-sale-total]").innerText(), expected);
      assert.equal(await page.locator("[data-sale-selection] li").count(), 1);
      // Hidden rows must be revealed when their quantity needs correction.
      await input.evaluate((element) => {
        element.value = String(Number(element.max) + 1);
        element.dispatchEvent(new Event("input", { bubbles: true }));
      });
      await page.getByRole("button", { name: "Confirmar venta ↗" }).click();
      assert.equal(await input.isVisible(), true);
      assert.match(await page.locator("[data-sale-error]").innerText(), /enteras/);
      console.log("PASS sale preview, retained selections, empty and hidden-row validation");
    }

    assert.deepEqual(writes, [], "Read-only checks must not mutate data");
    assert.deepEqual(errors, [], "No JavaScript errors");
    console.log("Browser checks passed. No data was modified.");
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
