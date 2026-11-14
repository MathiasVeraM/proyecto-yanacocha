<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import DietaFormPanel from '@/components/DietaFormPanel.vue'
import DietasPlanificacion from '@/components/DietasPlanificacion.vue'
import CalendarioActividades, { type VistaCalendario } from '@/components/planificacion/CalendarioActividades.vue'
import IndicadoresDia from '@/components/planificacion/IndicadoresDia.vue'
import ObservacionModal from '@/components/planificacion/ObservacionModal.vue'
import PanelActividad from '@/components/planificacion/PanelActividad.vue'
import PanelCrearActividad from '@/components/planificacion/PanelCrearActividad.vue'
import { actividadesApi, renovarHorizonteDeSesion } from '@/api/actividades'
import { cargarEnDosPasadas, fijar, type Pasada } from '@/api/cache'
import { clavesCache, consultas } from '@/api/consultas'
import { ApiError } from '@/api/http'
import {
  TIPOS_ACTIVIDAD,
  TIPO_LABEL,
  deIso,
  describirActividades,
  diaLargo,
  generaAlerta,
  horaCorta,
  lunesDe,
  nombreMes,
  sumarDias,
  type ContextoActividades,
} from '@/config/actividades'
import { useAhora } from '@/composables/useAhora'
import { useAuthStore } from '@/stores/auth'
import type { Actividad, Dieta, Observacion, ObservacionCreate, TipoActividad, UsuarioActividad } from '@/types/actividades'
import type { Animal, Recinto } from '@/types/animales'

type Pestana = 'actividades' | 'dietas'
type EstadoFiltro = 'todas' | 'pend' | 'hechas'
type Panel =
  | { modo: 'detalle'; id: number; volver: { clave: string; titulo: string; ids: number[] } | null }
  | { modo: 'lista'; clave: string; titulo: string; ids: number[] }
  | { modo: 'crear'; fecha: string; hora: string }
  | { modo: 'editar'; id: number }

const auth = useAuthStore()
const { hoy, hora: ahora } = useAhora()

// Checklist y Monitoreo de alimentación ahora viven dentro de "Actividades" (indicadores + calendario)
const pestañas: { id: Pestana; texto: string }[] = [
  { id: 'actividades', texto: 'Actividades' },
  { id: 'dietas', texto: 'Registro de Dietas' },
]
const VISTAS: { id: VistaCalendario; texto: string }[] = [
  { id: 'dia', texto: 'Día' },
  { id: 'semana', texto: 'Semana' },
  { id: 'mes', texto: 'Mes' },
]

const pestana = ref<Pestana>('actividades')
const animales = ref<Animal[]>([])
const recintos = ref<Recinto[]>([])
const usuariosAuditoria = ref<UsuarioActividad[]>([])
const actividades = ref<Actividad[]>([])
const obsPorActividad = ref<Record<number, number>>({})
const dietasPorAnimal = ref<Record<number, Dieta[]>>({})
const extrasPorDieta = ref<Record<number, { unidades: ('g' | 'kg' | 'unidad')[]; restriccion: boolean }>>({})
const cargandoActividades = ref(false)
const cargandoDietas = ref(false)
const actualizandoId = ref<number | null>(null)
const errorReferencias = ref('')
const errorActividades = ref('')
const errorDietas = ref('')
const formularioDietaAbierto = ref(false)

// Calendario y filtros
const vista = ref<VistaCalendario>('semana')
const ancla = ref(hoy.value)
const tipos = reactive<Record<TipoActividad, boolean>>({
  alimentacion: true,
  enriquecimiento: true,
  entrenamiento: true,
  limpieza: true,
  tratamiento: false,
})
const idAnimal = ref(0)
const estado = ref<EstadoFiltro>('todas')

// Panel derecho, observaciones y avisos
const panel = ref<Panel | null>(null)
const actividadEnfoque = ref<number | null>(null)
const borrador = ref<{ fecha: string; hora: string; minutos: number } | null>(null)
const observacionesPanel = ref<Observacion[]>([])
const cargandoObsPanel = ref(false)
const obsActividad = ref<Actividad | null>(null)
const guardandoObs = ref(false)
const errorObs = ref('')
const aviso = ref('')
let temporizadorAviso: ReturnType<typeof setTimeout> | undefined

// ---- Datos derivados ----

const dietasVigentes = computed(() => {
  const resultado: Record<number, Dieta> = {}
  for (const [id, historial] of Object.entries(dietasPorAnimal.value)) {
    const vigente = historial.find((dieta) => dieta.vigente)
    if (vigente) resultado[Number(id)] = vigente
  }
  return resultado
})

const dietasPorId = computed(() => {
  const resultado: Record<number, Dieta> = {}
  for (const historial of Object.values(dietasPorAnimal.value)) for (const dieta of historial) resultado[dieta.id_dieta] = dieta
  return resultado
})

const ctx = computed<ContextoActividades>(() => ({
  animales: animales.value,
  recintos: recintos.value,
  dietasPorId: dietasPorId.value,
  usuarios: usuariosAuditoria.value,
}))
const d = computed(() => describirActividades(ctx.value))

// Rango que se pide al servicio según la vista
const rango = computed(() => {
  if (vista.value === 'dia') return { desde: ancla.value, hasta: ancla.value }
  if (vista.value === 'semana') {
    const desde = lunesDe(ancla.value)
    return { desde, hasta: sumarDias(desde, 6) }
  }
  const a = deIso(ancla.value)
  const primero = `${a.getFullYear()}-${String(a.getMonth() + 1).padStart(2, '0')}-01`
  const ultimo = new Date(a.getFullYear(), a.getMonth() + 1, 0, 12)
  const desde = lunesDe(primero)
  const dias = Math.round((ultimo.getTime() - deIso(desde).getTime()) / 864e5) + 1
  return { desde, hasta: sumarDias(desde, Math.ceil(dias / 7) * 7 - 1) }
})

