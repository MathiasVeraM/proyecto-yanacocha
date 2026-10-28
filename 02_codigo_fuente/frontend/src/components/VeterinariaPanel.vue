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

const cantidadTratamientos = computed(
  () => Object.values(tratamientos.value).reduce((total, items) => total + items.length, 0),
)
const cantidadCriticos = computed(() => diagnosticos.value.filter((d) => d.es_critico).length)
const tratamientosEnCurso = computed(
  () => Object.values(tratamientos.value).flat().filter((t) => t.estado === 'en_curso').length,
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

watch(() => props.idAnimal, cargar, { immediate: true })
</script>

<template>
  <section class="veterinaria">
    <div class="resumen-grid" aria-label="Resumen veterinario">
      <article class="resumen-card">
        <span class="resumen-icono">+</span>
        <div>
          <strong>{{ diagnosticos.length + cantidadTratamientos }}</strong>
          <span>Registros clínicos</span>
        </div>
      </article>
      <article class="resumen-card">
        <span class="resumen-icono critico">!</span>
        <div>
          <strong>{{ cantidadCriticos }}</strong>
          <span>Diagnósticos críticos</span>
        </div>
      </article>
      <article class="resumen-card">
        <span class="resumen-icono tratamiento">↻</span>
        <div>
          <strong>{{ tratamientosEnCurso }}</strong>
          <span>Tratamientos en curso</span>
        </div>
      </article>
    </div>

    <div class="historial-cabecera">
      <div>
        <h2>Historial clínico</h2>
        <p>{{ diagnosticos.length }} {{ diagnosticos.length === 1 ? 'diagnóstico' : 'diagnósticos' }} ·
          {{ cantidadTratamientos }} {{ cantidadTratamientos === 1 ? 'tratamiento' : 'tratamientos' }} registrados
        </p>
      </div>
      <div class="acciones-cabecera">
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
      <li v-for="diagnostico in diagnosticos" :key="diagnostico.id_diagnostico" class="evento">
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

.resumen-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 22px;
}

.resumen-card {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 76px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.resumen-icono {
  display: grid;
  flex: 0 0 34px;
  place-items: center;
  height: 34px;
  border-radius: 10px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 19px;
  font-weight: 600;
}

.resumen-icono.critico {
  background: #f5e9c4;
  color: #87661a;
}

.resumen-icono.tratamiento {
  background: #e3e6f3;
  color: #4a538f;
}

.resumen-card strong,
.resumen-card span:not(.resumen-icono) {
  display: block;
}

.resumen-card strong {
  font-family: var(--font-serif);
  font-size: 21px;
}

.resumen-card div span {
  margin-top: 2px;
  color: var(--color-text-muted);
  font-size: 11px;
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

@media (max-width: 720px) {
  .resumen-grid {
    grid-template-columns: 1fr;
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
</style>
