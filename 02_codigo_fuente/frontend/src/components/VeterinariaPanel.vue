<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import AppBadge from '@/components/AppBadge.vue'
import VeterinariaRegistroModal from '@/components/VeterinariaRegistroModal.vue'
import { ApiError } from '@/api/http'
import { cargarEnDosPasadas, type Pasada } from '@/api/cache'
import { consultas } from '@/api/consultas'
import { formatearFecha } from '@/config/animales'
import { useAuthStore } from '@/stores/auth'
import type {
  Diagnostico,
  SignosVitales,
  SignosVitalesHistorial,
  Tratamiento,
  UnidadFrecuenciaTratamiento,
} from '@/types/veterinaria'

// fechaIngreso: para que un tratamiento no empiece antes del ingreso del animal
const props = defineProps<{ idAnimal: number; nombreEjemplar?: string; fechaIngreso?: string }>()

// Registrar y editar es solo de Veterinaria; Administración consulta y genera el PDF
const auth = useAuthStore()

type RegistroExistente =
  | { tipo: 'diagnostico'; datos: Diagnostico }
  | { tipo: 'tratamiento'; datos: Tratamiento }

const diagnosticos = ref<Diagnostico[]>([])
const tratamientos = ref<Record<number, Tratamiento[]>>({})
const cargando = ref(true)
const error = ref('')
const modalAbierto = ref(false)
const registroEditando = ref<RegistroExistente | null>(null)
const tipoNuevo = ref<'diagnostico' | 'tratamiento'>('diagnostico')
const paginaHistorial = ref(1)
// Cuántas tarjetas caben en el alto de la tarjeta de signos vitales (se mide; ver más abajo)
const registrosPorPagina = ref(4)
const pestanaHistorial = ref<'recientes' | 'historial'>('historial')
const diagnosticoSeleccionado = ref<Diagnostico | null>(null)

const cantidadTratamientos = computed(
  () => Object.values(tratamientos.value).reduce((total, items) => total + items.length, 0),
)
// Historial de signos vitales en orden cronológico (el más antiguo primero)
const historialSignos = ref<SignosVitalesHistorial[]>([])
const historialOrdenado = computed(() =>
  [...historialSignos.value].sort(
    (a, b) => new Date(a.fecha_diagnostico).getTime() - new Date(b.fecha_diagnostico).getTime(),
  ),
)
// La última revisión es el registro más reciente que trae signos vitales
const signosUltimaRevision = computed(() => historialOrdenado.value.at(-1) ?? null)

type ClaveNumerica =
  | 'peso_kg'
  | 'temperatura_c'
  | 'frecuencia_cardiaca_lpm'
  | 'frecuencia_respiratoria_rpm'
  | 'tiempo_llenado_capilar_s'

const SIGNOS_NUMERICOS: { clave: ClaveNumerica; etiqueta: string; unidad: string; decimales: number }[] = [
  { clave: 'peso_kg', etiqueta: 'Peso', unidad: 'kg', decimales: 3 },
  { clave: 'temperatura_c', etiqueta: 'Temperatura', unidad: '°C', decimales: 1 },
  { clave: 'frecuencia_cardiaca_lpm', etiqueta: 'Frec. cardíaca', unidad: 'lpm', decimales: 0 },
  { clave: 'frecuencia_respiratoria_rpm', etiqueta: 'Frec. respiratoria', unidad: 'rpm', decimales: 0 },
  { clave: 'tiempo_llenado_capilar_s', etiqueta: 'Llenado capilar', unidad: 's', decimales: 1 },
]

// Medidas del sparkline (en unidades del viewBox)
const SPARK_ANCHO = 72
const SPARK_ALTO = 22
const SPARK_PUNTOS = 10

const tarjetasNumericas = computed(() =>
  SIGNOS_NUMERICOS.map(({ clave, etiqueta, unidad, decimales }) => {
    const actual = signosUltimaRevision.value?.[clave] ?? null
    const serie = historialOrdenado.value
      .map((s) => s[clave])
      .filter((v): v is number => v !== null)
      .slice(-SPARK_PUNTOS)

    // Variación respecto al registro anterior que tenga este signo
    let variacion: string | null = null
    if (actual !== null && serie.length >= 2) {
      const anterior = serie[serie.length - 2]!
      const diferencia = Number((actual - anterior).toFixed(decimales))
      variacion =
        diferencia === 0
          ? '='
          : `${diferencia > 0 ? '▲' : '▼'} ${formatoNumero(Math.abs(diferencia), decimales)}`
    }

    let puntos = ''
    if (serie.length >= 2) {
      const minimo = Math.min(...serie)
      const rango = Math.max(...serie) - minimo || 1
      puntos = serie
        .map((v, i) => {
          const x = (i / (serie.length - 1)) * SPARK_ANCHO
          // Con todos los valores iguales la línea queda centrada
          const y = Math.max(...serie) === minimo ? SPARK_ALTO / 2 : SPARK_ALTO - 2 - ((v - minimo) / rango) * (SPARK_ALTO - 4)
          return `${x.toFixed(1)},${y.toFixed(1)}`
        })
        .join(' ')
    }

    return {
      clave,
      etiqueta,
      valor: actual !== null ? `${formatoNumero(actual, decimales)} ${unidad}` : '—',
      variacion,
      puntos,
    }
  }),
)