// El filtro de ejemplar también incluye las limpiezas de su recinto
function pasaAnimal(a: Actividad) {
  if (!idAnimal.value) return true
  if (a.tipo_actividad === 'limpieza') return a.id_recinto === d.value.animal(idAnimal.value)?.id_recinto
  return a.id_animal === idAnimal.value
}

const visibles = computed(() => actividades.value.filter((a) => !a.cancelada && pasaAnimal(a)))
const delCalendario = computed(() =>
  visibles.value.filter((a) => {
    if (!tipos[a.tipo_actividad]) return false
    if (estado.value === 'pend') return !a.completada
    if (estado.value === 'hechas') return a.completada
    return true
  }),
)
const delDia = computed(() => visibles.value.filter((a) => a.fecha_programada === ancla.value))
const conteo = computed(() => {
  const c: Record<TipoActividad, number> = {
    alimentacion: 0,
    enriquecimiento: 0,
    entrenamiento: 0,
    limpieza: 0,
    tratamiento: 0,
  }
  for (const a of visibles.value) c[a.tipo_actividad]++
  return c
})

const tiposVisibles = computed(() => TIPOS_ACTIVIDAD.filter((t) => tipos[t]).length)

// El menú de tipos se cierra al hacer clic fuera de él o con Escape
const menuTipos = ref<HTMLDetailsElement | null>(null)
function cerrarMenuTipos(evento?: MouseEvent) {
  const menu = menuTipos.value
  if (menu?.open && (!evento || !menu.contains(evento.target as Node))) menu.open = false
}
onMounted(() => document.addEventListener('click', cerrarMenuTipos))
onBeforeUnmount(() => document.removeEventListener('click', cerrarMenuTipos))

const tituloMes = computed(() => {
  const texto = `${nombreMes(ancla.value)} ${deIso(ancla.value).getFullYear()}`
  return texto.charAt(0).toUpperCase() + texto.slice(1)
})
// Corto, para que la cabecera quepa en una fila: el mes ya está en el título
const subtitulo = computed(() => {
  if (vista.value === 'dia') {
    const dia = deIso(ancla.value)
    const nombre = dia.toLocaleDateString('es-EC', { weekday: 'long' })
    return `${nombre.charAt(0).toUpperCase()}${nombre.slice(1)} ${dia.getDate()}`
  }
  if (vista.value === 'mes') return ''
  const a = deIso(rango.value.desde)
  const b = deIso(rango.value.hasta)
  return a.getMonth() === b.getMonth()
    ? `Semana del ${a.getDate()} al ${b.getDate()}`
    : `Semana del ${a.getDate()} ${nombreMes(rango.value.desde).slice(0, 3)} al ${b.getDate()} ${nombreMes(rango.value.hasta).slice(0, 3)}`
})

// Toda la información de fechas va en la cabecera del calendario: el rango que se ve y hoy con la hora
const textoHoy = computed(() => {
  const fecha = deIso(hoy.value)
  return `Hoy ${fecha.toLocaleDateString('es-EC', { weekday: 'long' })} ${fecha.getDate()} · ${ahora.value}`
})
const lineaFechas = computed(() =>
  // En la vista de día de hoy, el día ya está en "Hoy …": no se repite
  vista.value === 'dia' && ancla.value === hoy.value
    ? textoHoy.value
    : [subtitulo.value, textoHoy.value].filter(Boolean).join(' · '),
)

const porId = (id: number) => actividades.value.find((a) => a.id_actividad === id) ?? null
const actividadPanel = computed(() => (panel.value?.modo === 'detalle' ? porId(panel.value.id) : null))
const itemsPanel = computed(() =>
  panel.value?.modo === 'lista' ? panel.value.ids.map(porId).filter((a): a is Actividad => !!a) : [],
)
const seleccion = computed(() => {
  if (!panel.value) return null
  if (panel.value.modo === 'detalle') return panel.value.volver?.clave ?? `a-${panel.value.id}`
  if (panel.value.modo === 'lista') return panel.value.clave
  return null
})

// ---- Carga ----

function mensajeError(error: unknown, predeterminado: string) {
  return error instanceof ApiError ? error.message : predeterminado
}

// Animales: se muestran los guardados y se confirman por detrás. Recintos y usuarios: una vez por sesión
async function cargarReferencias() {
  const [rAnimales, rRecintos, rUsuarios] = await Promise.allSettled([
    consultas.animales({}, { alActualizar: (lista) => (animales.value = lista) }),
    consultas.recintos(),
    consultas.usuariosAuditoria(),
  ])
  const errores: string[] = []
  if (rAnimales.status === 'fulfilled') animales.value = rAnimales.value
  else errores.push(`ejemplares: ${mensajeError(rAnimales.reason, 'no se pudieron cargar')}`)
  if (rRecintos.status === 'fulfilled') recintos.value = rRecintos.value
  else errores.push(`recintos: ${mensajeError(rRecintos.reason, 'no se pudieron cargar')}`)
  if (rUsuarios.status === 'fulfilled') usuariosAuditoria.value = rUsuarios.value
  else errores.push(`usuarios: ${mensajeError(rUsuarios.reason, 'no se pudieron cargar')}`)
  errorReferencias.value = errores.length ? `No se pudieron cargar algunos datos de referencia (${errores.join('; ')}).` : ''
}

