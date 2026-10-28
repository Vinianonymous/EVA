"""Page contracts with mocked reads; no MySQL server is required."""
from decimal import Decimal
from html.parser import HTMLParser
import unittest
from unittest.mock import patch

from MySQLdb import OperationalError

import app as backend


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current = {"attrs": attrs, "inputs": []}
            self.forms.append(self.current)
        elif tag == "input" and self.current is not None:
            self.current["inputs"].append(attrs)

    def handle_endtag(self, tag):
        if tag == "form":
            self.current = None


class FrontendTests(unittest.TestCase):
    def setUp(self):
        backend.app.config.update(TESTING=True, SECRET_KEY="frontend-test", WTF_CSRF_ENABLED=True)
        self.client = backend.app.test_client()
        self.product = dict(id=1, nombre="Lápiz <script>alert(1)</script>",
                            descripcion="Grafito & papel", precio=Decimal("2500.00"),
                            proveedor_id=2, proveedor="Distribuidora", cantidad=5, activo=1)
        self.supplier = dict(id=2, nombre="Distribuidora", telefono="123", direccion="Centro")

    def page(self, path, records):
        with patch.object(backend, "consultar", return_value=records):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def test_live_catalog_and_escaped_product_content(self):
        html = self.page("/", [self.product])
        self.assertIn("2,500.00", html)
        self.assertIn("Disponible · 5 unidades", html)
        self.assertIn("Lápiz &lt;script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn('data-catalog', html)
        self.assertNotIn('href="#"', html)

    def test_catalog_query_filters_inactive_products(self):
        with patch.object(backend, "consultar", return_value=[]) as query:
            self.client.get("/")
        self.assertIn("WHERE p.activo = 1", query.call_args.args[0])

    def test_out_of_stock_product_and_empty_catalog(self):
        self.assertIn("Agotado", self.page("/", [{**self.product, "cantidad": 0}]))
        self.assertIn("Todavía no hay productos", self.page("/", []))

    def test_list_pages_render_records(self):
        for path, records, expected in (
            ("/productos", [self.product], "Ajustar stock"),
            ("/proveedores", [self.supplier], "Distribuidora"),
            ("/ventas/nueva", [self.product], "data-sale-quantity"),
            ("/admin", dict(productos=1, proveedores=1, ventas=0, total=Decimal("0")), "0.00"),
        ):
            with self.subTest(path=path):
                self.assertIn(expected, self.page(path, records))

    def test_empty_admin_pages(self):
        for path, expected in (("/productos", "Todavía no hay productos"),
                               ("/proveedores", "Todavía no hay proveedores"),
                               ("/ventas", "Todavía no hay ventas"),
                               ("/ventas/nueva", "Primero, un poco de stock"),
                               ("/productos/nuevo", "Empecemos por un proveedor")):
            with self.subTest(path=path):
                self.assertIn(expected, self.page(path, []))

    def test_forms_post_to_existing_routes_with_csrf(self):
        for path, records in (("/productos", [self.product]),
                               ("/proveedores", [self.supplier]),
                               ("/productos/nuevo", [self.supplier]),
                               ("/proveedores/nuevo", []),
                               ("/ventas/nueva", [self.product])):
            parser = FormParser()
            parser.feed(self.page(path, records))
            posts = [form for form in parser.forms if form["attrs"].get("method") == "post"]
            self.assertTrue(posts, path)
            adapter = backend.app.url_map.bind("localhost")
            for form in posts:
                adapter.match(form["attrs"]["action"], method="POST")
                tokens = [field for field in form["inputs"] if field.get("name") == "csrf_token"]
                self.assertEqual(len(tokens), 1)
                self.assertTrue(tokens[0]["value"])

    def test_edit_forms_and_cancelled_sales(self):
        for path, first in (("/productos/editar/1", self.product),
                            ("/proveedores/editar/2", self.supplier)):
            with patch.object(backend, "consultar", side_effect=[first, [self.supplier]]):
                response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Guardar", response.get_data(as_text=True))
        sale = dict(id=3, fecha="2026-10-28 10:00:00", total=Decimal("5000"), anulada=1)
        detail = dict(venta_id=3, nombre="Lápiz", cantidad=2, precio_unitario=Decimal("2500"))
        with patch.object(backend, "consultar", side_effect=[[sale], [detail]]):
            html = self.client.get("/ventas").get_data(as_text=True)
        self.assertIn("Anulada", html)
        self.assertIn("Stock restaurado", html)
        self.assertNotIn('action="/ventas/anular/3"', html)

    def test_error_pages_and_assets(self):
        self.assertEqual(self.client.get("/missing").status_code, 404)
        response = self.client.post("/proveedores", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("El formulario venció", response.get_data(as_text=True))
        with patch.object(backend, "consultar", side_effect=OperationalError("unavailable")):
            with self.assertLogs(backend.app.logger, level="ERROR"):
                response = self.client.get("/")
        self.assertEqual(response.status_code, 503)
        for asset in ("main.js", "estilos.css", "stationery.svg", "favicon.svg"):
            response = self.client.get(f"/static/{asset}")
            self.assertEqual(response.status_code, 200)
            response.close()


if __name__ == "__main__":
    unittest.main()
