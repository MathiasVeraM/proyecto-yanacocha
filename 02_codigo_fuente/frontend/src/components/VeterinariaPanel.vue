<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AppBadge from '@/components/AppBadge.vue'
import VeterinariaRegistroModal from '@/components/VeterinariaRegistroModal.vue'
import { ApiError } from '@/api/http'
import { veterinariaApi } from '@/api/veterinaria'
import { formatearFecha } from '@/config/animales'
import type { Diagnostico, Tratamiento } from '@/types/veterinaria'

const props = defineProps<{ idAnimal: number }>()

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
const registrosPorPagina = 5

const cantidadTratamientos = computed(
  () => Object.values(tratamientos.value).reduce((total, items) => total + items.length, 0),
)
const ultimaRevision = computed(
  () =>
    [...diagnosticos.value].sort(
      (a, b) => new Date(b.fecha_registro).getTime() - new Date(a.fecha_registro).getTime(),
    )[0] ?? null,
)
const signosUltimaRevision = computed(() => ultimaRevision.value?.signos_vitales ?? null)
const diagnosticosOrdenados = computed(() =>
  [...diagnosticos.value].sort(
    (a, b) => new Date(b.fecha_registro).getTime() - new Date(a.fecha_registro).getTime(),
  ),
)
const paginasHistorial = computed(() => Math.max(1, Math.ceil(diagnosticosOrdenados.value.length / registrosPorPagina)))
const diagnosticosPaginados = computed(() => {
  const inicio = (paginaHistorial.value - 1) * registrosPorPagina
  return diagnosticosOrdenados.value.slice(inicio, inicio + registrosPorPagina)
})

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

async function cargar() {
  const idAnimal = props.idAnimal
  cargando.value = true
  error.value = ''
  try {
    const registros = await veterinariaApi.listarDiagnosticos(idAnimal)
    const pares = await Promise.all(
      registros.map(async (diagnostico) => [
        diagnostico.id_diagnostico,
        await veterinariaApi.listarTratamientos(diagnostico.id_diagnostico),
      ] as const),
    )
    if (idAnimal !== props.idAnimal) return
    diagnosticos.value = registros
    tratamientos.value = Object.fromEntries(pares)
  } catch (e) {
    if (idAnimal === props.idAnimal) {
      error.value = e instanceof ApiError ? e.message : 'No se pudo cargar el historial veterinario'
    }
  } finally {
    if (idAnimal === props.idAnimal) cargando.value = false
  }
}

function nuevoDiagnostico() {
  registroEditando.value = null
  tipoNuevo.value = 'diagnostico'
  modalAbierto.value = true
}

function nuevoTratamiento() {
  registroEditando.value = null
  tipoNuevo.value = 'tratamiento'
  modalAbierto.value = true
}

function editarDiagnostico(datos: Diagnostico) {
  registroEditando.value = { tipo: 'diagnostico', datos }
  modalAbierto.value = true
}

function editarTratamiento(datos: Tratamiento) {
  registroEditando.value = { tipo: 'tratamiento', datos }
  modalAbierto.value = true
}

watch(
  () => props.idAnimal,
  () => {
    paginaHistorial.value = 1
    void cargar()
  },
  { immediate: true },
)

watch(paginasHistorial, (total) => {
  if (paginaHistorial.value > total) paginaHistorial.value = total
})
</script>