// El historial de dietas de todos los animales llega en una sola petición (antes, una por animal)
async function cargarDietas({ maxEdad, silencioso }: Pasada = { maxEdad: 0, silencioso: false }) {
  if (!silencioso) {
    cargandoDietas.value = true
    errorDietas.value = ''
  }
  try {
    const todas = await consultas.todasLasDietas({ maxEdad })
    const siguientes: Record<number, Dieta[]> = {}
    // Llegan ordenadas por animal y de la más reciente a la más antigua
    for (const dieta of todas) (siguientes[dieta.id_animal] ??= []).push(dieta)
    dietasPorAnimal.value = siguientes
  } catch (error) {
    // En la revalidación por detrás, si falla se conserva lo que ya se mostraba
    if (!silencioso) errorDietas.value = `No se pudieron cargar los historiales de dieta: ${mensajeError(error, 'error desconocido')}`
  } finally {
    if (!silencioso) cargandoDietas.value = false
  }
}

function contarObservaciones(obs: Observacion[]) {
  const conteoObs: Record<number, number> = {}
  for (const o of obs) conteoObs[o.id_actividad] = (conteoObs[o.id_actividad] ?? 0) + 1
  return conteoObs
}

// Cada rango (semana, día o mes) se guarda en la caché: al volver a uno ya visitado aparece al
// instante y se confirma con la API por detrás.
// fresco: espera la respuesta de la API · silencioso: no muestra "Cargando…" ni errores
async function cargarActividades({ fresco = false, silencioso = false } = {}) {
  const { desde, hasta } = rango.value
  const filtros = { fecha_desde: desde, fecha_hasta: hasta }
  const esElRangoActual = () => desde === rango.value.desde && hasta === rango.value.hasta
  if (!silencioso) {
    cargandoActividades.value = true
    errorActividades.value = ''
  }
  try {
    const lista = await consultas.actividades(
      filtros,
      fresco ? {} : { alActualizar: (nueva) => esElRangoActual() && (actividades.value = nueva) },
    )
    if (!esElRangoActual()) return
    actividades.value = lista
  } catch (error) {
    if (silencioso || !esElRangoActual()) return
    errorActividades.value = mensajeError(error, 'No se pudieron cargar las actividades.')
    actividades.value = []
  } finally {
    if (!silencioso) cargandoActividades.value = false
  }
  // Los contadores de observaciones son un extra: si fallan, el calendario sigue funcionando
  try {
    const obs = await consultas.observacionesEnRango(
      desde,
      hasta,
      fresco
        ? {}
        : { alActualizar: (nuevas) => esElRangoActual() && (obsPorActividad.value = contarObservaciones(nuevas)) },
    )
    if (esElRangoActual()) obsPorActividad.value = contarObservaciones(obs)
  } catch {
    if (!silencioso && esElRangoActual()) obsPorActividad.value = {}
  }
}

// Lo que el usuario cambió (completar, reabrir, observar) ya está en pantalla: se guarda tal cual
// en la caché del rango, para que al volver no haya que pedirlo de nuevo
function guardarRangoEnCache() {
  const { desde, hasta } = rango.value
  fijar(clavesCache.actividades({ fecha_desde: desde, fecha_hasta: hasta }), actividades.value)
}

watch(() => `${rango.value.desde}|${rango.value.hasta}`, () => void cargarActividades())

async function cargarObservacionesPanel(id: number) {
  cargandoObsPanel.value = true
  try {
    const lista = await actividadesApi.observaciones(id)
    if (panel.value?.modo === 'detalle' && panel.value.id === id) observacionesPanel.value = lista
  } catch {
    observacionesPanel.value = []
  } finally {
    cargandoObsPanel.value = false
  }
}

// ---- Acciones ----

function avisar(texto: string) {
  aviso.value = texto
  clearTimeout(temporizadorAviso)
  temporizadorAviso = setTimeout(() => (aviso.value = ''), 4000)
}

function reemplazar(actualizada: Actividad) {
  actividades.value = actividades.value.map((a) => (a.id_actividad === actualizada.id_actividad ? { ...a, ...actualizada } : a))
  guardarRangoEnCache()
}

async function completar(actividad: Actividad) {
  if (actividad.completada || actualizandoId.value !== null) return
  if (actividad.fecha_programada > hoy.value) {
    avisar('Solo se pueden completar actividades de hoy o de días anteriores')
    return
  }
  const original = { ...actividad }
  actualizandoId.value = actividad.id_actividad
  errorActividades.value = ''
  reemplazar({ ...actividad, completada: true, id_usuario_completo: auth.payload?.id_usuario ?? null, fecha_completada: new Date().toISOString() })
  try {
    reemplazar(await actividadesApi.completar(actividad.id_actividad))
    avisar(`${d.value.titulo(actividad)} marcada como hecha`)
  } catch (error) {
    reemplazar(original)
    errorActividades.value = mensajeError(error, 'No se pudo completar la actividad. Se restauró su estado anterior.')
  } finally {
    actualizandoId.value = null
  }
}

async function reabrir(actividad: Actividad) {
  if (!actividad.completada || actualizandoId.value !== null) return
  actualizandoId.value = actividad.id_actividad
  errorActividades.value = ''
  try {
    reemplazar(await actividadesApi.reabrir(actividad.id_actividad))
    avisar(`${d.value.titulo(actividad)} quedó pendiente`)
  } catch (error) {
    errorActividades.value = mensajeError(error, 'No se pudo marcar la actividad como pendiente.')
  } finally {
    actualizandoId.value = null
  }
}