// Signos categóricos: se resaltan los valores fuera de lo normal
const tarjetasCategoricas = computed(() => {
  const s = signosUltimaRevision.value
  return [
    {
      clave: 'hidratacion',
      etiqueta: 'Hidratación',
      valor: s?.hidratacion ? etiquetaCategoria(s.hidratacion) : '—',
      anomalo: !!s?.hidratacion && s.hidratacion !== 'normal',
    },
    {
      clave: 'mucosas',
      etiqueta: 'Mucosas',
      valor: s?.mucosas ? etiquetaCategoria(s.mucosas) : '—',
      anomalo: !!s?.mucosas && s.mucosas !== 'rosadas',
    },
    {
      clave: 'actitud',
      etiqueta: 'Actitud',
      valor: s?.actitud ? etiquetaCategoria(s.actitud) : '—',
      anomalo: !!s?.actitud && s.actitud !== 'alerta',
    },
  ]
})

function fechaCorta(fecha: string) {
  const valor = new Date(fecha)
  const mismoAnio = valor.getFullYear() === new Date().getFullYear()
  return new Intl.DateTimeFormat('es-EC', {
    day: 'numeric',
    month: 'short',
    ...(mismoAnio ? {} : { year: 'numeric' }),
  }).format(valor)
}
const diagnosticosOrdenados = computed(() =>
  [...diagnosticos.value].sort(
    (a, b) => new Date(b.fecha_registro).getTime() - new Date(a.fecha_registro).getTime(),
  ),
)
const diagnosticoReciente = computed(() => diagnosticosOrdenados.value[0] ?? null)
const paginasHistorial = computed(() => Math.max(1, Math.ceil(diagnosticosOrdenados.value.length / registrosPorPagina.value)))
const diagnosticosPaginados = computed(() => {
  const inicio = (paginaHistorial.value - 1) * registrosPorPagina.value
  return diagnosticosOrdenados.value.slice(inicio, inicio + registrosPorPagina.value)
})
const tratamientosOrdenados = computed(() =>
  diagnosticosOrdenados.value
    .flatMap((diagnostico) =>
      (tratamientos.value[diagnostico.id_diagnostico] ?? []).map((tratamiento) => ({
        diagnostico,
        tratamiento,
      })),
    )
    .sort(
      (a, b) =>
        new Date(b.tratamiento.fecha_inicio).getTime() - new Date(a.tratamiento.fecha_inicio).getTime() ||
        new Date(b.diagnostico.fecha_registro).getTime() - new Date(a.diagnostico.fecha_registro).getTime(),
    ),
)
const tratamientoReciente = computed(
  () => tratamientosOrdenados.value.find(({ tratamiento }) => tratamiento.estado === 'en_curso') ?? null,
)
const tratamientosSeleccionados = computed(() =>
  diagnosticoSeleccionado.value
    ? (tratamientos.value[diagnosticoSeleccionado.value.id_diagnostico] ?? [])
    : [],
)

function fechaHora(fecha: string) {
  return new Intl.DateTimeFormat('es-EC', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(fecha))
}

function tonoTratamiento(estado: Tratamiento['estado']) {
  if (estado === 'en_curso') return 'amber'
  if (estado === 'finalizado') return 'green'
  return 'gray'
}

function etiquetaTratamiento(estado: Tratamiento['estado']) {
  if (estado === 'en_curso') return 'En curso'
  if (estado === 'finalizado') return 'Finalizado'
  return 'Suspendido'
}

function etiquetaUnidadFrecuencia(unidad: UnidadFrecuenciaTratamiento | null) {
  if (!unidad) return ''
  return unidad === 'dias' ? 'días' : 'horas'
}

function formatoNumero(valor: number, decimales = 1) {
  return new Intl.NumberFormat('es-EC', { maximumFractionDigits: decimales }).format(valor)
}

function condicionCorporal(valor: number) {
  const etiquetas = ['Caquéctico', 'Delgado', 'Óptimo', 'Sobrepeso', 'Obeso']
  return `${valor}/5 · ${etiquetas[valor - 1]}`
}

function etiquetaCategoria(valor: string) {
  const etiquetas: Record<string, string> = {
    deshidratacion_leve: 'Deshidratación leve',
    deshidratacion_moderada: 'Deshidratación moderada',
    deshidratacion_severa: 'Deshidratación severa',
    palidas: 'Pálidas',
    cianoticas: 'Cianóticas',
    ictericas: 'Ictéricas',
  }
  return etiquetas[valor] ?? valor.charAt(0).toUpperCase() + valor.slice(1)
}

function valoresSignosVitales(signos: SignosVitales | null) {
  if (!signos) return []
  const valores: { etiqueta: string; valor: string }[] = []
  if (signos.peso_kg !== null) valores.push({ etiqueta: 'Peso', valor: `${formatoNumero(signos.peso_kg, 3)} kg` })
  if (signos.temperatura_c !== null) valores.push({ etiqueta: 'Temperatura', valor: `${formatoNumero(signos.temperatura_c)} °C` })
  if (signos.frecuencia_cardiaca_lpm !== null) {
    valores.push({ etiqueta: 'Frec. cardíaca', valor: `${signos.frecuencia_cardiaca_lpm} lpm` })
  }
  if (signos.frecuencia_respiratoria_rpm !== null) {
    valores.push({ etiqueta: 'Frec. respiratoria', valor: `${signos.frecuencia_respiratoria_rpm} rpm` })
  }
  if (signos.tiempo_llenado_capilar_s !== null) {
    valores.push({ etiqueta: 'Llenado capilar', valor: `${formatoNumero(signos.tiempo_llenado_capilar_s)} s` })
  }
  if (signos.hidratacion) valores.push({ etiqueta: 'Hidratación', valor: etiquetaCategoria(signos.hidratacion) })
  if (signos.condicion_corporal !== null) {
    valores.push({ etiqueta: 'Condición corporal', valor: condicionCorporal(signos.condicion_corporal) })
  }
  if (signos.mucosas) valores.push({ etiqueta: 'Mucosas', valor: etiquetaCategoria(signos.mucosas) })
  if (signos.actitud) valores.push({ etiqueta: 'Actitud', valor: etiquetaCategoria(signos.actitud) })
  return valores
}

