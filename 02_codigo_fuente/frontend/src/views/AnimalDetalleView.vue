<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AnimalFoto from '@/components/AnimalFoto.vue'
import AnimalFormModal from '@/components/AnimalFormModal.vue'
import AppBadge from '@/components/AppBadge.vue'
import SalidaModal from '@/components/SalidaModal.vue'
import VeterinariaPanel from '@/components/VeterinariaPanel.vue'
import { actividadesApi } from '@/api/actividades'
import { animalesApi } from '@/api/animales'
import { veterinariaApi } from '@/api/veterinaria'
import { ApiError } from '@/api/http'
import { ESTADOS_ANIMAL, ESTADOS_SALIDA, SEXOS, formatearFecha, hoyIso, nombreClase } from '@/config/animales'
import { MODULO_PLANIFICACION } from '@/config/modulos'
import { useAuthStore } from '@/stores/auth'
import type { Animal } from '@/types/animales'
import type { Actividad, Dieta } from '@/types/actividades'
import type { Diagnostico, Tratamiento } from '@/types/veterinaria'

const props = defineProps<{ id: string }>()

const auth = useAuthStore()
const puedeVerPlanificacion = computed(() => auth.tieneAcceso(MODULO_PLANIFICACION))

const animal = ref<Animal | null>(null)
const cargando = ref(true)
const error = ref('')
const tab = ref<'resumen' | 'veterinaria'>('veterinaria')
const editarAbierto = ref(false)
const salidaAbierta = ref(false)
const menuAbierto = ref(false)

// Veterinaria: diagnósticos para la línea de vida y tratamientos para la tarjeta "Hoy"
const diagnosticos = ref<Diagnostico[]>([])
const tratamientos = ref<Tratamiento[]>([])
const cargandoDiagnosticos = ref(false)
const errorDiagnosticos = ref('')

// Planificación: resumen de dieta vigente y actividades de alimentación de hoy
const dietaVigente = ref<Dieta | null>(null)
const dietas = ref<Dieta[]>([])
const actividades = ref<Actividad[]>([])
const cargandoPlanificacion = ref(false)
const errorPlanificacion = ref('')

const paginaLineaVida = ref(1)
const eventosPorPagina = 5

// Ficha guardada pero foto sin subir (puede venir del registro, en la URL)
const route = useRoute()
const router = useRouter()
const aviso = ref(typeof route.query.aviso === 'string' ? route.query.aviso : '')
if (route.query.aviso) router.replace({ query: {} })

const yaSalio = computed(() => !!animal.value && ESTADOS_SALIDA.includes(animal.value.estado_actual))
const estado = computed(() => (animal.value ? ESTADOS_ANIMAL[animal.value.estado_actual] : null))

// ---- Fechas y horas ----

function sumarDias(fecha: string, dias: number) {
  const [anio, mes, dia] = fecha.split('-').map(Number)
  const resultado = new Date(anio!, mes! - 1, dia! + dias)
  const m = String(resultado.getMonth() + 1).padStart(2, '0')
  const d = String(resultado.getDate()).padStart(2, '0')
  return `${resultado.getFullYear()}-${m}-${d}`
}

function horaCorta(hora: string | null) {
  return hora ? hora.slice(0, 5) : 'Todo el día'
}

function horaActual() {
  const ahora = new Date()
  return `${String(ahora.getHours()).padStart(2, '0')}:${String(ahora.getMinutes()).padStart(2, '0')}`
}

// ---- Dieta y actividades ----

function resumenDieta(dieta: Dieta) {
  return dieta.alimentos.map((alimento) => alimento.nombre_alimento).join(' + ') || 'Sin alimentos'
}

function formatearEdad(anios: number | null, meses: number | null, legado: string | null | undefined) {
  if (anios === null || meses === null) return legado ?? 'No registrada'
  return `${anios} ${anios === 1 ? 'año' : 'años'} y ${meses} ${meses === 1 ? 'mes' : 'meses'}`
}

const actividadesVigentes = computed(() =>
  actividades.value
    .filter((actividad) => !actividad.cancelada)
    .sort(
      (a, b) =>
        a.fecha_programada.localeCompare(b.fecha_programada) ||
        (a.hora_programada ?? '').localeCompare(b.hora_programada ?? ''),
    ),
)
const actividadesHoy = computed(() => actividadesVigentes.value.filter((a) => a.fecha_programada === hoyIso()))