function abrirDetalle(actividad: Actividad, desdeLista = false) {
  const volver = desdeLista && panel.value?.modo === 'lista'
    ? { clave: panel.value.clave, titulo: panel.value.titulo, ids: panel.value.ids }
    : null
  panel.value = { modo: 'detalle', id: actividad.id_actividad, volver }
  observacionesPanel.value = []
  void cargarObservacionesPanel(actividad.id_actividad)
}

function abrirLista(clave: string, titulo: string, items: Actividad[]) {
  panel.value = { modo: 'lista', clave, titulo, ids: items.map((a) => a.id_actividad) }
}

function volverALista() {
  if (panel.value?.modo === 'detalle' && panel.value.volver) panel.value = { modo: 'lista', ...panel.value.volver }
}

function abrirCrear(fecha: string, hora: string) {
  panel.value = { modo: 'crear', fecha: fecha || ancla.value, hora }
}

function cerrarPanel() {
  panel.value = null
  borrador.value = null
}

async function actividadCreada(actividad: Actividad, cantidad = 1) {
  borrador.value = null
  // Lleva al día y a la hora de la actividad creada: el mes no tiene horas, así que se pasa a la semana
  if (vista.value === 'mes') vista.value = 'semana'
  ancla.value = actividad.fecha_programada
  estado.value = 'todas'
  actividadEnfoque.value = actividad.id_actividad
  tipos[actividad.tipo_actividad] = true
  await cargarActividades()
  abrirDetalle(porId(actividad.id_actividad) ?? actividad)
  avisar(
    cantidad > 1
      ? `${cantidad} actividades de ${TIPO_LABEL[actividad.tipo_actividad].toLowerCase()} creadas desde el ${diaLargo(actividad.fecha_programada).toLowerCase()}`
      : `${TIPO_LABEL[actividad.tipo_actividad]} creada para el ${diaLargo(actividad.fecha_programada).toLowerCase()}`,
  )
}

// Al guardar cambios se va al día y la hora nuevos de la actividad, como al crearla
async function actividadEditada(actividad: Actividad) {
  borrador.value = null
  if (vista.value === 'mes') vista.value = 'semana'
  ancla.value = actividad.fecha_programada
  actividadEnfoque.value = actividad.id_actividad
  await cargarActividades()
  abrirDetalle(porId(actividad.id_actividad) ?? actividad)
  avisar('Cambios guardados')
}

async function eliminarActividad(actividad: Actividad) {
  const titulo = d.value.titulo(actividad)
  if (!window.confirm(`¿Eliminar "${titulo}" del ${diaLargo(actividad.fecha_programada).toLowerCase()}? También se borran sus observaciones. No se puede deshacer.`)) return
  actualizandoId.value = actividad.id_actividad
  try {
    await actividadesApi.eliminar(actividad.id_actividad)
    actividades.value = actividades.value.filter((a) => a.id_actividad !== actividad.id_actividad)
    guardarRangoEnCache()
    cerrarPanel()
    avisar(`${titulo} eliminada`)
  } catch (error) {
    errorActividades.value = mensajeError(error, 'No se pudo eliminar la actividad.')
  } finally {
    actualizandoId.value = null
  }
}

function observar(actividad: Actividad) {
  errorObs.value = ''
  obsActividad.value = actividad
}

async function guardarObservacion(datos: ObservacionCreate, marcarHecha: boolean) {
  const actividad = obsActividad.value
  if (!actividad) return
  guardandoObs.value = true
  errorObs.value = ''
  try {
    const creada = await actividadesApi.agregarObservacion(actividad.id_actividad, datos)
    obsPorActividad.value = { ...obsPorActividad.value, [actividad.id_actividad]: (obsPorActividad.value[actividad.id_actividad] ?? 0) + 1 }
    guardarRangoEnCache()
    obsActividad.value = null
    if (panel.value?.modo === 'detalle' && panel.value.id === actividad.id_actividad) {
      observacionesPanel.value = [...observacionesPanel.value, creada]
    } else {
      abrirDetalle(actividad)
    }
    avisar(creada.genera_alerta || generaAlerta(datos.categoria, datos.severidad)
      ? 'Observación guardada · se generó una alerta para el veterinario'
      : 'Observación guardada')
    const actual = porId(actividad.id_actividad)
    if (marcarHecha && actual && !actual.completada) await completar(actual)
  } catch (error) {
    errorObs.value = mensajeError(error, 'No se pudo guardar la observación.')
  } finally {
    guardandoObs.value = false
  }
}

function mover(paso: number) {
  if (vista.value === 'mes') {
    const a = deIso(ancla.value)
    const destino = new Date(a.getFullYear(), a.getMonth() + paso, 1, 12)
    ancla.value = `${destino.getFullYear()}-${String(destino.getMonth() + 1).padStart(2, '0')}-01`
  } else {
    ancla.value = sumarDias(ancla.value, vista.value === 'dia' ? paso : paso * 7)
  }
}

function verDia(fecha: string) {
  ancla.value = fecha
  vista.value = 'dia'
}

async function finalizarDieta(dieta: Dieta) {
  try {
    await actividadesApi.finalizarDieta(dieta.id_dieta)
    avisar('Dieta finalizada')
  } catch (error) {
    errorDietas.value = mensajeError(error, 'No se pudo finalizar la dieta.')
  }
  await cargarDietas()
  void cargarActividades({ fresco: true, silencioso: true })
}

