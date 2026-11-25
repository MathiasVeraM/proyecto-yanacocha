// Caché de respuestas de la API, SOLO en memoria.
//
// - Vive mientras la pestaña está abierta: no se escribe en localStorage, sessionStorage
//   ni IndexedDB, así que no queda nada guardado en el equipo (importante en computadoras
//   compartidas y frente a scripts maliciosos).
// - Se borra por completo al iniciar o cerrar sesión (limpiarCache).
// - El backend sigue siendo la fuente de verdad: la caché solo sirve para mostrar algo al
//   instante mientras se confirma con la API.
//
// Cada clave empieza con el servicio al que pertenece ("animales|…", "actividades|…",
// "auth|…"). Cuando una petición que modifica datos (POST, PUT, PATCH, DELETE) termina bien,
// http.ts invalida las claves de ese servicio y la próxima consulta vuelve a pedirlas.

export interface OpcionesConsulta<T> {
  /**
   * Edad máxima (ms) para usar lo guardado sin preguntar a la API.
   * 0 = siempre revalidar · Infinity = mientras no se invalide (toda la sesión).
   */
  maxEdad?: number
  /**
   * Si se indica, lo guardado (aunque sea viejo) se devuelve al instante y la API se
   * consulta por detrás; cuando llega la respuesta se entrega aquí.
   * Si no se indica y lo guardado es viejo, se espera la respuesta nueva.
   */
  alActualizar?: (datos: T) => void
}

interface Entrada {
  datos?: unknown
  tieneDatos: boolean
  // Versión del servicio cuando se pidieron los datos: si cambió, ya no son válidos
  version: number
  momento: number
  promesa?: Promise<unknown>
  versionPromesa?: number
}

const entradas = new Map<string, Entrada>()
const versiones = new Map<string, number>()
const alLimpiarFns = new Set<() => void>()
// Cambia en cada limpieza: una respuesta pedida antes de cerrar sesión no se guarda
let generacion = 0

const servicioDe = (clave: string) => clave.split('|', 1)[0]!
const versionDe = (servicio: string) => versiones.get(servicio) ?? 0

function vigente(entrada: Entrada | undefined, clave: string): entrada is Entrada {
  return !!entrada?.tieneDatos && entrada.version === versionDe(servicioDe(clave))
}

function traer<T>(clave: string, pedir: () => Promise<T>): Promise<T> {
  const servicio = servicioDe(clave)
  const version = versionDe(servicio)
  const actual = entradas.get(clave)
  // Si ya hay una petición en curso con datos válidos, se reutiliza (evita pedidos duplicados)
  if (actual?.promesa && actual.versionPromesa === version) return actual.promesa as Promise<T>

  const gen = generacion
  const promesa = pedir()
    .then((datos) => {
      if (gen === generacion) {
        entradas.set(clave, { datos, tieneDatos: true, version, momento: Date.now() })
      }
      return datos
    })
    .finally(() => {
      const entrada = entradas.get(clave)
      if (entrada?.promesa === promesa) {
        entrada.promesa = undefined
        entrada.versionPromesa = undefined
      }
    })
  entradas.set(clave, {
    ...(actual ?? { tieneDatos: false, version, momento: 0 }),
    promesa,
    versionPromesa: version,
  })
  return promesa
}

/** Consulta con caché: ver OpcionesConsulta para cómo se decide si se usa lo guardado. */
export async function consultar<T>(
  clave: string,
  pedir: () => Promise<T>,
  { maxEdad = 0, alActualizar }: OpcionesConsulta<T> = {},
): Promise<T> {
  const entrada = entradas.get(clave)
  if (vigente(entrada, clave)) {
    if (Date.now() - entrada.momento <= maxEdad) return entrada.datos as T
    if (alActualizar) {
      // Se muestra lo guardado y se actualiza por detrás; si falla, se queda lo que había
      traer(clave, pedir)
        .then(alActualizar)
        .catch(() => {})
      return entrada.datos as T
    }
  }
  return traer(clave, pedir)
}

/** Guarda datos que ya se conocen (por ejemplo, lo que devolvió la API al modificar algo). */
export function fijar<T>(clave: string, datos: T) {
  entradas.set(clave, {
    datos,
    tieneDatos: true,
    version: versionDe(servicioDe(clave)),
    momento: Date.now(),
  })
}

/** Modifica lo guardado en una clave, solo si existe y sigue siendo válido. */
export function actualizar<T>(clave: string, cambiar: (datos: T) => T) {
  const entrada = entradas.get(clave)
  if (vigente(entrada, clave)) fijar(clave, cambiar(entrada.datos as T))
}

/** Marca como desactualizado todo lo de un servicio ("animales", "actividades", "auth"). */
export function invalidar(servicio: string) {
  versiones.set(servicio, versionDe(servicio) + 1)
}

/** Registra algo que hay que liberar al limpiar la caché (por ejemplo, fotos descargadas). */
export function alLimpiar(fn: () => void) {
  alLimpiarFns.add(fn)
}

/** Borra todo lo guardado. Se llama al iniciar y al cerrar sesión. */
export function limpiarCache() {
  generacion++
  entradas.clear()
  versiones.clear()
  for (const fn of alLimpiarFns) fn()
}

// Edades predefinidas
export const TODA_LA_SESION = Infinity
// Para la segunda pasada de una carga compuesta: si se acaba de pedir, no se repite
export const RECIEN_PEDIDO = 3000

export interface Pasada {
  maxEdad: number
  // true en la segunda pasada: no muestra "Cargando…" ni reemplaza datos por errores
  silencioso: boolean
}

/**
 * Para cargas que combinan varias consultas (por ejemplo, diagnósticos + sus tratamientos):
 * 1.ª pasada: usa lo guardado si existe, así la pantalla aparece al instante.
 * 2.ª pasada (por detrás): confirma con la API. Si la 1.ª acaba de pedirlo, no se repite.
 */
export async function cargarEnDosPasadas(cargar: (pasada: Pasada) => Promise<unknown>) {
  await cargar({ maxEdad: TODA_LA_SESION, silencioso: false })
  void cargar({ maxEdad: RECIEN_PEDIDO, silencioso: true })
}
