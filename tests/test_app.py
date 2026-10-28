import os
from concurrent.futures import ThreadPoolExecutor
from contextvars import Context
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from threading import Barrier
import unittest
from unittest.mock import MagicMock, patch

import app as backend


class BackendTests(unittest.TestCase):
    def setUp(self):
        backend.app.config.update(TESTING=True, SECRET_KEY="test-secret", WTF_CSRF_ENABLED=False)
        self.client = backend.app.test_client()

    def test_storefront_is_preserved(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Temporada escolar 2026", response.data)
        self.assertIn(b"/admin", response.data)

    def test_price_validation(self):
        self.assertEqual(backend.precio("12.50"), Decimal("12.50"))
        self.assertEqual(backend.precio("0"), Decimal("0.00"))
        for value in ("NaN", "Infinity", "-1", "1.001", "10000000000", "", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                backend.precio(value)

    def test_integer_validation(self):
        self.assertEqual(backend.entero("5"), 5)
        for value in ("1.5", "abc", "-1", "2147483648", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                backend.entero(value)

    def test_csrf_rejects_missing_token(self):
        backend.app.config["WTF_CSRF_ENABLED"] = True
        response = self.client.post("/proveedores", data={"nombre": "Test"})
        self.assertEqual(response.status_code, 400)

    def test_mutations_reject_get(self):
        for path in ("/productos/borrar/1", "/proveedores/borrar/1", "/ventas/anular/1", "/inventario/1"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 405)

    def test_empty_sale_rejected_without_database(self):
        response = self.client.post("/ventas", data={})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/ventas/nueva"))

    def test_query_parameters_are_not_interpolated(self):
        connection = MagicMock()
        connection.cursor.return_value.rowcount = 1
        with patch.object(backend, "mysql", SimpleNamespace(connection=connection)):
            with backend.app.app_context():
                backend.insertar("INSERT INTO proveedores (nombre) VALUES (%s)", ("'; DROP TABLE productos; --",))
        connection.cursor.return_value.execute.assert_called_once_with(
            "INSERT INTO proveedores (nombre) VALUES (%s)", ("'; DROP TABLE productos; --",))
        connection.commit.assert_called_once()
        connection.cursor.return_value.close.assert_called_once()

    def test_product_inventory_failure_rolls_back(self):
        connection = MagicMock()
        connection.cursor.return_value.execute.side_effect = [None, RuntimeError("inventory failure")]
        with patch.object(backend, "mysql", SimpleNamespace(connection=connection)):
            with self.assertLogs(backend.app.logger, level="ERROR"):
                response = self.client.post("/productos", data={
                    "nombre": "Test", "precio": "1.00", "proveedor_id": "1", "cantidad": "3"})
        self.assertEqual(response.status_code, 302)
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()
        connection.cursor.return_value.close.assert_called_once()

    def test_stock_failure_after_first_sale_line_rolls_back(self):
        connection = MagicMock()
        connection.cursor.return_value.fetchone.side_effect = [
            {"id": 1, "nombre": "A", "precio": Decimal("2.00"), "activo": 1, "cantidad": 5},
            {"id": 2, "nombre": "B", "precio": Decimal("3.00"), "activo": 1, "cantidad": 0},
        ]
        with patch.object(backend, "mysql", SimpleNamespace(connection=connection)):
            response = self.client.post("/ventas", data={"producto_id": ["1", "2"], "cantidad": ["1", "1"]})
        self.assertEqual(response.status_code, 302)
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()


@unittest.skipUnless(os.environ.get("EVA_TEST_DB"), "Set EVA_TEST_DB for MySQL integration tests")
class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database = os.environ["EVA_TEST_DB"]
        if not database.endswith("_test"):
            raise RuntimeError("EVA_TEST_DB must end in _test; tests delete its data.")
        backend.app.config.update(MYSQL_DB=database, TESTING=True, SECRET_KEY="test-secret", WTF_CSRF_ENABLED=False)
        schema = (Path(__file__).resolve().parents[1] / "database" / "schema.sql").read_text()
        schema = "\n".join(line for line in schema.splitlines()
                           if not line.startswith(("--", "CREATE DATABASE", "USE ")))
        with backend.app.app_context():
            cur = backend.mysql.connection.cursor()
            try:
                for statement in schema.split(";"):
                    if statement.strip():
                        cur.execute(statement)
                backend.mysql.connection.commit()
            finally:
                cur.close()

    def setUp(self):
        self.client = backend.app.test_client()
        self.context = backend.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)
        cur = backend.mysql.connection.cursor()
        for table in ("detalle_ventas", "ventas", "inventario", "productos", "proveedores"):
            cur.execute(f"DELETE FROM {table}")  # Fixed test-owned table names, not user input.
        backend.mysql.connection.commit()
        cur.close()
        self.client.post("/proveedores", data={"nombre": "Proveedor de prueba"})
        self.proveedor = backend.consultar("SELECT id FROM proveedores", uno=True)["id"]

    def product(self, name="Cuaderno", price="10.50", stock="5"):
        response = self.client.post("/productos", data={
            "nombre": name, "precio": price, "proveedor_id": str(self.proveedor), "cantidad": stock})
        self.assertEqual(response.status_code, 302)
        return backend.consultar("SELECT id FROM productos ORDER BY id DESC LIMIT 1", uno=True)["id"]

    def stock(self, product):
        return backend.consultar("SELECT cantidad FROM inventario WHERE producto_id = %s", (product,), uno=True)["cantidad"]

    def test_crud_and_all_pages(self):
        product = self.product()
        for path in ("/", "/admin", "/proveedores", "/proveedores/nuevo", "/productos",
                     "/productos/nuevo", "/ventas", "/ventas/nueva",
                     f"/productos/editar/{product}", f"/proveedores/editar/{self.proveedor}"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        self.client.post(f"/productos/editar/{product}", data={
            "nombre": "Cuaderno editado", "precio": "12.00", "proveedor_id": str(self.proveedor), "activo": "1"})
        self.assertEqual(backend.consultar("SELECT nombre FROM productos WHERE id = %s", (product,), uno=True)["nombre"], "Cuaderno editado")
        with self.assertLogs(backend.app.logger, level="ERROR"):
            self.client.post(f"/proveedores/borrar/{self.proveedor}")
        self.assertIsNotNone(backend.consultar("SELECT id FROM proveedores WHERE id = %s", (self.proveedor,), uno=True))

    def test_sale_total_stock_and_cancellation(self):
        product = self.product()
        other = self.product("Lápiz", "2.25", "10")
        response = self.client.post("/ventas", data={
            "producto_id": [str(product), str(other)], "cantidad": ["2", "3"], "total": "0.01"})
        self.assertEqual(response.status_code, 302)
        sale = backend.consultar("SELECT * FROM ventas", uno=True)
        self.assertEqual(sale["total"], Decimal("27.75"))
        self.assertEqual(self.stock(product), 3)
        self.assertEqual(self.stock(other), 7)
        self.assertEqual(self.client.get("/ventas").status_code, 200)
        self.client.post(f"/ventas/anular/{sale['id']}")
        self.client.post(f"/ventas/anular/{sale['id']}")
        self.assertEqual(self.stock(product), 5)
        self.assertEqual(self.stock(other), 10)
        self.assertEqual(backend.consultar("SELECT anulada FROM ventas", uno=True)["anulada"], 1)

    def test_insufficient_stock_leaves_no_sale(self):
        first = self.product()
        second = self.product("Otro", stock="1")
        self.client.post("/ventas", data={"producto_id": [str(first), str(second)], "cantidad": ["1", "2"]})
        self.assertEqual(self.stock(first), 5)
        self.assertEqual(self.stock(second), 1)
        self.assertEqual(backend.consultar("SELECT COUNT(*) AS n FROM ventas", uno=True)["n"], 0)

    def test_duplicate_products_are_combined(self):
        product = self.product()
        self.client.post("/ventas", data={"producto_id": [str(product), str(product)], "cantidad": ["1", "2"]})
        self.assertEqual(self.stock(product), 2)
        detail = backend.consultar("SELECT * FROM detalle_ventas", uno=True)
        self.assertEqual(detail["cantidad"], 3)

    def test_inventory_adjustments_and_inactive_sale(self):
        product = self.product()
        self.client.post(f"/inventario/{product}", data={"ajuste": "-6"})
        self.assertEqual(self.stock(product), 5)
        self.client.post(f"/inventario/{product}", data={"ajuste": "3"})
        self.assertEqual(self.stock(product), 8)
        self.client.post(f"/productos/borrar/{product}")
        self.client.post("/ventas", data={"producto_id": str(product), "cantidad": "1"})
        self.assertEqual(self.stock(product), 8)
        self.assertEqual(backend.consultar("SELECT COUNT(*) AS n FROM ventas", uno=True)["n"], 0)

    def test_invalid_product_and_missing_ids(self):
        self.client.post("/productos", data={"nombre": "", "precio": "NaN", "cantidad": "0", "proveedor_id": str(self.proveedor)})
        self.assertEqual(backend.consultar("SELECT COUNT(*) AS n FROM productos", uno=True)["n"], 0)
        self.assertEqual(self.client.get("/productos/editar/2147483647").status_code, 404)
        self.assertEqual(self.client.get("/proveedores/editar/2147483647").status_code, 404)

    def test_supplier_update_and_delete(self):
        self.client.post(f"/proveedores/editar/{self.proveedor}", data={"nombre": "Editado", "telefono": "123"})
        row = backend.consultar("SELECT * FROM proveedores WHERE id = %s", (self.proveedor,), uno=True)
        self.assertEqual(row["nombre"], "Editado")
        self.assertEqual(row["telefono"], "123")
        self.client.post(f"/proveedores/borrar/{self.proveedor}")
        self.assertIsNone(backend.consultar("SELECT id FROM proveedores WHERE id = %s", (self.proveedor,), uno=True))

    def test_concurrent_sales_do_not_oversell(self):
        product = self.product(stock="1")
        barrier = Barrier(2)

        def sell():
            client = backend.app.test_client()
            barrier.wait(timeout=10)
            return client.post("/ventas", data={"producto_id": str(product), "cantidad": "1"}).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            # Each simulated request must own its app context and DB connection,
            # including on Python versions where worker threads inherit context.
            responses = list(pool.map(lambda _: Context().run(sell), range(2)))
        self.assertEqual(responses, [302, 302])
        self.assertEqual(self.stock(product), 0)
        self.assertEqual(backend.consultar("SELECT COUNT(*) AS n FROM ventas", uno=True)["n"], 1)


if __name__ == "__main__":
    unittest.main()