const tomasHoy = computed(() => actividadesHoy.value.filter((a) => a.tipo_actividad === 'alimentacion'))

// Lo que se muestra en la fila "Alimentación" de la tarjeta Hoy
const estadoAlimentacion = computed<{ texto: string; tono: 'ok' | 'pendiente' | 'atrasada' | 'neutro' }>(() => {
  if (!tomasHoy.value.length) return { texto: 'Sin tomas hoy', tono: 'neutro' }
  const pendientes = tomasHoy.value.filter((toma) => !toma.completada)
  if (!pendientes.length) return { texto: 'Tomas completas', tono: 'ok' }
  const ahora = horaActual()
  const atrasada = pendientes.find((toma) => toma.hora_programada && toma.hora_programada.slice(0, 5) < ahora)
  if (atrasada) return { texto: `Toma atrasada ${horaCorta(atrasada.hora_programada)}`, tono: 'atrasada' }
  return { texto: `Próxima toma ${horaCorta(pendientes[0]!.hora_programada)}`, tono: 'pendiente' }
})

const tratamientosEnCurso = computed(() => tratamientos.value.filter((t) => t.estado === 'en_curso'))

// ---- Línea de vida ----

type EventoLineaVida =
  | { tipo: 'ingreso'; fecha: string; clave: string }
  | { tipo: 'diagnostico'; fecha: string; clave: string; datos: Diagnostico }
  | { tipo: 'dieta'; fecha: string; clave: string; datos: Dieta }
  | { tipo: 'salida'; fecha: null; clave: string }

// Del más reciente al más antiguo; la salida (sin fecha registrada) va primero
const eventosLineaVida = computed<EventoLineaVida[]>(() => {
  if (!animal.value) return []
  const eventos: EventoLineaVida[] = [
    { tipo: 'ingreso', fecha: animal.value.fecha_ingreso, clave: 'ingreso' },
    ...diagnosticos.value.map((diagnostico) => ({
      tipo: 'diagnostico' as const,
      fecha: diagnostico.fecha_registro,
      clave: `diagnostico-${diagnostico.id_diagnostico}`,
      datos: diagnostico,
    })),
    ...dietas.value.map((dieta) => ({
      tipo: 'dieta' as const,
      fecha: dieta.fecha_inicio,
      clave: `dieta-${dieta.id_dieta}`,
      datos: dieta,
    })),
  ]
  if (yaSalio.value) eventos.push({ tipo: 'salida', fecha: null, clave: 'salida' })
  return eventos.sort((a, b) => {
    if (a.fecha === null) return b.fecha === null ? 0 : -1
    if (b.fecha === null) return 1
    return b.fecha.slice(0, 10).localeCompare(a.fecha.slice(0, 10))
  })
})
const paginasLineaVida = computed(() => Math.max(1, Math.ceil(eventosLineaVida.value.length / eventosPorPagina)))
const eventosLineaVidaPaginados = computed(() => {
  const inicio = (paginaLineaVida.value - 1) * eventosPorPagina
  return eventosLineaVida.value.slice(inicio, inicio + eventosPorPagina)
})

// ---- Carga de datos ----

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    animal.value = await animalesApi.obtener(Number(props.id))
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo cargar la ficha'
  } finally {
    cargando.value = false
  }
}

async function cargarDiagnosticos() {
  const idAnimal = Number(props.id)
  cargandoDiagnosticos.value = true
  errorDiagnosticos.value = ''
  try {
    const registros = await veterinariaApi.listarDiagnosticos(idAnimal)
    const listas = await Promise.all(
      registros.map((diagnostico) => veterinariaApi.listarTratamientos(diagnostico.id_diagnostico)),
    )
    if (idAnimal !== Number(props.id)) return
    diagnosticos.value = registros
    tratamientos.value = listas.flat()
  } catch (e) {
    if (idAnimal === Number(props.id)) {
      errorDiagnosticos.value =
        e instanceof ApiError ? e.message : 'No se pudieron cargar los registros veterinarios'
    }
  } finally {
    if (idAnimal === Number(props.id)) cargandoDiagnosticos.value = false
  }
}