// ---- Tarjetas resumen del historial ----

const tratamientosDe = (diagnostico: Diagnostico) => tratamientos.value[diagnostico.id_diagnostico] ?? []
const activosDe = (diagnostico: Diagnostico) => tratamientosDe(diagnostico).filter((t) => t.estado === 'en_curso').length
// Total de tratamientos en curso del animal (métrica de la cabecera)
const tratamientosActivos = computed(() =>
  Object.values(tratamientos.value).reduce((total, lista) => total + lista.filter((t) => t.estado === 'en_curso').length, 0),
)

// La lista de tarjetas ocupa el mismo alto que la tarjeta de signos vitales: se mide el espacio
// disponible y se muestran las que entran; las demás van en las páginas siguientes
const ALTO_TARJETA = 74
const ESPACIO_TARJETAS = 8
const listaHistorial = ref<HTMLElement | null>(null)
const pantallaAncha = window.matchMedia('(min-width: 901px)')
const observador = new ResizeObserver(([entrada]) => {
  const alto = entrada?.contentRect.height ?? 0
  // En pantallas angostas (una sola columna) no hay tarjeta de signos al lado: se usan 4 por página
  registrosPorPagina.value = pantallaAncha.matches && alto >= ALTO_TARJETA
    ? Math.max(1, Math.floor((alto + ESPACIO_TARJETAS) / (ALTO_TARJETA + ESPACIO_TARJETAS)))
    : 4
})
watch(listaHistorial, (elemento, anterior) => {
  if (anterior) observador.unobserve(anterior)
  if (elemento) observador.observe(elemento)
})
onBeforeUnmount(() => observador.disconnect())

// ---- Modal de detalle: se elige un tratamiento para ver todo su detalle ----
const tratamientoAbierto = ref<number | null>(null)
watch(diagnosticoSeleccionado, () => (tratamientoAbierto.value = null))
function alternarTratamiento(id: number) {
  tratamientoAbierto.value = tratamientoAbierto.value === id ? null : id
}

function abrirDetalle(diagnostico: Diagnostico) {
  diagnosticoSeleccionado.value = diagnostico
}

function cerrarDetalle() {
  diagnosticoSeleccionado.value = null
}

function editarDiagnosticoSeleccionado() {
  if (!diagnosticoSeleccionado.value) return
  editarDiagnostico(diagnosticoSeleccionado.value)
}

// Usa las mismas claves de caché que la ficha: si ambas piden a la vez, la API recibe un solo pedido
async function cargar({ maxEdad, silencioso }: Pasada = { maxEdad: 0, silencioso: false }) {
  const idAnimal = props.idAnimal
  if (!silencioso) {
    cargando.value = true
    error.value = ''
  }
  try {
    // Las 3 consultas a la vez: 3 peticiones sin importar cuántos diagnósticos haya
    const [registros, delAnimal, signos] = await Promise.all([
      consultas.diagnosticos(idAnimal, { maxEdad }),
      consultas.tratamientosDelAnimal(idAnimal, { maxEdad }),
      // null = el historial de signos falló (se arma abajo con los signos de los diagnósticos)
      consultas.signosVitales(idAnimal, { maxEdad }).catch(() => null),
    ])
    if (idAnimal !== props.idAnimal) return
    // Tratamientos agrupados por diagnóstico, como los usa el historial
    const porDiagnostico: Record<number, Tratamiento[]> = {}
    for (const diagnostico of registros) porDiagnostico[diagnostico.id_diagnostico] = []
    for (const tratamiento of delAnimal) {
      ;(porDiagnostico[tratamiento.id_diagnostico] ??= []).push(tratamiento)
    }
    diagnosticos.value = registros
    tratamientos.value = porDiagnostico
    historialSignos.value =
      signos ??
      registros.flatMap((d) =>
        d.signos_vitales ? [{ ...d.signos_vitales, fecha_diagnostico: d.fecha_registro }] : [],
      )
    if (diagnosticoSeleccionado.value) {
      diagnosticoSeleccionado.value =
        registros.find((d) => d.id_diagnostico === diagnosticoSeleccionado.value?.id_diagnostico) ?? null
    }
  } catch (e) {
    if (idAnimal === props.idAnimal && !silencioso) {
      error.value = e instanceof ApiError ? e.message : 'No se pudo cargar el historial veterinario'
    }
  } finally {
    if (idAnimal === props.idAnimal && !silencioso) cargando.value = false
  }
}

function nuevoDiagnostico() {
  if (!auth.permisos.registrarVeterinaria) return
  registroEditando.value = null
  tipoNuevo.value = 'diagnostico'
  modalAbierto.value = true
}

