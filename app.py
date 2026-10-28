import os
from decimal import Decimal, InvalidOperation

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY"),
    MYSQL_HOST=os.environ.get("MYSQL_HOST", "localhost"),
    MYSQL_PORT=int(os.environ.get("MYSQL_PORT", "3306")),
    MYSQL_USER=os.environ.get("MYSQL_USER", "eva"),
    MYSQL_PASSWORD=os.environ.get("MYSQL_PASSWORD", ""),
    MYSQL_DB=os.environ.get("MYSQL_DB", "eva"),
    MYSQL_UNIX_SOCKET=os.environ.get("MYSQL_UNIX_SOCKET", ""),
    MYSQL_CURSORCLASS="DictCursor",
)
mysql = MySQL(app)
CSRFProtect(app)


def consultar(sql, datos=(), uno=False):
    cur = mysql.connection.cursor()
    try:
        cur.execute(sql, datos)
        return cur.fetchone() if uno else cur.fetchall()
    finally:
        cur.close()
        # End read transactions so later requests see current data.
        mysql.connection.rollback()


def modificarTabla(sql, datos, verificar_cambios=False):
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute(sql, datos)
        modificado = cur.rowcount > 0
        mysql.connection.commit()
        # An unchanged existing row is still a successful update.
        return modificado if verificar_cambios else True
    except Exception:
        mysql.connection.rollback()
        app.logger.exception("Error al modificar el registro")
        return False
    finally:
        if cur is not None:
            cur.close()


def insertar(sql, datos):
    return modificarTabla(sql, datos)


def eliminar(sql, datos):
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute(sql, datos)
        eliminado = cur.rowcount > 0
        mysql.connection.commit()
        return eliminado
    except Exception:
        mysql.connection.rollback()
        app.logger.exception("Error al eliminar el registro")
        return False
    finally:
        if cur is not None:
            cur.close()


def texto(campo, maximo, obligatorio=True):
    valor = request.form.get(campo, "").strip()
    if (obligatorio and not valor) or len(valor) > maximo:
        raise ValueError(f"El campo {campo} es obligatorio y admite hasta {maximo} caracteres."
                         if obligatorio else f"El campo {campo} admite hasta {maximo} caracteres.")
    return valor


def entero(valor, minimo=0):
    try:
        numero = int(valor)
    except (ValueError, TypeError):
        raise ValueError("Ingrese una cantidad o identificador entero válido.") from None
    if numero < minimo or numero > 2147483647:
        raise ValueError(f"El número debe estar entre {minimo} y 2147483647.")
    return numero


def precio(valor):
    try:
        numero = Decimal(valor)
        if not numero.is_finite() or numero < 0 or numero > Decimal("9999999999.99"):
            raise ValueError
        if numero != numero.quantize(Decimal("0.01")):
            raise ValueError
        return numero.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Ingrese un precio válido, no negativo y con hasta dos decimales.") from None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin")
def dashboard():
    resumen = consultar("""
        SELECT (SELECT COUNT(*) FROM productos WHERE activo = 1) AS productos,
               (SELECT COUNT(*) FROM proveedores) AS proveedores,
               (SELECT COUNT(*) FROM ventas WHERE anulada = 0) AS ventas,
               (SELECT COALESCE(SUM(total), 0) FROM ventas WHERE anulada = 0) AS total
    """, uno=True)
    return render_template("dashboard.html", resumen=resumen)


@app.route("/proveedores")
def proveedores():
    registros = consultar("SELECT * FROM proveedores ORDER BY nombre, id")
    return render_template("proveedores.html", proveedores=registros)


@app.route("/proveedores/nuevo")
def nuevo_proveedor():
    return render_template("form_proveedor.html", proveedor=None)


@app.route("/proveedores", methods=["POST"])
def crear_proveedor():
    try:
        datos = (texto("nombre", 120), texto("telefono", 30, False),
                 texto("direccion", 255, False))
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("nuevo_proveedor"))
    if insertar("INSERT INTO proveedores (nombre, telefono, direccion) VALUES (%s, %s, %s)", datos):
        flash("Proveedor agregado correctamente", "exito")
    else:
        flash("No se pudo agregar el proveedor", "error")
    return redirect(url_for("proveedores"))


@app.route("/proveedores/editar/<int:id>")
def formulario_proveedor(id):
    registro = consultar("SELECT * FROM proveedores WHERE id = %s", (id,), uno=True)
    if registro is None:
        abort(404)
    return render_template("form_proveedor.html", proveedor=registro)


@app.route("/proveedores/editar/<int:id>", methods=["POST"])
def editar_proveedor(id):
    if consultar("SELECT id FROM proveedores WHERE id = %s", (id,), uno=True) is None:
        abort(404)
    try:
        datos = (texto("nombre", 120), texto("telefono", 30, False),
                 texto("direccion", 255, False), id)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("formulario_proveedor", id=id))
    if modificarTabla("UPDATE proveedores SET nombre = %s, telefono = %s, direccion = %s WHERE id = %s", datos):
        flash("Proveedor modificado correctamente", "exito")
    else:
        flash("No se pudo modificar el proveedor", "error")
    return redirect(url_for("proveedores"))


