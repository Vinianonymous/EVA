<<<<<<< HEAD

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

=======
-- MySQL 8.0.16+ (enforced CHECK constraints). Run before datos_ejemplo.sql.
CREATE DATABASE IF NOT EXISTS eva CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE eva;

CREATE TABLE IF NOT EXISTS proveedores (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    telefono VARCHAR(30) NOT NULL DEFAULT '',
    direccion VARCHAR(255) NOT NULL DEFAULT ''
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS productos (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(1000) NOT NULL DEFAULT '',
    precio DECIMAL(12,2) NOT NULL,
    proveedor_id INT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_producto_proveedor FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    CONSTRAINT ck_producto_precio CHECK (precio >= 0),
    CONSTRAINT ck_producto_activo CHECK (activo IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inventario (
    producto_id INT NOT NULL PRIMARY KEY,
    cantidad INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_inventario_producto FOREIGN KEY (producto_id) REFERENCES productos(id),
    CONSTRAINT ck_inventario_cantidad CHECK (cantidad >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ventas (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(16,2) NOT NULL,
    anulada BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT ck_venta_total CHECK (total >= 0),
    CONSTRAINT ck_venta_anulada CHECK (anulada IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS detalle_ventas (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    venta_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_detalle_venta FOREIGN KEY (venta_id) REFERENCES ventas(id),
    CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id) REFERENCES productos(id),
    CONSTRAINT uq_detalle_producto UNIQUE (venta_id, producto_id),
    CONSTRAINT ck_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT ck_detalle_precio CHECK (precio_unitario >= 0)
) ENGINE=InnoDB;
>>>>>>> ef23aeb (Implemented DB)
