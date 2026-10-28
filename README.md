# E.V.A.

**Idea de negocio:**  Libreria virtual (Utiles,  impresiones)
Nombre: EVA

# Productos:
- lapices (Papel o color), boligrafos, borradores, hojas sacapuntas, reglas, carpetas, pinceles, material artistico
- Cosas con material reciclado (Organizadores, ...)
- Presilladora, perforadora, pegamento (Plasticola, isocola)
- Mochilas

# Marketing:
- Tiktok, ig, yt
- folletos

# Integrantes:
- Vinicius Rodrigues
- Emilio Morinigo
- Ariel Araujo
  
# Tablas que van a utilizar:
- Productos
- Inventario
- Proveedores
- Ventas
- Detalle de ventas

## Backend Flask + MySQL

Implementado siguiendo el ejemplo de clase: rutas Flask, formularios HTML,
consultas parametrizadas con `flask_mysqldb`, mensajes flash y redirecciones.
Las rutas y la conexión están en `app.py`; no se utiliza SQLite.

### Preparación

Requisitos: Python 3.10+, MySQL 8.0.16+ o MariaDB 10.6+ y las bibliotecas
de desarrollo de MySQL/MariaDB para instalar `mysqlclient`.
En Debian/Ubuntu: `sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mysql -u root -p < database/schema.sql
# Opcional: ejecutar una sola vez sobre la base vacía.
mysql -u root -p < database/datos_ejemplo.sql
```

Crear un usuario para la aplicación desde la consola de MySQL (cambiar la contraseña):

```sql
CREATE USER 'eva'@'localhost' IDENTIFIED BY 'cambiar-esta-clave';
GRANT SELECT, INSERT, UPDATE, DELETE ON eva.* TO 'eva'@'localhost';
```

Configurar las variables en la terminal e iniciar:

```bash
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=eva
export MYSQL_PASSWORD='cambiar-esta-clave'
export MYSQL_DB=eva
python app.py
```

Abrir `http://127.0.0.1:5000/` para la tienda existente o `/admin` para el
resumen administrativo. Las variables se leen del entorno; no se carga un
archivo `.env` automáticamente. Conservar una `SECRET_KEY` estable entre
reinicios para mantener las sesiones. Para desarrollo solamente, usar
`FLASK_DEBUG=1`; el modo debug está deshabilitado por defecto.

### Funciones

- `/proveedores`: alta, consulta, edición y eliminación. No permite eliminar
  proveedores asociados a productos, incluso si están desactivados.
- `/productos`: alta y edición; desactivación sin borrar el historial.
  La edición permite reactivar productos.
- Inventario: cada producto tiene un registro. Los ajustes son incrementos o
  decrementos, nunca permiten stock negativo y se aplican atómicamente.
- `/ventas`: venta de varios productos, detalles y anulación con devolución
  de stock. Los precios y totales se calculan en el servidor con `Decimal`.
- Ventas y altas de productos usan transacciones: todos los cambios se
  confirman juntos o se revierten. Las ventas bloquean las filas de stock
  durante la comprobación para evitar vender las mismas unidades dos veces.
- Anular dos veces una venta no devuelve stock dos veces.
- Todas las modificaciones usan POST y protección CSRF. Las consultas usan
  parámetros `%s`, nunca concatenación de datos del formulario.

**Alcance:** administración local para el proyecto de clase, sin inicio de
sesión ni roles. CSRF no reemplaza la autenticación: no publicar estas rutas
en Internet antes de agregar autenticación y autorización. La tienda conserva
su contenido de ejemplo; no se implementa carrito ni pagos.

### Pruebas

Pruebas unitarias (sin servidor MySQL):

```bash
python -m unittest discover -s tests -v
```

Para incluir pruebas reales de SQL, crear una base **exclusiva de pruebas**
cuyo nombre termine en `_test` y otorgar permisos de creación de tablas y CRUD
al usuario de pruebas. El esquema de tablas se carga automáticamente:

```sql
CREATE DATABASE eva_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON eva_test.* TO 'eva'@'localhost';
```

```bash
EVA_TEST_DB=eva_test python -m unittest discover -s tests -v
```

Las pruebas de integración usan las variables `MYSQL_*` y **vacían las cinco
tablas de la base de pruebas en cada caso**. Nunca apuntarlas a datos reales.