async function cambiarFinDieta(dieta: Dieta, fechaFin: string | null) {
  try {
    await actividadesApi.cambiarFinDieta(dieta.id_dieta, fechaFin)
    avisar(fechaFin ? 'Fecha de fin guardada' : 'La dieta ya no tiene fecha de fin')
  } catch (error) {
    errorDietas.value = mensajeError(error, 'No se pudo cambiar la fecha de fin.')
  }
  await cargarDietas()
  void cargarActividades({ fresco: true, silencioso: true })
}

async function guardarDieta(dieta: Dieta, extras: { unidades: ('g' | 'kg' | 'unidad')[]; restriccion: boolean }) {
  formularioDietaAbierto.value = false
  extrasPorDieta.value = { ...extrasPorDieta.value, [dieta.id_dieta]: extras }
  await cargarDietas()
  try {
    await actividadesApi.generarTomas(dieta.id_dieta)
  } catch (error) {
    errorDietas.value = `La dieta se registró, pero no se pudieron generar sus alimentaciones: ${mensajeError(error, 'error desconocido')}`
  }
  await cargarActividades()
}

function cambiarPestana(nueva: Pestana) {
  pestana.value = nueva
  formularioDietaAbierto.value = false
  if (nueva === 'dietas') void cargarEnDosPasadas(cargarDietas)
  else void cargarActividades()
}

const tituloObs = computed(() => (obsActividad.value ? d.value.titulo(obsActividad.value) : ''))
const subtituloObs = computed(() =>
  obsActividad.value
    ? `${diaLargo(obsActividad.value.fecha_programada)}${obsActividad.value.hora_programada ? `, ${horaCorta(obsActividad.value)}` : ''}`
    : '',
)

// Las tomas y dosis de los próximos días se completan por detrás, sin bloquear la pantalla.
// Al terminar se refresca el rango que se está viendo por si aparecieron actividades nuevas.
async function renovarHorizonte() {
  const [tomas, tratamientos] = await renovarHorizonteDeSesion()
  const errores: string[] = []
  if (tomas?.status === 'rejected') {
    errores.push(`No se pudo renovar el horizonte de alimentaciones: ${mensajeError(tomas.reason, 'error desconocido')}`)
  }
  if (tratamientos?.status === 'rejected') {
    errores.push(`No se pudo renovar el horizonte de tratamientos: ${mensajeError(tratamientos.reason, 'error desconocido')}`)
  }
  if (errores.length) errorActividades.value = [errorActividades.value, ...errores].filter(Boolean).join(' ')
  await cargarActividades({ fresco: true, silencioso: true })
}

// Todo se pide a la vez: el calendario aparece apenas llegan las actividades, sin esperar
// a los datos de referencia, a las dietas ni a la renovación
onMounted(() => {
  void cargarActividades()
  void cargarReferencias()
  void cargarEnDosPasadas(cargarDietas)
  void renovarHorizonte()
})
</script>