@app.route("/proveedores/borrar/<int:id>", methods=["POST"])
def borrar_proveedor(id):
    if eliminar("DELETE FROM proveedores WHERE id = %s", (id,)):
        flash("Proveedor eliminado correctamente", "exito")
    else:
        flash("No se pudo eliminar: el proveedor no existe o tiene productos asociados.", "error")
    return redirect(url_for("proveedores"))


@app.route("/productos")
def productos():
    registros = consultar("""
        SELECT p.*, pr.nombre AS proveedor, i.cantidad
        FROM productos p JOIN proveedores pr ON pr.id = p.proveedor_id
        JOIN inventario i ON i.producto_id = p.id
        ORDER BY p.activo DESC, p.nombre, p.id
    """)
    return render_template("productos.html", productos=registros)


@app.route("/productos/nuevo")
def nuevo_producto():
    registros = consultar("SELECT id, nombre FROM proveedores ORDER BY nombre, id")
    return render_template("form_producto.html", producto=None, proveedores=registros)


def datos_producto():
    return (texto("nombre", 120), texto("descripcion", 1000, False),
            precio(request.form.get("precio")), entero(request.form.get("proveedor_id"), 1))


@app.route("/productos", methods=["POST"])
def crear_producto():
    try:
        datos = datos_producto()
        cantidad = entero(request.form.get("cantidad"))
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("nuevo_producto"))
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO productos (nombre, descripcion, precio, proveedor_id)
                       VALUES (%s, %s, %s, %s)""", datos)
        cur.execute("INSERT INTO inventario (producto_id, cantidad) VALUES (%s, %s)",
                    (cur.lastrowid, cantidad))
        mysql.connection.commit()
        flash("Producto agregado correctamente", "exito")
    except Exception:
        mysql.connection.rollback()
        app.logger.exception("Error al crear producto e inventario")
        flash("No se pudo agregar el producto. Verifique el proveedor.", "error")
    finally:
        if cur is not None:
            cur.close()
    return redirect(url_for("productos"))


@app.route("/productos/editar/<int:id>")
def formulario_producto(id):
    registro = consultar("SELECT * FROM productos WHERE id = %s", (id,), uno=True)
    if registro is None:
        abort(404)
    registros = consultar("SELECT id, nombre FROM proveedores ORDER BY nombre, id")
    return render_template("form_producto.html", producto=registro, proveedores=registros)


@app.route("/productos/editar/<int:id>", methods=["POST"])
def editar_producto(id):
    if consultar("SELECT id FROM productos WHERE id = %s", (id,), uno=True) is None:
        abort(404)
    try:
        datos = datos_producto() + (1 if request.form.get("activo") == "1" else 0, id)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("formulario_producto", id=id))
    if modificarTabla("""UPDATE productos SET nombre = %s, descripcion = %s, precio = %s,
                         proveedor_id = %s, activo = %s WHERE id = %s""", datos):
        flash("Producto modificado correctamente", "exito")
    else:
        flash("No se pudo modificar el producto. Verifique el proveedor.", "error")
    return redirect(url_for("productos"))


@app.route("/productos/borrar/<int:id>", methods=["POST"])
def borrar_producto(id):
    if consultar("SELECT id FROM productos WHERE id = %s", (id,), uno=True) is None:
        abort(404)
    if modificarTabla("UPDATE productos SET activo = 0 WHERE id = %s", (id,)):
        flash("Producto desactivado; se conserva su historial de ventas.", "exito")
    else:
        flash("No se pudo desactivar el producto", "error")
    return redirect(url_for("productos"))


@app.route("/inventario/<int:producto_id>", methods=["POST"])
def actualizar_inventario(producto_id):
    if consultar("SELECT producto_id FROM inventario WHERE producto_id = %s",
                 (producto_id,), uno=True) is None:
        abort(404)
    try:
        # Apply a delta, not a stale absolute stock value from a browser form.
        ajuste = entero(request.form.get("ajuste"), -2147483647)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("productos"))
    if modificarTabla("""UPDATE inventario SET cantidad = cantidad + %s
                   WHERE producto_id = %s AND cantidad + %s BETWEEN 0 AND 2147483647""",
                      (ajuste, producto_id, ajuste), verificar_cambios=True):
        flash("Inventario actualizado correctamente", "exito")
    else:
        flash("Sin cambios: verifique que el ajuste no deje el stock negativo o fuera de rango.", "error")
    return redirect(url_for("productos"))


@app.route("/ventas")
def ventas():
    registros = consultar("SELECT * FROM ventas ORDER BY fecha DESC, id DESC")
    detalles = consultar("""
        SELECT d.*, p.nombre FROM detalle_ventas d
        JOIN productos p ON p.id = d.producto_id ORDER BY d.venta_id, d.id
    """)
    por_venta = {}
    for detalle in detalles:
        por_venta.setdefault(detalle["venta_id"], []).append(detalle)
    return render_template("ventas.html", ventas=registros, detalles=por_venta)


@app.route("/ventas/nueva")
def nueva_venta():
    registros = consultar("""
        SELECT p.id, p.nombre, p.precio, i.cantidad FROM productos p
        JOIN inventario i ON i.producto_id = p.id
        WHERE p.activo = 1 AND i.cantidad > 0 ORDER BY p.nombre, p.id
    """)
    return render_template("form_venta.html", productos=registros)


@app.route("/ventas", methods=["POST"])
def crear_venta():
    try:
        ids = request.form.getlist("producto_id")
        cantidades = request.form.getlist("cantidad")
        if not ids or len(ids) != len(cantidades):
            raise ValueError("Seleccione al menos un producto.")
        pedido = {}
        for identificador, cantidad in zip(ids, cantidades):
            producto_id = entero(identificador, 1)
            unidades = entero(cantidad)
            if unidades:
                pedido[producto_id] = entero(pedido.get(producto_id, 0) + unidades, 1)
        if not pedido:
            raise ValueError("Ingrese al menos una cantidad mayor que cero.")
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("nueva_venta"))
    cur = None
    try:
        cur = mysql.connection.cursor()
        lineas = []
        total = Decimal("0.00")
        # Stable lock order reduces deadlocks between simultaneous sales.
        for producto_id, cantidad in sorted(pedido.items()):
            cur.execute("""
                SELECT p.id, p.nombre, p.precio, p.activo, i.cantidad
                FROM productos p JOIN inventario i ON i.producto_id = p.id
                WHERE p.id = %s FOR UPDATE
            """, (producto_id,))
            producto = cur.fetchone()
            if producto is None or not producto["activo"]:
                raise ValueError("Uno de los productos no existe o está desactivado.")
            if producto["cantidad"] < cantidad:
                raise ValueError(f"Stock insuficiente para {producto['nombre']}.")
            total += producto["precio"] * cantidad
            lineas.append((producto_id, cantidad, producto["precio"]))
        if total > Decimal("99999999999999.99"):
            raise ValueError("El total de la venta supera el máximo permitido.")
        cur.execute("INSERT INTO ventas (total) VALUES (%s)", (total,))
        venta_id = cur.lastrowid
        for producto_id, cantidad, precio_unitario in lineas:
            cur.execute("""INSERT INTO detalle_ventas
                           (venta_id, producto_id, cantidad, precio_unitario)
                           VALUES (%s, %s, %s, %s)""",
                        (venta_id, producto_id, cantidad, precio_unitario))
            cur.execute("UPDATE inventario SET cantidad = cantidad - %s WHERE producto_id = %s",
                        (cantidad, producto_id))
        mysql.connection.commit()
        flash("Venta registrada correctamente", "exito")
    except ValueError as error:
        mysql.connection.rollback()
        flash(str(error), "error")
        return redirect(url_for("nueva_venta"))
    except Exception:
        mysql.connection.rollback()
        app.logger.exception("Error al registrar venta")
        flash("No se pudo registrar la venta. No se modificó el inventario.", "error")
    finally:
        if cur is not None:
            cur.close()
    return redirect(url_for("ventas"))


@app.route("/ventas/anular/<int:id>", methods=["POST"])
def anular_venta(id):
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, anulada FROM ventas WHERE id = %s FOR UPDATE", (id,))
        venta = cur.fetchone()
        if venta is None or venta["anulada"]:
            raise ValueError("La venta no existe o ya fue anulada.")
        cur.execute("SELECT * FROM detalle_ventas WHERE venta_id = %s ORDER BY producto_id", (id,))
        detalles = cur.fetchall()
        for detalle in detalles:
            cur.execute("""UPDATE inventario SET cantidad = cantidad + %s
                           WHERE producto_id = %s AND cantidad <= 2147483647 - %s""",
                        (detalle["cantidad"], detalle["producto_id"], detalle["cantidad"]))
            if cur.rowcount != 1:
                raise ValueError("No se puede restaurar el stock: supera el máximo permitido.")
        cur.execute("UPDATE ventas SET anulada = 1 WHERE id = %s", (id,))
        mysql.connection.commit()
        flash("Venta anulada e inventario restaurado", "exito")
    except ValueError as error:
        mysql.connection.rollback()
        flash(str(error), "error")
    except Exception:
        mysql.connection.rollback()
        app.logger.exception("Error al anular venta")
        flash("No se pudo anular la venta", "error")
    finally:
        if cur is not None:
            cur.close()
    return redirect(url_for("ventas"))


if __name__ == "__main__":
    if not app.secret_key:
        raise RuntimeError("Configure la variable de entorno SECRET_KEY antes de iniciar EVA.")
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
