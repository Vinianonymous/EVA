-- Optional seed data: run once on an empty EVA database, after schema.sql.
USE eva;
START TRANSACTION;
INSERT INTO proveedores (nombre, telefono, direccion)
VALUES ('Distribuidora Escolar', '021 555 100', 'Av. Principal 123');
SET @proveedor = LAST_INSERT_ID();

INSERT INTO productos (nombre, descripcion, precio, proveedor_id)
VALUES ('Cuaderno A5', 'Cuaderno rayado de 100 hojas', 4500.00, @proveedor);
INSERT INTO inventario (producto_id, cantidad) VALUES (LAST_INSERT_ID(), 30);

INSERT INTO productos (nombre, descripcion, precio, proveedor_id)
VALUES ('Bolígrafo azul', 'Bolígrafo de tinta azul', 2500.00, @proveedor);
INSERT INTO inventario (producto_id, cantidad) VALUES (LAST_INSERT_ID(), 100);

INSERT INTO productos (nombre, descripcion, precio, proveedor_id)
VALUES ('Mochila escolar', 'Mochila reforzada', 29900.00, @proveedor);
INSERT INTO inventario (producto_id, cantidad) VALUES (LAST_INSERT_ID(), 10);
COMMIT;
