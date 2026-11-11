<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import DietaFormPanel from '@/components/DietaFormPanel.vue'
import DietasPlanificacion from '@/components/DietasPlanificacion.vue'
import CalendarioActividades, { type VistaCalendario } from '@/components/planificacion/CalendarioActividades.vue'
import IndicadoresDia from '@/components/planificacion/IndicadoresDia.vue'
import ObservacionModal from '@/components/planificacion/ObservacionModal.vue'
import PanelActividad from '@/components/planificacion/PanelActividad.vue'
import PanelCrearActividad from '@/components/planificacion/PanelCrearActividad.vue'
import { actividadesApi, planificacionReferenciasApi } from '@/api/actividades'
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

const tituloMes = computed(() => {
  const texto = `${nombreMes(ancla.value)} ${deIso(ancla.value).getFullYear()}`
  return texto.charAt(0).toUpperCase() + texto.slice(1)
})
const subtitulo = computed(() => {
  if (vista.value === 'dia') return diaLargo(ancla.value)
  if (vista.value === 'mes') return ''
  const a = deIso(rango.value.desde)
  const b = deIso(rango.value.hasta)
  return a.getMonth() === b.getMonth()
    ? `Semana del ${a.getDate()} al ${b.getDate()} de ${nombreMes(rango.value.hasta)}`
    : `Semana del ${a.getDate()} de ${nombreMes(rango.value.desde)} al ${b.getDate()} de ${nombreMes(rango.value.hasta)}`
})

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

