
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    telefono TEXT,
    correo TEXT,
    direccion TEXT
);

CREATE TABLE IF NOT EXISTS productos (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    descripcion TEXT,
    precio_compra NUMERIC NOT NULL CHECK(precio_compra >= 0),
    precio_venta NUMERIC NOT NULL CHECK(precio_venta >= 0),
    id_proveedor INTEGER,

    FOREIGN KEY (id_proveedor)
        REFERENCES proveedores(id_proveedor)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS inventario (
    id_inventario INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto INTEGER NOT NULL UNIQUE,
    cantidad_disponible INTEGER NOT NULL DEFAULT 0
        CHECK(cantidad_disponible >= 0),
    stock_minimo INTEGER NOT NULL DEFAULT 5
        CHECK(stock_minimo >= 0),
    ultima_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS ventas (
    id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_venta TEXT DEFAULT CURRENT_TIMESTAMP,
    nombre_cliente TEXT NOT NULL,
    total NUMERIC NOT NULL DEFAULT 0 CHECK(total >= 0),
    metodo_pago TEXT,
    estado TEXT NOT NULL DEFAULT 'completada'
);

CREATE TABLE IF NOT EXISTS detalle_ventas (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
    precio_unitario NUMERIC NOT NULL CHECK(precio_unitario >= 0),
    subtotal NUMERIC GENERATED ALWAYS AS
        (cantidad * precio_unitario) STORED,

    FOREIGN KEY (id_venta)
        REFERENCES ventas(id_venta)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

