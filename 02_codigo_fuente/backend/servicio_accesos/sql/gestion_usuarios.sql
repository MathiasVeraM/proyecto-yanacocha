-- 1. Creación de la tabla de Roles
CREATE TABLE rol (
    id_rol SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) UNIQUE NOT NULL, -- Administrativa, Veterinaria, Manejo de Animales, Voluntarios
    descripcion TEXT
);

-- 2. Creación de la tabla de Módulos (Servicios del sistema)
CREATE TABLE modulo (
    id_modulo SERIAL PRIMARY KEY,
    nombre_modulo VARCHAR(100) UNIQUE NOT NULL, -- Gestion Animal, Actividades, Estadisticas, Accesos
    codigo_servicio VARCHAR(50) NOT NULL
);

-- 3. Tabla intermedia para los Permisos (Qué rol accede a qué módulo)
CREATE TABLE rol_permiso (
    id_rol INT REFERENCES rol(id_rol) ON DELETE CASCADE,
    id_modulo INT REFERENCES modulo(id_modulo) ON DELETE CASCADE,
    PRIMARY KEY (id_rol, id_modulo)
);

-- 4. Creación de la tabla de Usuarios (Basada en los atributos de tu diagrama)
CREATE TABLE usuario (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INT REFERENCES rol(id_rol), -- Relación con los 4 roles definidos
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Inserción de los 4 Roles base
INSERT INTO rol (nombre_rol, descripcion) VALUES
('Administrativa', 'Acceso total a todos los servicios del sistema'),
('Veterinaria', 'Acceso a fichas de ejemplares, bienestar animal y control/informes'),
('Manejo de Animales', 'Acceso a fichas de ejemplares, planificación y bienestar animal'),
('Voluntarios', 'Acceso a planificación y bienestar animal');

-- 6. Inserción de los Módulos/Servicios principales
INSERT INTO modulo (nombre_modulo, codigo_servicio) VALUES
('Fichas de ejemplares', 'servicio-gestion-animal'),
('Planificación', 'servicio-actividades'),
('Bienestar animal y Estadísticas', 'servicio-estadisticas'),
('Seguridad y Accesos', 'servicio-accesos');

-- 7. Asignación de Permisos por Rol (Según tus reglas)
-- Administrador (Rol ID 1): Acceso a todo (Módulos 1, 2, 3, 4)
INSERT INTO rol_permiso (id_rol, id_modulo) VALUES (1, 1), (1, 2), (1, 3), (1, 4);

-- Veterinaria (Rol ID 2): Acceso a Fichas (1), Bienestar/Estadísticas (3), y Accesos si requiere ver reportes (o según regla: Fichas, Bienestar, Control/Informes)
INSERT INTO rol_permiso (id_rol, id_modulo) VALUES (2, 1), (2, 3);

-- Manejo Animal (Rol ID 3): Acceso a Fichas (1), Planificación (2), Bienestar (3)
INSERT INTO rol_permiso (id_rol, id_modulo) VALUES (3, 1), (3, 2), (3, 3);

-- Voluntarios (Rol ID 4): Acceso a Planificación (2) y Bienestar (3)
INSERT INTO rol_permiso (id_rol, id_modulo) VALUES (4, 2), (4, 3);