<template>
  <main class="planning-page" :class="{ 'pagina-calendario': pestana === 'actividades' }">
    <p v-if="errorReferencias" class="alert-error" role="alert">{{ errorReferencias }}</p>

    <section v-if="pestana === 'actividades'" role="tabpanel" class="actividades">
      <p v-if="errorActividades" class="alert-error" role="alert">{{ errorActividades }}</p>

      <div class="actividades-layout">
        <!-- Columna izquierda: pestañas arriba y el resumen de hoy debajo; así el calendario
             empieza a la misma altura que las pestañas -->
        <div class="columna-izquierda">
          <nav class="planning-tabs" role="tablist" aria-label="Secciones de planificación">
            <button
              v-for="tab in pestañas"
              :key="tab.id"
              class="planning-tab"
              :class="{ active: pestana === tab.id }"
              type="button"
              role="tab"
              :aria-selected="pestana === tab.id"
              @click="cambiarPestana(tab.id)"
            >
              {{ tab.texto }}
            </button>
          </nav>

          <IndicadoresDia
            class="indicadores-compactos"
            :fecha="ancla"
            :actividades="delDia"
            :ctx="ctx"
            :hoy="hoy"
            :ahora="ahora"
            :obs-por-actividad="obsPorActividad"
            :actualizando-id="actualizandoId"
            @completar="completar"
            @observar="observar"
            @abrir="(a) => abrirDetalle(a)"
          />
        </div>

        <section class="cal" aria-label="Calendario de actividades">
        <header class="cal-top">
          <div class="cal-tit">
            <h2>{{ tituloMes }}</h2>
            <span>{{ lineaFechas }}</span>
          </div>
          <!-- Todo en una sola fila: tipos (también filtran), filtros y navegación -->
          <!-- El espacio libre va después del título: filtros y navegación quedan juntos a la derecha -->
          <span class="grow" />
          <!-- Tipos de actividad: lista con casillas para mostrar u ocultar cada tipo -->
          <details ref="menuTipos" class="tipos-menu" @keydown.esc="cerrarMenuTipos()">
            <summary class="tipos-boton" aria-label="Filtrar por tipo de actividad">
              <span class="tipos-puntos" aria-hidden="true">
                <span v-for="t in TIPOS_ACTIVIDAD" :key="t" class="dot" :class="[`t-${t}`, { off: !tipos[t] }]" />
              </span>
              Tipos
              <span class="cnt">{{ tiposVisibles }}/{{ TIPOS_ACTIVIDAD.length }}</span>
            </summary>
            <div class="tipos-lista" role="group" aria-label="Tipos de actividad visibles">
              <label v-for="t in TIPOS_ACTIVIDAD" :key="t" class="tipo-opcion" :class="`t-${t}`">
                <input v-model="tipos[t]" type="checkbox" />
                <span class="dot" />
                <span class="tipo-nombre">{{ TIPO_LABEL[t] }}</span>
                <span class="cnt">{{ conteo[t] }}</span>
              </label>
            </div>
          </details>
          <div class="filtros-calendario">
            <select v-model.number="idAnimal" aria-label="Filtrar por ejemplar">
              <option :value="0">Todos los ejemplares</option>
              <option v-for="a in animales" :key="a.id_animal" :value="a.id_animal">
                {{ a.nombre ? `${a.nombre} · ${a.taxonomia.nombre_comun}` : a.taxonomia.nombre_comun }}
              </option>
            </select>
            <select v-model="estado" aria-label="Filtrar por estado">
              <option value="todas">Todos los estados</option>
              <option value="pend">Pendientes</option>
              <option value="hechas">Hechas</option>
            </select>
          </div>
          <span v-if="cargandoActividades" class="cargando" role="status">Cargando…</span>
          <button class="pill" type="button" @click="ancla = hoy">Hoy</button>
          <div class="nav">
            <button type="button" aria-label="Anterior" @click="mover(-1)">‹</button>
            <button type="button" aria-label="Siguiente" @click="mover(1)">›</button>
          </div>
          <div class="seg" role="group" aria-label="Vista del calendario">
            <button v-for="v in VISTAS" :key="v.id" type="button" :class="{ on: vista === v.id }" @click="vista = v.id">{{ v.texto }}</button>
          </div>
          <button class="btn btn-primary crear" type="button" aria-label="Crear actividad" title="Crear actividad" @click="abrirCrear(ancla, '')">+ Crear</button>
        </header>

        <div class="cal-cuerpo" :class="{ 'con-panel': panel }">
          <CalendarioActividades
            :vista="vista"
            :ancla="ancla"
            :actividades="delCalendario"
            :ctx="ctx"
            :hoy="hoy"
            :ahora="ahora"
            :obs-por-actividad="obsPorActividad"
            :seleccion="seleccion"
            :enfoque="actividadEnfoque"
            :actualizando-id="actualizandoId"
            :fantasma="panel?.modo === 'crear' || panel?.modo === 'editar' ? borrador : null"
            @abrir="(a) => abrirDetalle(a)"
            @lista="abrirLista"
            @crear="abrirCrear"
            @completar="completar"
            @observar="observar"
            @ver-dia="verDia"
            @enfocado="actividadEnfoque = null"
          />

          <PanelCrearActividad
            v-if="panel?.modo === 'crear' || panel?.modo === 'editar'"
            :animales="animales"
            :recintos="recintos"
            :fecha="panel.modo === 'crear' ? panel.fecha : ''"
            :hora="panel.modo === 'crear' ? panel.hora : ''"
            :id-animal="idAnimal || undefined"
            :actividad="panel.modo === 'editar' ? porId(panel.id) : null"
            @close="cerrarPanel"
            @creada="actividadCreada"
            @editada="actividadEditada"
            @borrador="(b) => (borrador = b)"
          />
          <PanelActividad
            v-else-if="panel"
            :modo="panel.modo"
            :actividad="actividadPanel"
            :items="itemsPanel"
            :titulo-lista="panel.modo === 'lista' ? panel.titulo : ''"
            :volver-a="panel.modo === 'detalle' ? panel.volver?.titulo : undefined"
            :ctx="ctx"
            :hoy="hoy"
            :ahora="ahora"
            :observaciones="observacionesPanel"
            :cargando-observaciones="cargandoObsPanel"
            :obs-por-actividad="obsPorActividad"
            :actualizando-id="actualizandoId"
            @close="cerrarPanel"
            @volver="volverALista"
            @abrir="(a) => abrirDetalle(a, true)"
            @completar="completar"
            @reabrir="reabrir"
            @observar="observar"
            @editar="(a) => (panel = { modo: 'editar', id: a.id_actividad })"
            @eliminar="eliminarActividad"
          />
        </div>
        </section>
      </div>
    </section>

    <section v-else role="tabpanel">
      <nav class="planning-tabs dietas-tabs" role="tablist" aria-label="Secciones de planificación">
        <button
          v-for="tab in pestañas"
          :key="tab.id"
          class="planning-tab"
          :class="{ active: pestana === tab.id }"
          type="button"
          role="tab"
          :aria-selected="pestana === tab.id"
          @click="cambiarPestana(tab.id)"
        >
          {{ tab.texto }}
        </button>
      </nav>
      <DietaFormPanel
        :abierto="formularioDietaAbierto"
        :animales="animales"
        :dietas-vigentes="dietasVigentes"
        :extras-por-dieta="extrasPorDieta"
        @close="formularioDietaAbierto = false"
        @saved="guardarDieta"
      />
      <DietasPlanificacion
        :animales="animales"
        :dietas-vigentes="dietasVigentes"
        :historiales="dietasPorAnimal"
        :extras-por-dieta="extrasPorDieta"
        :cargando="cargandoDietas"
        :error="errorDietas"
        @registrar="formularioDietaAbierto = true"
        @finalizar="finalizarDieta"
        @cambiar-fin="cambiarFinDieta"
      />
    </section>

    <ObservacionModal
      :actividad="obsActividad"
      :titulo="tituloObs"
      :subtitulo="subtituloObs"
      :guardando="guardandoObs"
      :error="errorObs"
      @close="obsActividad = null"
      @guardar="guardarObservacion"
    />

    <div v-if="aviso" class="aviso" role="status">{{ aviso }}</div>
  </main>
</template>

<style>
/* Colores por tipo de actividad (mismos tonos que AppBadge). Globales porque los usan
   el calendario, los indicadores, los paneles y el modal de observación. */
.t-alimentacion {
  --c: #87661a;
  --cb: #f8edcf;
  --cd: #ead79f;
}