function editarDiagnostico(datos: Diagnostico) {
  if (!auth.permisos.registrarVeterinaria) return
  registroEditando.value = { tipo: 'diagnostico', datos }
  modalAbierto.value = true
}

function editarTratamiento(datos: Tratamiento) {
  if (!auth.permisos.registrarVeterinaria) return
  registroEditando.value = { tipo: 'tratamiento', datos }
  modalAbierto.value = true
}

watch(
  () => props.idAnimal,
  () => {
    paginaHistorial.value = 1
    // Aparece al instante con lo guardado y se confirma con la API por detrás
    void cargarEnDosPasadas(cargar)
  },
  { immediate: true },
)

watch(paginasHistorial, (total) => {
  if (paginaHistorial.value > total) paginaHistorial.value = total
})
</script>

<template>
  <section class="veterinaria" @keydown.esc="cerrarDetalle">
    <div class="veterinaria-grid">
      <aside class="columna-signos">
        <section class="ultima-revision" aria-label="Signos vitales de la última revisión">
          <header class="ultima-revision-header">
            <h2>
              Signos vitales · última revisión
              <template v-if="signosUltimaRevision">
                ·
                <time
                  :datetime="signosUltimaRevision.fecha_diagnostico"
                  :title="fechaHora(signosUltimaRevision.fecha_diagnostico)"
                >
                  {{ fechaCorta(signosUltimaRevision.fecha_diagnostico) }}
                </time>
              </template>
            </h2>
            <span v-if="signosUltimaRevision?.condicion_corporal" class="condicion">
              Condición corporal: <strong>{{ condicionCorporal(signosUltimaRevision.condicion_corporal) }}</strong>
            </span>
            <span v-else-if="!signosUltimaRevision">Sin signos vitales registrados</span>
          </header>
          <div class="signos-resumen">
            <article v-for="t in tarjetasNumericas" :key="t.clave" class="signo-resumen">
              <span>{{ t.etiqueta }}</span>
              <strong>{{ t.valor }}</strong>
              <div v-if="t.puntos || t.variacion" class="tendencia">
                <svg
                  v-if="t.puntos"
                  :viewBox="`-1 0 ${SPARK_ANCHO + 2} ${SPARK_ALTO}`"
                  :width="SPARK_ANCHO"
                  :height="SPARK_ALTO"
                  aria-hidden="true"
                >
                  <polyline
                    :points="t.puntos"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                <small v-if="t.variacion" :aria-label="`Variación respecto al registro anterior: ${t.variacion}`">
                  {{ t.variacion }}
                </small>
              </div>
            </article>
            <article
              v-for="t in tarjetasCategoricas"
              :key="t.clave"
              class="signo-resumen"
              :class="{ anomalo: t.anomalo }"
            >
              <span>{{ t.etiqueta }}</span>
              <strong>{{ t.valor }}</strong>
            </article>
          </div>
        </section>
      </aside>

      <section class="columna-historial">
        <!-- La cabecera (título, contadores y acciones) se muestra en la barra de pestañas de la ficha -->
        <Teleport defer to="#acciones-pestanas-ficha">
          <div class="historial-cabecera">
            <div>
              <h2>Historial clínico</h2>
              <p>{{ diagnosticos.length }} {{ diagnosticos.length === 1 ? 'diagnóstico' : 'diagnósticos' }} ·
                {{ cantidadTratamientos }} {{ cantidadTratamientos === 1 ? 'tratamiento' : 'tratamientos' }}
                <span v-if="!cargando" class="metrica-activos" :class="{ hay: tratamientosActivos > 0 }">
                  · {{ tratamientosActivos }} {{ tratamientosActivos === 1 ? 'activo' : 'activos' }}
                </span>
              </p>
            </div>
            <nav
              v-if="!error && !cargando"
              class="pestanas-historial"
              role="tablist"
              aria-label="Vistas del historial clínico"
            >
              <button
                type="button"
                role="tab"
                id="tab-registros-recientes"
                aria-controls="panel-registros-recientes"
                :aria-selected="pestanaHistorial === 'recientes'"
                :class="{ activa: pestanaHistorial === 'recientes' }"
                @click="pestanaHistorial = 'recientes'"
              >
                Más recientes
              </button>
              <button
                type="button"
                role="tab"
                id="tab-historial-diagnosticos"
                aria-controls="panel-historial-diagnosticos"
                :aria-selected="pestanaHistorial === 'historial'"
                :class="{ activa: pestanaHistorial === 'historial' }"
                @click="pestanaHistorial = 'historial'"
              >
                Historial de diagnósticos
              </button>
            </nav>
            <div class="acciones-cabecera">
              <button class="btn btn-secondary" type="button" :disabled="!auth.permisos.generarPdfVeterinaria">
                Generar PDF
              </button>
              <!-- Solo Veterinaria registra; los demás roles lo ven deshabilitado -->
              <button
                class="btn btn-primary"
                type="button"
                :disabled="!auth.permisos.registrarVeterinaria"
                :title="auth.permisos.registrarVeterinaria ? undefined : 'Solo el rol de Veterinaria puede registrar diagnósticos y tratamientos'"
                @click="nuevoDiagnostico"
              >
                + Nuevo registro
              </button>
            </div>
          </div>
        </Teleport>

        <p v-if="error" class="alert-error mensaje-error">
          {{ error }}
          <button class="btn btn-secondary" @click="cargar()">Reintentar</button>
        </p>
        <p v-else-if="cargando" class="estado-vacio">Cargando historial clínico…</p>
        <template v-else>
          <section
            v-show="pestanaHistorial === 'recientes'"
            id="panel-registros-recientes"
            class="registros-recientes"
            role="tabpanel"
            aria-labelledby="tab-registros-recientes"
          >
            <article v-if="diagnosticoReciente" class="registro-reciente">
              <span class="tipo-label">Diagnóstico más reciente</span>
              <button
                type="button"
                class="resumen-diagnostico"
                :aria-label="`Ver diagnóstico ${diagnosticoReciente.diagnostico}`"
                @click="abrirDetalle(diagnosticoReciente)"
              >
                <span class="resumen-cabecera">
                  <strong>{{ diagnosticoReciente.diagnostico }}</strong>
                  <AppBadge v-if="diagnosticoReciente.es_critico" tone="amber">Crítico</AppBadge>
                  <time :datetime="diagnosticoReciente.fecha_registro">
                    {{ fechaHora(diagnosticoReciente.fecha_registro) }}
                  </time>
                </span>
                <span class="resumen-descripcion">
                  {{ diagnosticoReciente.observaciones || 'Sin descripción registrada.' }}
                </span>
              </button>
            </article>
            <p v-else class="estado-vacio">
              Aún no hay diagnósticos registrados. Registra uno para iniciar el historial clínico.
            </p>

            <article v-if="tratamientoReciente" class="registro-reciente">
              <span class="tipo-label">Tratamiento en curso más reciente</span>
              <div class="resumen-tratamiento">
                <div class="resumen-cabecera">
                  <strong>{{ tratamientoReciente.tratamiento.descripcion }}</strong>
                  <span class="tratamiento-meta">
                    <AppBadge :tone="tonoTratamiento(tratamientoReciente.tratamiento.estado)">
                      {{ etiquetaTratamiento(tratamientoReciente.tratamiento.estado) }}
                    </AppBadge>
                    <time :datetime="tratamientoReciente.tratamiento.fecha_inicio">
                      Desde {{ formatearFecha(tratamientoReciente.tratamiento.fecha_inicio) }}
                      <template v-if="tratamientoReciente.tratamiento.fecha_fin">
                        · hasta {{ formatearFecha(tratamientoReciente.tratamiento.fecha_fin) }}
                      </template>
                    </time>
                  </span>
                </div>
                <p
                  v-if="
                    tratamientoReciente.tratamiento.frecuencia_valor &&
                    tratamientoReciente.tratamiento.frecuencia_unidad
                  "
                >
                  Frecuencia: cada {{ tratamientoReciente.tratamiento.frecuencia_valor }}
                  {{ etiquetaUnidadFrecuencia(tratamientoReciente.tratamiento.frecuencia_unidad) }}
                  <template v-if="tratamientoReciente.tratamiento.hora_inicio">
                    · Inicio {{ tratamientoReciente.tratamiento.hora_inicio.slice(0, 5) }}
                  </template>
                </p>
                <p
                  v-else-if="tratamientoReciente.tratamiento.frecuencia"
                  class="dato-legado"
                >
                  Frecuencia anterior: {{ tratamientoReciente.tratamiento.frecuencia }}
                </p>
                <ul v-if="tratamientoReciente.tratamiento.medicamentos.length" class="medicamentos-resumen">
                  <li
                    v-for="medicamento in tratamientoReciente.tratamiento.medicamentos"
                    :key="medicamento.id_tratamiento_medicamento"
                  >
                    {{ medicamento.nombre_medicamento }} · Dosis
                    {{ formatoNumero(medicamento.dosis_ml, 2) }} ml
                  </li>
                </ul>
                <p
                  v-else-if="tratamientoReciente.tratamiento.dosis"
                  class="dato-legado"
                >
                  Dosis anterior: {{ tratamientoReciente.tratamiento.dosis }}
                </p>
                <button
                  type="button"
                  class="enlace-diagnostico"
                  @click="abrirDetalle(tratamientoReciente.diagnostico)"
                >
                  Diagnóstico asociado: {{ tratamientoReciente.diagnostico.diagnostico }}
                </button>
              </div>
            </article>
            <p v-else class="sin-tratamiento">No hay tratamientos en curso.</p>
          </section>

          <section
            v-show="pestanaHistorial === 'historial'"
            id="panel-historial-diagnosticos"
            class="historial-diagnosticos"
            role="tabpanel"
            aria-label="Historial de diagnósticos"
            aria-labelledby="tab-historial-diagnosticos"
          >
            <p v-if="diagnosticosOrdenados.length === 0" class="estado-vacio">
              Aún no hay diagnósticos registrados.
            </p>
            <!-- Tarjeta resumen (título y fecha) por diagnóstico; al hacer clic se abre el detalle -->
            <div v-else ref="listaHistorial" class="lista-medida">
              <ol class="lista-diagnosticos">
                <li v-for="diagnostico in diagnosticosPaginados" :key="diagnostico.id_diagnostico">
                  <button
                    type="button"
                    class="tarjeta-diagnostico"
                    :class="{ critico: diagnostico.es_critico }"
                    :aria-label="`Ver diagnóstico ${diagnostico.diagnostico}`"
                    @click="abrirDetalle(diagnostico)"
                  >
                    <span class="td-fila">
                      <strong class="td-titulo">{{ diagnostico.diagnostico }}</strong>
                      <AppBadge v-if="diagnostico.es_critico" tone="amber">Crítico</AppBadge>
                    </span>
                    <span class="td-fila td-pie">
                      <time :datetime="diagnostico.fecha_registro">{{ fechaHora(diagnostico.fecha_registro) }}</time>
                      <span class="td-metrica" :class="{ hay: activosDe(diagnostico) > 0 }">
                        {{ activosDe(diagnostico) }} {{ activosDe(diagnostico) === 1 ? 'tratamiento activo' : 'tratamientos activos' }}
                        · {{ tratamientosDe(diagnostico).length }} en total
                      </span>
                    </span>
                  </button>
                </li>
              </ol>
            </div>
            <nav
              class="paginacion"
              aria-label="Paginación del historial de diagnósticos"
            >
              <button
                class="btn btn-secondary"
                type="button"
                :disabled="paginaHistorial === 1"
                @click="paginaHistorial--"
              >
                Anterior
              </button>
              <span>Página {{ paginaHistorial }} de {{ paginasHistorial }}</span>
              <button
                class="btn btn-secondary"
                type="button"
                :disabled="paginaHistorial === paginasHistorial"
                @click="paginaHistorial++"
              >
                Siguiente
              </button>
            </nav>
          </section>
        </template>
      </section>
    </div>

    <template v-if="diagnosticoSeleccionado">
      <button
        type="button"
        class="detalle-fondo"
        aria-label="Cerrar detalle del diagnóstico"
        @click="cerrarDetalle"
      />
      <aside
        class="detalle-lateral"
        role="dialog"
        aria-modal="true"
        aria-labelledby="detalle-titulo"
        tabindex="-1"
        @keydown.esc="cerrarDetalle"
      >
        <header class="detalle-header">
          <div>
            <AppBadge :tone="diagnosticoSeleccionado.es_critico ? 'amber' : 'blue'">
              Diagnóstico{{ diagnosticoSeleccionado.es_critico ? ' · Crítico' : '' }}
            </AppBadge>
            <h2 id="detalle-titulo">{{ diagnosticoSeleccionado.diagnostico }}</h2>
            <time :datetime="diagnosticoSeleccionado.fecha_registro">
              {{ fechaHora(diagnosticoSeleccionado.fecha_registro) }}
            </time>
          </div>
          <button type="button" class="cerrar-detalle" aria-label="Cerrar" autofocus @click="cerrarDetalle">×</button>
        </header>
        <div class="detalle-contenido">
          <p class="descripcion-detalle">
            {{ diagnosticoSeleccionado.observaciones || 'Sin descripción registrada.' }}
          </p>
          <p class="registrado-por">Registrado por usuario #{{ diagnosticoSeleccionado.id_usuario }}</p>
          <section class="detalle-seccion">
            <h3>Signos vitales de este registro</h3>
            <dl v-if="valoresSignosVitales(diagnosticoSeleccionado.signos_vitales).length" class="detalle-signos">
              <div v-for="signo in valoresSignosVitales(diagnosticoSeleccionado.signos_vitales)" :key="signo.etiqueta">
                <dt>{{ signo.etiqueta }}</dt>
                <dd>{{ signo.valor }}</dd>
              </div>
            </dl>
            <p v-else class="detalle-vacio">No se registraron signos vitales.</p>
          </section>
          <section class="detalle-seccion">
            <h3>Tratamientos <span class="detalle-cuenta">Elige uno para ver su detalle</span></h3>
            <ul v-if="tratamientosSeleccionados.length" class="detalle-tratamientos">
              <li
                v-for="tratamiento in tratamientosSeleccionados"
                :key="tratamiento.id_tratamiento"
                :class="{ abierto: tratamientoAbierto === tratamiento.id_tratamiento }"
              >
                <button
                  type="button"
                  class="tratamiento-opcion"
                  :aria-expanded="tratamientoAbierto === tratamiento.id_tratamiento"
                  @click="alternarTratamiento(tratamiento.id_tratamiento)"
                >
                  <strong>{{ tratamiento.descripcion }}</strong>
                  <span class="tratamiento-fechas">
                    {{ formatearFecha(tratamiento.fecha_inicio) }}
                    <template v-if="tratamiento.fecha_fin"> — {{ formatearFecha(tratamiento.fecha_fin) }}</template>
                  </span>
                  <AppBadge :tone="tonoTratamiento(tratamiento.estado)">
                    {{ etiquetaTratamiento(tratamiento.estado) }}
                  </AppBadge>
                  <span class="flecha" aria-hidden="true">{{ tratamientoAbierto === tratamiento.id_tratamiento ? '▴' : '▾' }}</span>
                </button>
                <div v-if="tratamientoAbierto === tratamiento.id_tratamiento" class="tratamiento-detalle">
                <p v-if="tratamiento.frecuencia_valor && tratamiento.frecuencia_unidad">
                  Frecuencia: cada {{ tratamiento.frecuencia_valor }}
                  {{ etiquetaUnidadFrecuencia(tratamiento.frecuencia_unidad) }}
                  <template v-if="tratamiento.hora_inicio">
                    · Inicio {{ tratamiento.hora_inicio.slice(0, 5) }}
                  </template>
                </p>
                <p v-else-if="tratamiento.frecuencia" class="dato-legado">
                  Frecuencia anterior: {{ tratamiento.frecuencia }}
                </p>
                <ul v-if="tratamiento.medicamentos.length" class="medicamentos-resumen">
                  <li
                    v-for="medicamento in tratamiento.medicamentos"
                    :key="medicamento.id_tratamiento_medicamento"
                  >
                    {{ medicamento.nombre_medicamento }} · Dosis
                    {{ formatoNumero(medicamento.dosis_ml, 2) }} ml
                  </li>
                </ul>
                <p v-else-if="tratamiento.dosis" class="dato-legado">
                  Dosis anterior: {{ tratamiento.dosis }}
                </p>
                <button
                  v-if="auth.permisos.registrarVeterinaria"
                  type="button"
                  class="accion-link"
                  @click="editarTratamiento(tratamiento)"
                >
                  Editar tratamiento
                </button>
                </div>
              </li>
            </ul>
            <p v-else class="detalle-vacio">No hay tratamientos asociados.</p>
          </section>
        </div>
        <footer v-if="auth.permisos.registrarVeterinaria" class="detalle-footer">
          <button type="button" class="btn btn-secondary" @click="editarDiagnosticoSeleccionado">
            Editar
          </button>
        </footer>
      </aside>
    </template>
  </section>

  <VeterinariaRegistroModal
    :open="modalAbierto"
    :id-animal="idAnimal"
    :nombre-ejemplar="nombreEjemplar"
    :diagnosticos="diagnosticos"
    :fecha-ingreso="fechaIngreso"
    :registro="registroEditando"
    :tipo-inicial="tipoNuevo"
    @close="modalAbierto = false"
    @saved="cargar()"
  />