async function cargarPlanificacion() {
  if (!puedeVerPlanificacion.value) return
  const idAnimal = Number(props.id)
  const hoy = hoyIso()
  cargandoPlanificacion.value = true
  errorPlanificacion.value = ''
  try {
    const [vigente, historial, programadas] = await Promise.all([
      // Sin dieta vigente el servicio responde 404: no es un error para la ficha
      actividadesApi.dietaVigente(idAnimal).catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null
        throw e
      }),
      actividadesApi.dietasPorAnimal(idAnimal),
      actividadesApi.listar({ id_animal: idAnimal, fecha_desde: hoy, fecha_hasta: sumarDias(hoy, 7) }),
    ])
    if (idAnimal !== Number(props.id)) return
    dietaVigente.value = vigente
    dietas.value = historial
    actividades.value = programadas
  } catch (e) {
    if (idAnimal === Number(props.id)) {
      errorPlanificacion.value =
        e instanceof ApiError ? e.message : 'No se pudieron cargar las actividades del ejemplar'
    }
  } finally {
    if (idAnimal === Number(props.id)) cargandoPlanificacion.value = false
  }
}

function onGuardado(actualizado: Animal, nuevoAviso?: string) {
  animal.value = actualizado
  aviso.value = nuevoAviso ?? ''
  editarAbierto.value = false
  salidaAbierta.value = false
}

// ---- Menú de más acciones ----

function abrirSalida() {
  menuAbierto.value = false
  salidaAbierta.value = true
}

function cerrarMenuSiSaleFoco(evento: FocusEvent) {
  const destino = evento.relatedTarget as Node | null
  if (!destino || !(evento.currentTarget as HTMLElement).contains(destino)) menuAbierto.value = false
}

watch(
  () => props.id,
  () => {
    diagnosticos.value = []
    tratamientos.value = []
    dietaVigente.value = null
    dietas.value = []
    actividades.value = []
    paginaLineaVida.value = 1
    tab.value = 'veterinaria'
    void cargar()
  },
  { immediate: true },
)

// El resumen consulta sus datos al abrirse; Veterinaria tiene su propio panel.
watch(tab, (valor) => {
  if (valor === 'resumen') {
    void cargarDiagnosticos()
    void cargarPlanificacion()
  }
})
</script>