async function cargarReferencias() {
  const [rAnimales, rRecintos, rUsuarios] = await Promise.allSettled([
    planificacionReferenciasApi.animales(),
    planificacionReferenciasApi.recintos(),
    planificacionReferenciasApi.usuariosAuditoria(),
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

async function cargarDietas() {
  if (!animales.value.length) {
    dietasPorAnimal.value = {}
    return
  }
  cargandoDietas.value = true
  errorDietas.value = ''
  const resultados = await Promise.allSettled(
    animales.value.map(async (animal) => ({ id: animal.id_animal, dietas: await actividadesApi.dietasPorAnimal(animal.id_animal) })),
  )
  const siguientes: Record<number, Dieta[]> = {}
  const errores: string[] = []
  resultados.forEach((r, i) => {
    if (r.status === 'fulfilled') siguientes[r.value.id] = r.value.dietas
    else {
      const animal = animales.value[i]
      errores.push(`${animal?.nombre ?? animal?.taxonomia.nombre_comun ?? 'un ejemplar'}: ${mensajeError(r.reason, 'no se pudo cargar su historial')}`)
    }
  })
  dietasPorAnimal.value = siguientes
  errorDietas.value = errores.length ? `No se pudieron cargar todos los historiales de dieta (${errores.join('; ')}).` : ''
  cargandoDietas.value = false
}

async function cargarActividades() {
  const { desde, hasta } = rango.value
  cargandoActividades.value = true
  errorActividades.value = ''
  try {
    const lista = await actividadesApi.listar({ fecha_desde: desde, fecha_hasta: hasta })
    if (desde !== rango.value.desde) return
    actividades.value = lista
  } catch (error) {
    errorActividades.value = mensajeError(error, 'No se pudieron cargar las actividades.')
    actividades.value = []
  } finally {
    cargandoActividades.value = false
  }
  // Los contadores de observaciones son un extra: si fallan, el calendario sigue funcionando
  try {
    const obs = await actividadesApi.observacionesEnRango(desde, hasta)
    const conteoObs: Record<number, number> = {}
    for (const o of obs) conteoObs[o.id_actividad] = (conteoObs[o.id_actividad] ?? 0) + 1
    obsPorActividad.value = conteoObs
  } catch {
    obsPorActividad.value = {}
  }
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
}

async function completar(actividad: Actividad) {
  if (actividad.completada || actualizandoId.value !== null) return
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

async function actividadCreada(actividad: Actividad) {
  borrador.value = null
  ancla.value = actividad.fecha_programada
  tipos[actividad.tipo_actividad] = true
  await cargarActividades()
  abrirDetalle(porId(actividad.id_actividad) ?? actividad)
  avisar(`${TIPO_LABEL[actividad.tipo_actividad]} creada para el ${diaLargo(actividad.fecha_programada).toLowerCase()}`)
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
  if (nueva === 'dietas') void cargarDietas()
  else void cargarActividades()
}

const tituloObs = computed(() => (obsActividad.value ? d.value.titulo(obsActividad.value) : ''))
const subtituloObs = computed(() =>
  obsActividad.value
    ? `${diaLargo(obsActividad.value.fecha_programada)}${obsActividad.value.hora_programada ? `, ${horaCorta(obsActividad.value)}` : ''}`
    : '',
)

onMounted(async () => {
  await cargarReferencias()
  await cargarDietas()
  let errorRenovacion = ''
  try {
    await actividadesApi.renovarTomas()
  } catch (error) {
    errorRenovacion = `No se pudo renovar el horizonte de alimentaciones: ${mensajeError(error, 'error desconocido')}`
  }
  try {
    await actividadesApi.renovarTratamientos()
  } catch (error) {
    errorRenovacion = [
      errorRenovacion,
      `No se pudo renovar el horizonte de tratamientos: ${mensajeError(error, 'error desconocido')}`,
    ]
      .filter(Boolean)
      .join(' ')
  }
  await cargarActividades()
  if (errorRenovacion) errorActividades.value = [errorActividades.value, errorRenovacion].filter(Boolean).join(' ')
})
</script>

<template>
  <main class="planning-page">
    <p v-if="errorReferencias" class="alert-error" role="alert">{{ errorReferencias }}</p>

    <section v-if="pestana === 'actividades'" role="tabpanel" class="actividades">
      <p v-if="errorActividades" class="alert-error" role="alert">{{ errorActividades }}</p>

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

      <div class="actividades-layout">
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

        <section class="cal" aria-label="Calendario de actividades">
        <header class="cal-top">
          <div class="cal-tit">
            <h2>{{ tituloMes }}</h2>
            <span v-if="subtitulo">{{ subtitulo }}</span>
          </div>
          <span class="grow" />
          <span v-if="cargandoActividades" class="cargando" role="status">Cargando…</span>
          <button class="pill" type="button" @click="ancla = hoy">Hoy</button>
          <div class="nav">
            <button type="button" aria-label="Anterior" @click="mover(-1)">‹</button>
            <button type="button" aria-label="Siguiente" @click="mover(1)">›</button>
          </div>
          <div class="seg" role="group" aria-label="Vista del calendario">
            <button v-for="v in VISTAS" :key="v.id" type="button" :class="{ on: vista === v.id }" @click="vista = v.id">{{ v.texto }}</button>
          </div>
          <button class="btn btn-primary crear" type="button" @click="abrirCrear(ancla, '')">+ Crear actividad</button>
        </header>

        <div class="leyenda">
          <div class="leyenda-tipos" aria-label="Filtrar por tipo de actividad">
            <button
              v-for="t in TIPOS_ACTIVIDAD"
              :key="t"
              type="button"
              class="ley"
              :class="[`t-${t}`, { off: !tipos[t] }]"
              :aria-pressed="tipos[t]"
              @click="tipos[t] = !tipos[t]"
            >
              <span class="dot" />{{ TIPO_LABEL[t] }} <span class="cnt">{{ conteo[t] }}</span>
            </button>
          </div>
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
        </div>

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
            :actualizando-id="actualizandoId"
            :fantasma="panel?.modo === 'crear' ? borrador : null"
            @abrir="(a) => abrirDetalle(a)"
            @lista="abrirLista"
            @crear="abrirCrear"
            @completar="completar"
            @observar="observar"
            @ver-dia="verDia"
          />

          <PanelCrearActividad
            v-if="panel?.modo === 'crear'"
            :animales="animales"
            :recintos="recintos"
            :fecha="panel.fecha"
            :hora="panel.hora"
            :id-animal="idAnimal || undefined"
            @close="cerrarPanel"
            @creada="actividadCreada"
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
  padding: 4px;
  margin-bottom: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  scrollbar-width: thin;
}

.actividades-layout {
  display: grid;
  grid-template-columns: minmax(210px, 250px) minmax(0, 1fr);
  align-items: start;
  gap: 14px;
}

.indicadores-compactos {
  min-width: 0;
}

.indicadores-compactos :deep(.indicadores) {
  gap: 9px;
  margin: 0;
}

.indicadores-compactos :deep(.ind-h) {
  display: grid;
  gap: 3px;
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
}

.indicadores-compactos :deep(.ind) {
  grid-template-columns: 32px minmax(0, 1fr) 36px;
  gap: 9px;
  min-height: 58px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
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
  border-radius: 20px;
  background: #fffefb;
}

.cal-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 16px 20px 12px;
}

.cal-tit h2 {
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.cal-tit span {
  font-size: 13px;
  color: var(--color-text-muted);
}

.grow {
  flex: 1;
}

.cargando {
  font-size: 12px;
  color: var(--color-text-muted);
}

.pill {
  height: 34px;
  padding: 0 16px;
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
  width: 34px;
  height: 34px;
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
  padding: 6px 14px;
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

.leyenda {
  display: grid;
  margin: 0 20px 14px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.leyenda-tipos {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 3px;
}

.filtros-calendario {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--color-border);
}

.ley {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 9px;
  border: none;
  border-radius: 999px;
  background: none;
  font-size: 12px;
  font-weight: 500;
}

.ley:hover {
  background: var(--color-surface-alt);
}

.ley .dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--c);
}

.ley .cnt {
  font-size: 11.5px;
  color: var(--color-text-subtle);
  font-variant-numeric: tabular-nums;
}

.ley.off {
  color: var(--color-text-subtle);
  text-decoration: line-through;
}

.ley.off .dot {
  background: transparent;
  box-shadow: inset 0 0 0 1.5px var(--c);
}

.leyenda select {
  height: 30px;
  min-width: 180px;
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
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    z-index: 45;
    width: min(360px, 100%);
    max-height: none;
    box-shadow: 0 14px 40px rgba(35, 40, 31, 0.18);
  }
}

@media (max-width: 1050px) {
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

  .leyenda {
    margin-right: 10px;
    margin-left: 10px;
  }

  .filtros-calendario {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .leyenda select {
    width: 100%;
  }
}
</style>
