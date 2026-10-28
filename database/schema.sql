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