<template>
  <RouterLink :to="{ name: 'fichas' }" class="volver">‹ Volver a fichas</RouterLink>

  <p v-if="aviso" class="alert-error aviso">
    {{ aviso }} Puedes volver a adjuntarla desde «Editar ficha».
    <button type="button" aria-label="Cerrar aviso" @click="aviso = ''">×</button>
  </p>

  <p v-if="cargando" class="vacio">Cargando ficha…</p>
  <p v-else-if="error" class="alert-error">{{ error }}</p>

  <template v-else-if="animal">
    <!-- ---- Cabecera ---- -->
    <header class="cabecera">
      <AnimalFoto :url="animal.url_imagen" :nombre="animal.taxonomia.nombre_comun" class="foto" />

      <div class="identidad">
        <div class="titulo">
          <h1>{{ animal.nombre ?? animal.taxonomia.nombre_comun }}</h1>
          <AppBadge v-if="estado" :tone="estado.tono">{{ estado.label }}</AppBadge>
        </div>
        <p class="especie">
          <template v-if="animal.nombre">{{ animal.taxonomia.nombre_comun }} · </template>
          <em>{{ animal.taxonomia.especie }}</em>
        </p>
        <p class="meta">
          <span class="mono">{{ animal.codigo_animal }}</span> · Recinto
          <span class="mono">{{ animal.recinto.nombre_recinto }}</span>
        </p>
      </div>

      <div class="acciones">
        <button class="btn btn-primary" @click="editarAbierto = true">Editar ficha</button>
        <div class="menu" @focusout="cerrarMenuSiSaleFoco" @keydown.esc="menuAbierto = false">
          <button
            type="button"
            class="btn-mas"
            aria-label="Más acciones"
            aria-haspopup="menu"
            :aria-expanded="menuAbierto"
            @click="menuAbierto = !menuAbierto"
          >
            ⋯
          </button>
          <div v-if="menuAbierto" class="menu-lista" role="menu">
            <button type="button" role="menuitem" class="peligro" :disabled="yaSalio" @click="abrirSalida">
              {{ yaSalio ? 'Salida registrada' : 'Registrar salida' }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- ---- Pestañas ---- -->
    <nav class="tabs" aria-label="Secciones de la ficha">
      <button :class="{ activo: tab === 'resumen' }" @click="tab = 'resumen'">Resumen</button>
      <button :class="{ activo: tab === 'veterinaria' }" @click="tab = 'veterinaria'">Veterinaria</button>
    </nav>

    <!-- ---- Resumen ---- -->
    <div v-if="tab === 'resumen'" class="resumen">
      <article class="panel">
        <h2>Ficha técnica completa</h2>

        <div class="grupos">
          <section>
            <h3>Identificación</h3>
            <dl>
              <div>
                <dt>Código</dt>
                <dd><span class="mono">{{ animal.codigo_animal }}</span> <span class="auto">· automático</span></dd>
              </div>
              <div>
                <dt>Nombre del ejemplar</dt>
                <dd>{{ animal.nombre ?? '—' }}</dd>
              </div>
              <div>
                <dt>Nombre común</dt>
                <dd>{{ animal.taxonomia.nombre_comun }}</dd>
              </div>
              <div>
                <dt>Sexo</dt>
                <dd>{{ animal.sexo ? SEXOS[animal.sexo] : '—' }}</dd>
              </div>
              <div>
                <dt>Edad</dt>
                <dd>{{ formatearEdad(animal.edad_anios, animal.edad_meses, animal.edad_aproximada) }}</dd>
              </div>
            </dl>
          </section>

          <section>
            <h3>Taxonomía</h3>
            <dl>
              <div>
                <dt>Clase</dt>
                <dd>{{ nombreClase(animal.taxonomia.clase) }}</dd>
              </div>
              <div>
                <dt>Orden</dt>
                <dd>{{ animal.taxonomia.orden ?? '—' }}</dd>
              </div>
              <div>
                <dt>Familia</dt>
                <dd>{{ animal.taxonomia.familia ?? '—' }}</dd>
              </div>
              <div>
                <dt>Género</dt>
                <dd><em>{{ animal.taxonomia.genero ?? '—' }}</em></dd>
              </div>
              <div>
                <dt>Nombre científico</dt>
                <dd><em>{{ animal.taxonomia.especie }}</em></dd>
              </div>
            </dl>
          </section>

          <section class="estancia">
            <h3>Estancia</h3>
            <dl>
              <div>
                <dt>Lugar de estancia</dt>
                <dd>
                  <span class="mono">{{ animal.recinto.nombre_recinto }}</span>
                  <template v-if="animal.recinto.tipo"> · {{ animal.recinto.tipo }}</template>
                </dd>
              </div>
              <div>
                <dt>Estado</dt>
                <dd><AppBadge v-if="estado" :tone="estado.tono">{{ estado.label }}</AppBadge></dd>
              </div>
              <div>
                <dt>Fecha de ingreso</dt>
                <dd>{{ formatearFecha(animal.fecha_ingreso) }}</dd>
              </div>
              <div>
                <dt>Fecha de salida</dt>
                <dd :class="{ apagado: yaSalio }">{{ yaSalio ? 'Sin fecha registrada' : '—' }}</dd>
              </div>
            </dl>
          </section>
        </div>
      </article>

      <div class="columna">
        <article v-if="puedeVerPlanificacion" class="panel">
          <div class="panel-cabecera">
            <h2>Hoy</h2>
            <RouterLink :to="{ name: 'planificacion' }" class="enlace">Ver planificación</RouterLink>
          </div>

          <p v-if="cargandoPlanificacion && !actividades.length" class="estado-linea">Cargando…</p>
          <p v-else-if="errorPlanificacion" class="alert-error error-linea">
            {{ errorPlanificacion }}
            <button type="button" class="accion-reintentar" @click="cargarPlanificacion">Reintentar</button>
          </p>
          <dl v-else class="hoy">
            <div>
              <dt>Dieta vigente</dt>
              <dd>{{ dietaVigente ? resumenDieta(dietaVigente) : 'Sin dieta vigente' }}</dd>
            </div>
            <div>
              <dt>Alimentación</dt>
              <dd class="alimentacion" :class="estadoAlimentacion.tono">
                <span v-if="estadoAlimentacion.tono !== 'neutro'" class="punto" aria-hidden="true" />
                {{ estadoAlimentacion.texto }}
              </dd>
            </div>
            <div v-if="tomasHoy.length">
              <dt>Tomas</dt>
              <dd class="tomas">
                <span
                  v-for="toma in tomasHoy"
                  :key="toma.id_actividad"
                  class="toma"
                  :class="{ hecha: toma.completada }"
                  :title="toma.completada ? 'Realizada' : 'Pendiente'"
                >
                  {{ horaCorta(toma.hora_programada) }}
                </span>
              </dd>
            </div>
            <div>
              <dt>Tratamiento</dt>
              <dd>
                <template v-if="tratamientosEnCurso.length">
                  {{ tratamientosEnCurso.map((t) => t.descripcion).join(', ') }}
                </template>
                <template v-else>Ninguno en curso</template>
              </dd>
            </div>
          </dl>
        </article>

        <article class="panel">
          <h2>Línea de vida</h2>
          <ol class="linea">
            <li v-for="evento in eventosLineaVidaPaginados" :key="evento.clave">
              <time>{{ evento.fecha ? formatearFecha(evento.fecha.slice(0, 10)) : '—' }}</time>
              <template v-if="evento.tipo === 'ingreso'">
                <AppBadge tone="green">Ingreso</AppBadge>
                <span>Ingreso al centro · {{ animal.recinto.nombre_recinto }}</span>
              </template>
              <template v-else-if="evento.tipo === 'diagnostico'">
                <AppBadge :tone="evento.datos.es_critico ? 'amber' : 'blue'">Diagnóstico</AppBadge>
                <span class="texto-evento">
                  {{ evento.datos.diagnostico }}
                  <strong v-if="evento.datos.es_critico"> · Crítico</strong>
                </span>
              </template>
              <template v-else-if="evento.tipo === 'dieta'">
                <AppBadge tone="gray">Dieta</AppBadge>
                <span class="texto-evento">
                  {{ evento.datos.es_restriccion ? 'Inicio de restricción' : 'Inicio de dieta' }}:
                  {{ resumenDieta(evento.datos) }}
                </span>
              </template>
              <template v-else>
                <AppBadge :tone="estado?.tono">Salida</AppBadge>
                <span>{{ estado?.label }}</span>
              </template>
            </li>
          </ol>
          <p v-if="cargandoDiagnosticos" class="estado-linea">Cargando registros veterinarios…</p>
          <p v-else-if="errorDiagnosticos" class="alert-error error-linea">
            {{ errorDiagnosticos }}
            <button type="button" class="accion-reintentar" @click="cargarDiagnosticos">Reintentar</button>
          </p>
          <nav v-if="eventosLineaVida.length > eventosPorPagina" class="paginacion" aria-label="Paginación de la línea de vida">
            <button type="button" class="btn btn-secondary" :disabled="paginaLineaVida === 1" @click="paginaLineaVida--">
              Anterior
            </button>
            <span>Página {{ paginaLineaVida }} de {{ paginasLineaVida }}</span>
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="paginaLineaVida === paginasLineaVida"
              @click="paginaLineaVida++"
            >
              Siguiente
            </button>
          </nav>
          <p class="linea-ayuda">Eventos del ejemplar, del más reciente al más antiguo</p>
        </article>
      </div>
    </div>

    <!-- ---- Veterinaria ---- -->
    <VeterinariaPanel
      v-else-if="tab === 'veterinaria'"
      :id-animal="animal.id_animal"
      :nombre-ejemplar="animal.nombre ?? animal.taxonomia.nombre_comun"
    />

  </template>

  <AnimalFormModal :open="editarAbierto" :animal="animal" @close="editarAbierto = false" @saved="onGuardado" />
  <SalidaModal :open="salidaAbierta" :animal="animal" @close="salidaAbierta = false" @saved="onGuardado" />
</template>

<style scoped>
.volver {
  display: inline-block;
  margin-bottom: 14px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.volver:hover {
  color: var(--color-text);
}

.aviso {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.aviso button {
  border: none;
  background: none;
  font-size: 18px;
  line-height: 1;
  color: inherit;
}

.cabecera,
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

/* ---- Cabecera ---- */

.cabecera {
  display: grid;
  grid-template-columns: 188px minmax(0, 1fr) auto;
  gap: 24px;
  align-items: start;
  padding: 20px;
}

.foto {
  height: 150px;
  border-radius: var(--radius-md);
}

.identidad {
  padding-top: 8px;
}

.titulo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

h1 {
  font-family: var(--font-serif);
  font-size: 32px;
  font-weight: 600;
  line-height: 1.15;
}

.especie {
  margin-top: 14px;
  font-size: 16px;
  color: var(--color-text-muted);
}

.meta {
  margin-top: 14px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.acciones {
  display: flex;
  gap: 10px;
}

.acciones .btn-primary {
  padding: 11px 20px;
}

.menu {
  position: relative;
}

.btn-mas {
  width: 38px;
  height: 38px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: 16px;
  line-height: 1;
}

.btn-mas:hover,
.btn-mas[aria-expanded='true'] {
  background: var(--color-surface-alt);
  color: var(--color-text);
}

.menu-lista {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 10;
  min-width: 190px;
  padding: 6px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.menu-lista button {
  width: 100%;
  padding: 9px 12px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  text-align: left;
  font-size: 13px;
  font-weight: 500;
}

.menu-lista button:hover:not(:disabled) {
  background: var(--color-danger-soft);
}

.menu-lista .peligro {
  color: var(--color-danger);
}

.menu-lista button:disabled {
  color: var(--color-text-subtle);
  cursor: default;
}

/* ---- Pestañas ---- */

.tabs {
  display: flex;
  gap: 4px;
  margin: 18px 0 22px;
  border-bottom: 1px solid var(--color-border);
}

.tabs button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.tabs button.activo {
  border-bottom-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.contador {
  min-width: 20px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--color-surface-alt);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-align: center;
}

/* ---- Paneles ---- */

.resumen {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

.columna {
  display: grid;
  gap: 22px;
}

.panel {
  padding: 24px 26px;
}

.panel h2 {
  font-size: 18px;
  font-weight: 700;
}

.panel-cabecera {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.enlace {
  border: none;
  background: none;
  padding: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-primary);
}

.enlace:hover {
  text-decoration: underline;
}

.sub {
  margin-top: 16px;
  font-size: 14px;
  color: var(--color-text-muted);
}

dl {
  margin: 0;
}

dl > div {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 11px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 14px;
}

dt {
  color: var(--color-text-muted);
}

dd {
  margin: 0;
  font-weight: 500;
  text-align: right;
}

.mono {
  font-family: ui-monospace, 'Cascadia Code', monospace;
}

.auto {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-muted);
}

.apagado {
  font-weight: 400;
  color: var(--color-text-muted);
}

/* Ficha técnica: Identificación y Taxonomía lado a lado, Estancia debajo a todo el ancho */

.grupos {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px 34px;
  margin-top: 26px;
}

.grupos h3 {
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.estancia {
  grid-column: 1 / -1;
}

.estancia dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 34px;
}

/* Tarjeta Hoy */

.hoy {
  margin-top: 18px;
}

.hoy > div {
  border-bottom-style: dashed;
}

.hoy > div:last-child {
  border-bottom: none;
}

.alimentacion {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.punto {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.alimentacion.pendiente {
  color: #87661a;
}

.alimentacion.atrasada {
  color: var(--color-danger);
}

.alimentacion.ok {
  color: var(--color-primary);
}

.alimentacion.neutro {
  color: var(--color-text-muted);
  font-weight: 400;
}

.tomas {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.toma {
  padding: 3px 9px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-alt);
  font-size: 12px;
  color: var(--color-text-muted);
}

.toma.hecha {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  text-decoration: line-through;
}

/* Línea de vida */

.linea {
  margin-top: 14px;
  padding: 0;
  list-style: none;
}

.linea-ayuda {
  margin-top: 12px;
  padding-top: 9px;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-subtle);
  font-size: 11px;
}

.linea li {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 7px 0;
  font-size: 14px;
}

.linea time {
  min-width: 100px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.linea :deep(.badge) {
  padding: 5px 11px;
  border-radius: 999px;
  font-size: 12px;
}

.texto-evento {
  min-width: 0;
  overflow-wrap: anywhere;
}

.texto-evento strong {
  color: #87661a;
}

.estado-linea {
  margin-top: 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.error-linea {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding: 10px 12px;
}

.accion-reintentar {
  border: 0;
  background: none;
  color: var(--color-primary);
  font-weight: 600;
}

.paginacion {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 14px;
  margin-top: 16px;
}

.paginacion span {
  color: var(--color-text-muted);
  font-size: 12px;
}

.vacio {
  padding: 48px;
  text-align: center;
  color: var(--color-text-muted);
}

@media (max-width: 1100px) {
  .resumen {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .cabecera {
    grid-template-columns: 1fr;
  }

  .foto {
    height: 200px;
  }

  .grupos,
  .estancia dl {
    grid-template-columns: 1fr;
  }

  .tabs {
    overflow-x: auto;
  }
}

@media (max-width: 600px) {
  .panel {
    padding: 18px;
  }

  .linea li {
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
