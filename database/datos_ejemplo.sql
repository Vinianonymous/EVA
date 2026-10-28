<<<<<<< HEAD

-- ==========================================
-- E.V.A. - Librería Virtual
-- Datos de ejemplo
-- =========================================
-- 1. PROVEEDORES

INSERT INTO proveedores
(nombre, telefono, correo, direccion)
VALUES
('Distribuidora Escolar',
 '0981123456',
 'ventas@distribuidora.test',
 'Asunción'),

('Papelería Central',
 '0982234567',
 'contacto@papeleria.test',
 'San Lorenzo'),

('Arte y Diseño',
 '0983345678',
 'info@arteydiseno.test',
 'Fernando de la Mora');


-- 2. PRODUCTOS

INSERT INTO productos
(nombre, categoria, descripcion,
 precio_compra, precio_venta, id_proveedor)
VALUES

('Lápiz de grafito HB', 'Escritura',
 'Lápiz para escritura y dibujo',
 1000, 2000, 1),

('Bolígrafo azul', 'Escritura',
 'Bolígrafo de tinta azul',
 1500, 3000, 1),

('Bolígrafo negro', 'Escritura',
 'Bolígrafo de tinta negra',
 1500, 3000, 1),

('Borrador blanco', 'Corrección',
 'Borrador para lápiz',
 800, 1500, 1),

('Sacapuntas', 'Escolar',
 'Sacapuntas de plástico',
 1200, 2500, 1),

('Regla de 30 cm', 'Geometría',
 'Regla transparente',
 2000, 4000, 2),

('Cuaderno de 100 hojas', 'Papelería',
 'Cuaderno universitario',
 6000, 10000, 2),

('Carpeta A4', 'Papelería',
 'Carpeta para documentos',
 3000, 5000, 2),

('Hojas A4 - 100 unidades', 'Papelería',
 'Paquete de hojas blancas',
 8000, 12000, 2),

('Lápices de colores - 12 unidades', 'Arte',
 'Caja de lápices de colores',
 10000, 15000, 3),

('Pincel mediano', 'Arte',
 'Pincel para pintura',
 3000, 5000, 3),

('Plasticola 100 ml', 'Adhesivos',
 'Pegamento escolar',
 2500, 4500, 2),

('Presilladora', 'Oficina',
 'Presilladora de escritorio',
 15000, 25000, 2),

('Mochila escolar', 'Accesorios',
 'Mochila para estudiantes',
 60000, 85000, 1),

('Organizador reciclado', 'Reciclados',
 'Portalápices de material reciclado',
 3000, 8000, NULL);


-- 3. INVENTARIO

INSERT INTO inventario
(id_producto, cantidad_disponible, stock_minimo)
VALUES
(1,  47, 10),
(2,  58, 10),
(3,  40, 10),
(4,  48, 10),
(5,  35, 5),
(6,  30, 5),
(7,  24, 5),
(8,  25, 5),
(9,  20, 5),
(10, 15, 5),
(11, 20, 5),
(12, 28, 5),
(13, 10, 3),
(14, 8, 2),
(15, 12, 3);


-- 4. VENTAS

INSERT INTO ventas
(fecha_venta, nombre_cliente, total,
 metodo_pago, estado)
VALUES
('2026-10-15 09:30:00',
 'Juan Pérez', 10500,
 'Efectivo', 'completada'),

('2026-10-16 11:15:00',
 'María González', 19000,
 'Transferencia', 'completada'),

('2026-10-17 14:45:00',
 'Carlos López', 13000,
 'Efectivo', 'completada');


-- 5. DETALLE DE VENTAS

-- Venta 1: 3 lápices y 1 plasticola
INSERT INTO detalle_ventas
(id_venta, id_producto, cantidad, precio_unitario)
VALUES
(1, 1, 3, 2000),
(1, 12, 1, 4500);

-- Venta 2: 1 cuaderno, 2 bolígrafos
-- y 2 borradores
INSERT INTO detalle_ventas
(id_venta, id_producto, cantidad, precio_unitario)
VALUES
(2, 7, 1, 10000),
(2, 2, 2, 3000),
(2, 4, 2, 1500);

-- Venta 3: 1 organizador y 1 carpeta
INSERT INTO detalle_ventas
(id_venta, id_producto, cantidad, precio_unitario)
VALUES
(3, 15, 1, 8000),
(3, 8, 1, 5000);

=======
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
>>>>>>> ef23aeb (Implemented DB)