.t-limpieza {
  --c: #2d6a9a;
  --cb: #e3eef7;
  --cd: #bcd4e8;
}

.t-enriquecimiento {
  --c: #2e6b34;
  --cb: #e6efdc;
  --cd: #c3d8b0;
}

.t-entrenamiento {
  --c: #4a538f;
  --cb: #e8eaf6;
  --cd: #c8cdea;
}

.planning-page {
  --linea: #e9e3d3;
  --linea-suave: #f3eee2;
  --alim: #87661a;
  --alim-bg: #f8edcf;
}
</style>

<style scoped>
.planning-page {
  min-width: 0;
}

.planning-page > .alert-error,
.actividades > .alert-error {
  margin-bottom: 12px;
}

.planning-tabs {
  display: inline-flex;
  max-width: 100%;
  gap: 4px;
  overflow-x: auto;
  padding: 3px;
  margin-bottom: 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  scrollbar-width: thin;
}

.actividades-layout {
  display: grid;
  grid-template-columns: minmax(200px, 236px) minmax(0, 1fr);
  align-items: start;
  gap: 8px;
}

.columna-izquierda {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* Dentro de la columna, las pestañas ocupan todo el ancho */
.columna-izquierda .planning-tabs {
  display: flex;
}

.columna-izquierda .planning-tab {
  /* Cada pestaña según su texto, sin partirse en dos líneas */
  flex: 1 1 auto;
  white-space: nowrap;
  padding-right: 8px;
  padding-left: 8px;
}

.indicadores-compactos {
  min-width: 0;
  width: 100%;
}

.indicadores-compactos :deep(.indicadores) {
  gap: 9px;
  margin: 0;
}

.indicadores-compactos :deep(.ind-h) {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 1px;
}

.indicadores-compactos :deep(.ind-h h2) {
  font-size: 15px;
}

.indicadores-compactos :deep(.ind-h span) {
  font-size: 11px;
}

.indicadores-compactos :deep(.grid) {
  grid-template-columns: minmax(0, 1fr);
  gap: 7px;
  min-width: 0;
  width: 100%;
}

.indicadores-compactos :deep(.ind) {
  box-sizing: border-box;
  grid-template-columns: 32px minmax(0, 1fr) 36px;
  gap: 7px;
  min-height: 58px;
  min-width: 0;
  width: 100%;
  padding: 7px 8px;
  border-radius: var(--radius-md);
}

.indicadores-compactos :deep(.detalle) {
  box-sizing: border-box;
  min-width: 0;
  max-width: 100%;
  padding: 12px;
}

.indicadores-compactos :deep(.det-h),
.indicadores-compactos :deep(.det-h h3),
.indicadores-compactos :deep(.det-acc),
.indicadores-compactos :deep(.filas) {
  min-width: 0;
  max-width: 100%;
}

.indicadores-compactos :deep(.det-h) {
  align-items: flex-start;
}

.indicadores-compactos :deep(.det-acc) {
  flex-wrap: wrap;
}

.indicadores-compactos :deep(.filas li) {
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  gap: 6px;
  min-width: 0;
}

.indicadores-compactos :deep(.filas li > *) {
  grid-column: 1;
  justify-self: start;
  max-width: 100%;
  min-width: 0;
}

.indicadores-compactos :deep(.filas li .avatar) {
  display: none;
}

.indicadores-compactos :deep(.quien) {
  width: 100%;
}

.indicadores-compactos :deep(.quien small) {
  overflow: visible;
  white-space: normal;
  overflow-wrap: anywhere;
  text-overflow: clip;
}

.indicadores-compactos :deep(.ico) {
  width: 32px;
  height: 32px;
  border-radius: 8px;
}

.indicadores-compactos :deep(.ico svg) {
  width: 18px;
  height: 18px;
}

.indicadores-compactos :deep(.tit) {
  overflow: hidden;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.indicadores-compactos :deep(.big) {
  font-size: 19px;
}

.indicadores-compactos :deep(.big small) {
  font-size: 12px;
}

.indicadores-compactos :deep(.big em) {
  font-size: 11px;
}

.indicadores-compactos :deep(.pie) {
  font-size: 10px;
}

.indicadores-compactos :deep(.ring) {
  width: 36px;
  height: 36px;
}

.indicadores-compactos :deep(.ring span) {
  width: 29px;
  height: 29px;
  font-size: 10px;
}

.indicadores-compactos :deep(.caret) {
  top: 3px;
  right: 5px;
}

.dietas-tabs {
  margin-bottom: 20px;
}

.cal {
  min-width: 0;
}

.planning-tab {
  flex: 0 0 auto;
  padding: 7px 14px;
  border: 0;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--color-text);
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}

.planning-tab:hover,
.planning-tab:focus-visible {
  color: var(--color-primary);
  outline-color: var(--color-primary);
}

.planning-tab.active {
  background: var(--color-primary);
  color: #fff;
}

/* ---- Calendario ---- */
.cal {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: #fffefb;
}

/* Una sola fila siempre: si falta espacio, se angostan los selectores y se recorta el subtítulo
   (en pantallas angostas sí pasa a varias líneas, ver media query) */
.cal-top {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  padding: 10px 16px 8px;
}

.cal-top > * {
  flex-shrink: 0;
}

.cal-tit {
  flex-shrink: 1 !important;
  min-width: 120px;
}

.cal-tit h2 {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.cal-tit span {
  display: block;
  overflow: hidden;
  font-size: 12px;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: var(--color-text-muted);
}

.grow {
  flex: 1;
  min-width: 0;
}

.cargando {
  font-size: 12px;
  color: var(--color-text-muted);
}

.pill {
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--color-border-strong);
  border-radius: 999px;
  background: var(--color-surface);
  font-size: 13px;
  font-weight: 600;
}

.pill:hover {
  background: var(--color-surface-alt);
}

.nav {
  display: inline-flex;
  gap: 2px;
}

.nav button {
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border-strong);
  border-radius: 50%;
  background: var(--color-surface);
  font-size: 17px;
  line-height: 1;
  color: var(--color-text-muted);
}