<template>
  <section class="veterinaria">
    <section class="ultima-revision" aria-label="Signos vitales de la última revisión">
      <header class="ultima-revision-header">
        <h2>Signos vitales · última revisión</h2>
        <time v-if="ultimaRevision" :datetime="ultimaRevision.fecha_registro">
          {{ fechaHora(ultimaRevision.fecha_registro) }}
        </time>
        <span v-else>Sin revisiones registradas</span>
      </header>
      <div class="signos-resumen">
        <article class="signo-resumen">
          <span>Temperatura</span>
          <strong>
            {{ signosUltimaRevision?.temperatura_c !== null && signosUltimaRevision?.temperatura_c !== undefined
              ? `${formatoNumero(signosUltimaRevision.temperatura_c)} °C`
              : '—' }}
          </strong>
        </article>
        <article class="signo-resumen">
          <span>Hidratación</span>
          <strong>{{ signosUltimaRevision?.hidratacion ? etiquetaCategoria(signosUltimaRevision.hidratacion) : '—' }}</strong>
        </article>
        <article class="signo-resumen">
          <span>Condición corporal</span>
          <strong>
            {{ signosUltimaRevision?.condicion_corporal
              ? condicionCorporal(signosUltimaRevision.condicion_corporal)
              : '—' }}
          </strong>
        </article>
        <article class="signo-resumen">
          <span>Frec. cardíaca</span>
          <strong>
            {{ signosUltimaRevision?.frecuencia_cardiaca_lpm != null
              ? `${signosUltimaRevision.frecuencia_cardiaca_lpm} lpm`
              : '—' }}
          </strong>
        </article>
        <article class="signo-resumen">
          <span>Frec. respiratoria</span>
          <strong>
            {{ signosUltimaRevision?.frecuencia_respiratoria_rpm != null
              ? `${signosUltimaRevision.frecuencia_respiratoria_rpm} rpm`
              : '—' }}
          </strong>
        </article>
        <article class="signo-resumen">
          <span>Peso actual</span>
          <strong>
            {{ signosUltimaRevision?.peso_kg != null
              ? `${formatoNumero(signosUltimaRevision.peso_kg, 3)} kg`
              : '—' }}
          </strong>
        </article>
        <article class="signo-resumen">
          <span>Llenado capilar</span>
          <strong>
            {{ signosUltimaRevision?.tiempo_llenado_capilar_s != null
              ? `${formatoNumero(signosUltimaRevision.tiempo_llenado_capilar_s)} s`
              : '—' }}
          </strong>
        </article>
        <article class="signo-resumen">
          <span>Mucosas</span>
          <strong>{{ signosUltimaRevision?.mucosas ? etiquetaCategoria(signosUltimaRevision.mucosas) : '—' }}</strong>
        </article>
        <article class="signo-resumen">
          <span>Actitud</span>
          <strong>{{ signosUltimaRevision?.actitud ? etiquetaCategoria(signosUltimaRevision.actitud) : '—' }}</strong>
        </article>
      </div>
    </section>

    <div class="historial-cabecera">
      <div>
        <h2>Historial clínico</h2>
        <p>{{ diagnosticos.length }} {{ diagnosticos.length === 1 ? 'diagnóstico' : 'diagnósticos' }} ·
          {{ cantidadTratamientos }} {{ cantidadTratamientos === 1 ? 'tratamiento' : 'tratamientos' }} registrados
        </p>
      </div>
      <div class="acciones-cabecera">
        <button class="btn btn-secondary" type="button">Generar PDF</button>
        <button class="btn btn-secondary" :disabled="diagnosticos.length === 0" @click="nuevoTratamiento">
          + Tratamiento
        </button>
        <button class="btn btn-primary" @click="nuevoDiagnostico">+ Nuevo registro</button>
      </div>
    </div>

    <p v-if="error" class="alert-error mensaje-error">
      {{ error }}
      <button class="btn btn-secondary" @click="cargar">Reintentar</button>
    </p>
    <p v-else-if="cargando" class="estado-vacio">Cargando historial clínico…</p>
    <div v-else-if="diagnosticos.length === 0" class="estado-vacio">
      <span class="vacio-icono">✚</span>
      <h3>Aún no hay registros veterinarios</h3>
      <p>Registra un diagnóstico para iniciar el historial clínico de este ejemplar.</p>
      <button class="btn btn-primary" @click="nuevoDiagnostico">Registrar diagnóstico</button>
    </div>

    <ol v-else class="linea-tiempo">
      <li v-for="diagnostico in diagnosticosPaginados" :key="diagnostico.id_diagnostico" class="evento">
        <span class="evento-punto" :class="{ critico: diagnostico.es_critico }" />
        <article class="evento-card">
          <header class="evento-header">
            <div class="evento-tipo">
              <span class="tipo-label">Diagnóstico</span>
              <AppBadge v-if="diagnostico.es_critico" tone="amber">Crítico</AppBadge>
            </div>
            <div class="evento-acciones">
              <time :datetime="diagnostico.fecha_registro">{{ fechaHora(diagnostico.fecha_registro) }}</time>
              <button
                class="accion-link"
                :aria-label="`Editar diagnóstico ${diagnostico.diagnostico}`"
                @click="editarDiagnostico(diagnostico)"
              >
                Editar
              </button>
            </div>
          </header>
          <h3>{{ diagnostico.diagnostico }}</h3>
          <p v-if="diagnostico.observaciones" class="descripcion">{{ diagnostico.observaciones }}</p>
          <dl v-if="diagnostico.signos_vitales" class="signos-vitales">
            <div v-if="diagnostico.signos_vitales.peso_kg !== null">
              <dt>Peso</dt><dd>{{ formatoNumero(diagnostico.signos_vitales.peso_kg, 3) }} kg</dd>
            </div>
            <div v-if="diagnostico.signos_vitales.temperatura_c !== null">
              <dt>Temperatura</dt><dd>{{ formatoNumero(diagnostico.signos_vitales.temperatura_c) }} °C</dd>
            </div>
            <div v-if="diagnostico.signos_vitales.frecuencia_cardiaca_lpm !== null">
              <dt>Frec. cardíaca</dt><dd>{{ diagnostico.signos_vitales.frecuencia_cardiaca_lpm }} lpm</dd>
            </div>
            <div v-if="diagnostico.signos_vitales.frecuencia_respiratoria_rpm !== null">
              <dt>Frec. respiratoria</dt><dd>{{ diagnostico.signos_vitales.frecuencia_respiratoria_rpm }} rpm</dd>
            </div>
            <div v-if="diagnostico.signos_vitales.tiempo_llenado_capilar_s !== null">
              <dt>Llenado capilar</dt><dd>{{ formatoNumero(diagnostico.signos_vitales.tiempo_llenado_capilar_s) }} s</dd>
            </div>
            <div v-if="diagnostico.signos_vitales.hidratacion">
              <dt>Hidratación</dt><dd>{{ etiquetaCategoria(diagnostico.signos_vitales.hidratacion) }}</dd>
            </div>
            <div v-if="diagnostico.signos_vitales.condicion_corporal !== null">
              <dt>Condición corporal</dt><dd>{{ condicionCorporal(diagnostico.signos_vitales.condicion_corporal) }}</dd>
            </div>
            <div v-if="diagnostico.signos_vitales.mucosas">
              <dt>Mucosas</dt><dd>{{ etiquetaCategoria(diagnostico.signos_vitales.mucosas) }}</dd>
            </div>
            <div v-if="diagnostico.signos_vitales.actitud">
              <dt>Actitud</dt><dd>{{ etiquetaCategoria(diagnostico.signos_vitales.actitud) }}</dd>
            </div>
          </dl>
          <p class="registrado-por">Registrado por usuario #{{ diagnostico.id_usuario }}</p>

          <div
            v-for="tratamiento in tratamientos[diagnostico.id_diagnostico] ?? []"
            :key="tratamiento.id_tratamiento"
            class="tratamiento"
          >
            <div class="tratamiento-icono">↳</div>
            <div class="tratamiento-contenido">
              <div class="tratamiento-titulo">
                <strong>{{ tratamiento.medicamento_o_proceso }}</strong>
                <AppBadge :tone="tonoTratamiento(tratamiento.estado)">
                  {{ etiquetaTratamiento(tratamiento.estado) }}
                </AppBadge>
              </div>
              <p>
                <span v-if="tratamiento.dosis">{{ tratamiento.dosis }}</span>
                <span v-if="tratamiento.frecuencia"> · {{ tratamiento.frecuencia }}</span>
                <span> · Desde {{ formatearFecha(tratamiento.fecha_inicio) }}</span>
                <span v-if="tratamiento.fecha_fin"> hasta {{ formatearFecha(tratamiento.fecha_fin) }}</span>
              </p>
            </div>
            <button
              class="accion-link"
              :aria-label="`Editar tratamiento ${tratamiento.medicamento_o_proceso}`"
              @click="editarTratamiento(tratamiento)"
            >
              Editar
            </button>
          </div>
          <p
            v-if="!(tratamientos[diagnostico.id_diagnostico]?.length)"
            class="sin-tratamiento"
          >
            Sin tratamientos asociados
            <button class="accion-link" @click="nuevoTratamiento">Añadir tratamiento</button>
          </p>
        </article>
      </li>
    </ol>
    <nav
      v-if="!cargando && !error && diagnosticosOrdenados.length > registrosPorPagina"
      class="paginacion"
      aria-label="Paginación del historial clínico"
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

  <VeterinariaRegistroModal
    :open="modalAbierto"
    :id-animal="idAnimal"
    :diagnosticos="diagnosticos"
    :registro="registroEditando"
    :tipo-inicial="tipoNuevo"
    @close="modalAbierto = false"
    @saved="cargar"
  />