</template>

<style scoped>
.veterinaria {
  min-width: 0;
}

.veterinaria-grid {
  display: grid;
  grid-template-columns: minmax(260px, 0.8fr) minmax(0, 1.7fr);
  align-items: stretch;
  gap: 18px;
}

.columna-signos {
  min-width: 0;
}

.columna-historial {
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding-left: 18px;
  border-left: 1px dashed var(--color-border-strong);
}

.ultima-revision {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.columna-signos .signos-resumen {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

/* Vive en la barra de pestañas de la ficha: ocupa todo el alto para que el
   subrayado de la pestaña activa quede sobre la línea de la barra. */
/* Las sub-pestañas van a la derecha, junto a "Generar PDF" */
.pestanas-historial {
  display: flex;
  align-self: stretch;
  align-items: flex-end;
  gap: 18px;
  margin-left: auto;
  margin-bottom: -6px;
}

.pestanas-historial button {
  padding: 10px 4px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--color-text-muted);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.pestanas-historial button.activa {
  border-bottom-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.registros-recientes,
.historial-diagnosticos {
  display: grid;
  gap: 12px;
}

.historial-diagnosticos {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

/* Ocupa el alto que le deja la tarjeta de signos vitales (contain: size evita que las tarjetas
   estiren la columna); el panel mide ese alto y calcula cuántas tarjetas entran por página */
.lista-medida {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  contain: size;
}

.tarjeta-diagnostico {
  display: grid;
  align-content: center;
  gap: 6px;
  width: 100%;
  height: 74px;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-left: 3px solid #3f5a96;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
}

.tarjeta-diagnostico.critico {
  border-left-color: #b9791b;
}

.tarjeta-diagnostico:hover {
  background: var(--color-surface-alt);
}

.td-fila {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.td-titulo {
  overflow: hidden;
  font-size: 14.5px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.td-pie {
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-muted);
}

.td-metrica {
  white-space: nowrap;
}

.td-metrica.hay,
.metrica-activos.hay {
  color: #87661a;
  font-weight: 600;
}

.registro-reciente {
  display: grid;
  gap: 8px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.resumen-diagnostico {
  display: grid;
  width: 100%;
  gap: 8px;
  padding: 13px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
}

.resumen-diagnostico:hover,
.resumen-diagnostico:focus-visible {
  border-color: var(--color-primary);
  outline: none;
}

.resumen-cabecera {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.resumen-cabecera time {
  margin-left: auto;
  color: var(--color-text-subtle);
  font-size: 11px;
  font-weight: 400;
  text-align: right;
}

.tratamiento-meta {
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 6px 10px;
  margin-left: auto;
}

.tratamiento-meta time {
  color: var(--color-text-subtle);
  font-size: 11px;
  text-align: right;
}

.resumen-descripcion {
  display: -webkit-box;
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-line;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.resumen-diagnostico time,
.resumen-tratamiento time {
  color: var(--color-text-subtle);
  font-size: 11px;
}

.lista-diagnosticos {
  display: grid;
  flex: 1;
  align-content: start;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.resumen-tratamiento {
  display: grid;
  gap: 8px;
  padding-top: 3px;
}

.resumen-tratamiento > p {
  color: var(--color-text-muted);
  font-size: 12px;
}

.enlace-diagnostico {
  justify-self: start;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-primary);
  font: inherit;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
}

.detalle-fondo {
  position: fixed;
  z-index: 1199;
  inset: 0;
  border: 0;
  background: rgb(20 24 20 / 32%);
}

/* Modal centrado con todo el detalle del diagnóstico */
.detalle-lateral {
  position: fixed;
  z-index: 1200;
  top: 50%;
  left: 50%;
  display: flex;
  flex-direction: column;
  width: min(720px, calc(100vw - 32px));
  max-height: calc(100vh - 48px);
  max-height: calc(100dvh - 48px);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: 0 24px 60px rgba(35, 40, 31, 0.25);
  transform: translate(-50%, -50%);
}

.detalle-cuenta {
  margin-left: 6px;
  font-size: 11.5px;
  font-weight: 400;
  color: var(--color-text-muted);
}

.tratamiento-opcion {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto 14px;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 0;
  border: 0;
  background: none;
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
}

.tratamiento-opcion strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tratamiento-fechas {
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.flecha {
  color: var(--color-text-muted);
}

.tratamiento-detalle {
  display: grid;
  gap: 6px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--color-border);
}

.detalle-tratamientos li.abierto {
  border-color: var(--color-border-strong);
  background: var(--color-surface-alt);
}

.detalle-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
  border-bottom: 1px solid var(--color-border);
}

.detalle-header h2 {
  margin-top: 9px;
  font-family: var(--font-serif);
  font-size: 18px;
}

.detalle-header time {
  display: block;
  margin-top: 4px;
  color: var(--color-text-subtle);
  font-size: 11px;
}

.cerrar-detalle {
  align-self: flex-start;
  padding: 0 4px;
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 22px;
  cursor: pointer;
}

.detalle-contenido {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.descripcion-detalle {
  margin-bottom: 18px;
  color: var(--color-text);
  font-size: 13px;
  line-height: 1.55;
  white-space: pre-line;
}

.detalle-seccion + .detalle-seccion {
  margin-top: 20px;
}

.detalle-seccion h3 {
  padding-bottom: 7px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.detalle-signos {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding-top: 12px;
}

.detalle-signos div {
  display: grid;
  gap: 3px;
}

.detalle-signos dt {
  color: var(--color-text-subtle);
  font-size: 10px;
}

.detalle-signos dd {
  font-size: 12px;
  font-weight: 600;
}

.detalle-tratamientos {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.detalle-tratamientos li {
  display: grid;
  gap: 7px;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
}

.detalle-tratamientos p,
.detalle-vacio {
  color: var(--color-text-muted);
  font-size: 12px;
}

.detalle-footer {
  display: flex;
  justify-content: flex-end;
  padding: 12px 20px;
  border-top: 1px solid var(--color-border);
}

.ultima-revision-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 6px 12px;
  margin-bottom: 12px;
}

.ultima-revision-header h2 {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.ultima-revision-header time {
  text-transform: none;
}

.ultima-revision-header > span {
  color: var(--color-text-subtle);
  font-size: 12px;
}

.ultima-revision-header .condicion strong {
  color: var(--color-text);
  font-weight: 600;
}

.signos-resumen {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.signo-resumen {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  min-height: 84px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-input);
}

.signo-resumen span {
  color: var(--color-text-muted);
  font-size: 12px;
}

.signo-resumen strong {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

/* Valores categóricos fuera de lo normal */
.signo-resumen.anomalo {
  background: var(--color-danger-soft);
}

.signo-resumen.anomalo strong {
  color: var(--color-danger);
}

.tendencia {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-top: 2px;
  color: var(--color-primary);
}

.tendencia svg {
  flex-shrink: 0;
  overflow: visible;
}

.tendencia small {
  color: var(--color-text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.historial-cabecera {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  width: 100%;
  margin: 0;
}

.historial-cabecera h2 {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
}

.historial-cabecera p {
  margin-top: 3px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.acciones-cabecera {
  display: flex;
  gap: 8px;
}

.acciones-cabecera .btn {
  padding: 9px 13px;
  font-size: 12px;
  white-space: nowrap;
}

.tipo-label {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.accion-link {
  padding: 3px 6px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 600;
}

.accion-link:hover {
  background: var(--color-primary-soft);
}

.registrado-por {
  margin-top: 10px;
  color: var(--color-text-subtle);
  font-size: 10px;
}

.sin-tratamiento {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  color: var(--color-text-subtle);
  font-size: 11px;
}

.estado-vacio {
  display: grid;
  justify-items: center;
  gap: 9px;
  padding: 36px 20px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  text-align: center;
}

.estado-vacio h3 {
  color: var(--color-text);
  font-size: 15px;
}

.estado-vacio p {
  max-width: 380px;
  font-size: 12px;
}

.estado-vacio .btn {
  margin-top: 5px;
}

.mensaje-error {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.paginacion {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 14px;
  margin-top: 20px;
}

.historial-diagnosticos .paginacion {
  margin-top: auto;
  padding-top: 18px;
}

.paginacion span {
  color: var(--color-text-muted);
  font-size: 12px;
}

.medicamentos-resumen {
  display: grid;
  gap: 4px;
  margin: 0;
  padding-left: 18px;
  color: var(--color-text-muted);
  font-size: 12px;
}

@media (max-width: 900px) {
  /* Una sola columna: sin la tarjeta de signos al lado, la lista toma su alto natural */
  .lista-medida {
    flex: none;
    overflow: visible;
    contain: none;
  }

  .veterinaria-grid {
    grid-template-columns: 1fr;
  }

  .columna-historial {
    padding-top: 18px;
    padding-left: 0;
    border-top: 1px dashed var(--color-border-strong);
    border-left: 0;
  }

  .signos-resumen {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .historial-cabecera {
    align-items: flex-start;
    flex-direction: column;
  }

  .pestanas-historial {
    margin-bottom: 0;
  }

}

@media (max-width: 420px) {
  .columna-signos .signos-resumen {
    grid-template-columns: 1fr;
  }
}
</style>