.nav button:hover {
  background: var(--color-surface-alt);
  color: var(--color-text);
}

.seg {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border-radius: 999px;
  background: var(--color-surface-alt);
}

.seg button {
  padding: 5px 10px;
  border: none;
  border-radius: 999px;
  background: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.seg button.on {
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: 0 1px 3px rgba(35, 40, 31, 0.15);
}

.crear {
  border-radius: 999px;
}

/* ---- Menú "Tipos": lista con casillas, con el mismo aspecto que los selectores ---- */
.tipos-menu {
  position: relative;
}

.tipos-boton {
  display: flex;
  align-items: center;
  gap: 7px;
  height: 30px;
  padding: 0 10px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-alt);
  font-size: 13px;
  list-style: none;
  white-space: nowrap;
  cursor: pointer;
}

.tipos-boton::-webkit-details-marker {
  display: none;
}

.tipos-boton::after {
  content: '⌄';
  margin-top: -5px;
  color: var(--color-text-muted);
}

.tipos-puntos {
  display: inline-flex;
  gap: 3px;
}

.tipos-menu .dot {
  width: 9px;
  height: 9px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--c);
}

.tipos-menu .dot.off {
  background: transparent;
  box-shadow: inset 0 0 0 1.5px var(--c);
}

.tipos-menu .cnt {
  font-size: 12px;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.tipos-lista {
  position: absolute;
  z-index: 30;
  top: calc(100% + 6px);
  left: 0;
  display: grid;
  gap: 2px;
  min-width: 220px;
  padding: 6px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.tipo-opcion {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
}

.tipo-opcion:hover {
  background: var(--color-surface-alt);
}

.tipo-opcion input {
  accent-color: var(--color-primary);
}

.tipo-nombre {
  flex: 1;
}

.filtros-calendario {
  display: flex;
  flex-shrink: 1 !important;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.filtros-calendario select {
  flex: 1 1 165px;
  height: 30px;
  min-width: 96px;
  max-width: 170px;
  text-overflow: ellipsis;
  padding: 0 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-surface-alt);
  font-size: 13px;
}

.cal-cuerpo {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  min-height: 0;
  border-top: 1px solid var(--linea);
}

.cal-cuerpo.con-panel {
  grid-template-columns: minmax(0, 1fr) 340px;
}

.cal-cuerpo > :deep(.panel) {
  max-height: calc(66vh + 50px);
}

/* ---- Pestaña Actividades: la página ocupa exactamente el alto de la ventana ----
   No hay scroll fuera del calendario: la columna "Hoy" y el calendario se desplazan por dentro.
   En pantallas angostas (una sola columna) la página vuelve a desplazarse normalmente. */
@media (min-width: 1051px) {
  .planning-page.pagina-calendario {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
  }

  .pagina-calendario > .alert-error {
    flex-shrink: 0;
  }

  .pagina-calendario .actividades {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 0;
  }

  .pagina-calendario .actividades > .alert-error {
    flex-shrink: 0;
  }

  .pagina-calendario .actividades-layout {
    flex: 1;
    grid-template-rows: minmax(0, 1fr);
    align-items: stretch;
    min-height: 0;
  }

  .pagina-calendario .columna-izquierda {
    min-height: 0;
    overflow-y: auto;
    scrollbar-width: thin;
  }

  .pagina-calendario .cal {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .pagina-calendario .cal-top {
    flex-shrink: 0;
  }

  .pagina-calendario .cal-cuerpo {
    flex: 1;
    grid-template-rows: minmax(0, 1fr);
  }

  .pagina-calendario .cal-cuerpo > :deep(.panel) {
    max-height: 100%;
  }
}

/* Pantallas angostas: el calendario vuelve a tener una altura fija con scroll propio */
@media (max-width: 1050px) {
  .cal-cuerpo :deep(.rejilla),
  .cal-cuerpo :deep(.mes) {
    height: auto;
  }

  .cal-cuerpo :deep(.scroll) {
    max-height: 66vh;
  }
}

.aviso {
  position: fixed;
  bottom: 20px;
  left: 50%;
  z-index: 60;
  padding: 10px 16px;
  border-radius: var(--radius-md);
  background: var(--color-dark);
  color: #faf7ee;
  font-weight: 500;
  box-shadow: 0 14px 40px rgba(35, 40, 31, 0.18);
  transform: translateX(-50%);
}

@media (max-width: 1180px) {
  .cal-cuerpo.con-panel {
    grid-template-columns: minmax(0, 1fr);
  }

  .cal-cuerpo > :deep(.panel) {
    position: static;
    width: auto;
    max-height: min(70vh, 680px);
    border-top: 1px solid var(--color-border);
    border-left: 0;
    box-shadow: none;
  }
}

@media (max-width: 1050px) {
  .cal-top {
    flex-wrap: wrap;
  }

  .actividades-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .indicadores-compactos :deep(.grid) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .planning-tabs {
    display: flex;
  }

  .filtros-calendario {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    width: 100%;
    margin-left: 0;
  }

  .filtros-calendario select {
    width: 100%;
    max-width: none;
  }
}
</style>