</template>

<style scoped>
.veterinaria {
  min-width: 0;
}

.ultima-revision {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.ultima-revision-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.ultima-revision-header h2 {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.ultima-revision-header time,
.ultima-revision-header > span {
  color: var(--color-text-subtle);
  font-size: 10px;
}

.signos-resumen {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.signo-resumen {
  display: grid;
  align-content: start;
  gap: 4px;
  min-height: 68px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-input);
}

.signo-resumen span {
  color: var(--color-text-muted);
  font-size: 10px;
}

.signo-resumen strong {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 14px;
  font-weight: 600;
}

.historial-cabecera {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin: 0 0 16px;
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

.linea-tiempo {
  position: relative;
  display: grid;
  gap: 14px;
  margin: 0;
  padding: 0 0 0 20px;
  list-style: none;
}

.linea-tiempo::before {
  position: absolute;
  top: 14px;
  bottom: 20px;
  left: 5px;
  width: 1px;
  background: var(--color-border-strong);
  content: '';
}

.evento {
  position: relative;
}

.evento-punto {
  position: absolute;
  top: 17px;
  left: -20px;
  width: 11px;
  height: 11px;
  border: 2px solid var(--color-surface);
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}

.evento-punto.critico {
  background: #b8861b;
  box-shadow: 0 0 0 1px #b8861b;
}

.evento-card {
  padding: 16px 18px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.evento-header,
.evento-tipo,
.evento-acciones,
.tratamiento-titulo {
  display: flex;
  align-items: center;
  gap: 9px;
}

.evento-header {
  justify-content: space-between;
  gap: 12px;
}

.tipo-label {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.evento-acciones {
  color: var(--color-text-subtle);
  font-size: 11px;
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

.evento-card h3 {
  margin-top: 10px;
  font-size: 15px;
  font-weight: 600;
}

.descripcion {
  margin-top: 6px;
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.55;
  white-space: pre-line;
}

.signos-vitales {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 8px;
  margin-top: 12px;
  padding: 11px;
  border-radius: var(--radius-sm);
  background: var(--color-input);
}

.signos-vitales div {
  display: grid;
  gap: 3px;
}

.signos-vitales dt {
  color: var(--color-text-muted);
  font-size: 10px;
}

.signos-vitales dd {
  font-size: 12px;
  font-weight: 600;
}

.registrado-por {
  margin-top: 10px;
  color: var(--color-text-subtle);
  font-size: 10px;
}

.tratamiento {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 13px;
  padding: 11px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-alt);
}

.tratamiento-icono {
  color: var(--color-primary);
  font-size: 18px;
}

.tratamiento-contenido {
  flex: 1;
  min-width: 0;
}

.tratamiento-titulo {
  flex-wrap: wrap;
}

.tratamiento-titulo strong {
  font-size: 12px;
}

.tratamiento-contenido p {
  margin-top: 4px;
  color: var(--color-text-muted);
  font-size: 11px;
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

.vacio-icono {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 20px;
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

.paginacion span {
  color: var(--color-text-muted);
  font-size: 12px;
}

@media (max-width: 720px) {
  .signos-resumen {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .historial-cabecera {
    align-items: flex-start;
    flex-direction: column;
  }

  .acciones-cabecera {
    width: 100%;
  }

  .acciones-cabecera .btn {
    flex: 1;
  }

  .evento-header {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 420px) {
  .signos-resumen {
    grid-template-columns: 1fr;
  }
}
</style>
