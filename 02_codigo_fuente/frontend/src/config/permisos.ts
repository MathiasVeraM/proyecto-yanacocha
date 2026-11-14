// Qué puede hacer cada rol dentro de los módulos. Solo muestra, oculta o deshabilita botones:
// el permiso real lo aplican el gateway (src/permisos_rol.py) y cada servicio.
// Los id deben coincidir con la tabla rol del servicio de accesos.

export const ROL = {
  ADMIN: 1,
  VETERINARIA: 2,
  MANEJO_ANIMAL: 3,
  VOLUNTARIO: 4,
} as const

export interface PermisosRol {
  // ---- Fichas ----
  // Registrar ingreso, editar la ficha y registrar la salida de un animal
  gestionarFichas: boolean
  verPestanaVeterinaria: boolean
  // Nuevo registro, editar diagnósticos y tratamientos
  registrarVeterinaria: boolean
  generarPdfVeterinaria: boolean
  // ---- Planificación ----
  // Crear, editar, eliminar, reabrir actividades y manejar dietas
  gestionarActividades: boolean
  // Marcar como hecha y agregar observaciones
  completarActividades: boolean
}

export function permisosDeRol(idRol: number | null | undefined): PermisosRol {
  const es = (...roles: number[]) => idRol != null && roles.includes(idRol)
  return {
    gestionarFichas: es(ROL.VETERINARIA, ROL.MANEJO_ANIMAL),
    verPestanaVeterinaria: es(ROL.VETERINARIA, ROL.ADMIN),
    registrarVeterinaria: es(ROL.VETERINARIA),
    generarPdfVeterinaria: es(ROL.VETERINARIA, ROL.ADMIN),
    gestionarActividades: es(ROL.MANEJO_ANIMAL),
    completarActividades: es(ROL.MANEJO_ANIMAL, ROL.VOLUNTARIO),
  }
}
