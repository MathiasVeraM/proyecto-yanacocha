<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Actividad, TipoActividad, UsuarioResponsable } from '@/types/actividades'
import type { Animal, Recinto } from '@/types/animales'

const props = defineProps<{
  actividades: Actividad[]
  animales: Animal[]
  recintos: Recinto[]
  usuarios: UsuarioResponsable[]
  cargando: boolean
  error: string
  actualizandoId: number | null
}>()
const emit = defineEmits<{ completar: [id: number, observaciones?: string] }>()

const tipoFiltro = ref('')
const animalFiltro = ref(0)
const estadoFiltro = ref<'pendientes' | 'completadas'>('pendientes')
const observacionAbierta = ref<number | null>(null)
const observacion = ref('')

const tipos: { valor: TipoActividad; etiqueta: string }[] = [
  { valor: 'alimentacion', etiqueta: 'Alimentación' },
  { valor: 'limpieza', etiqueta: 'Limpieza' },
  { valor: 'enriquecimiento', etiqueta: 'Enriquecimiento' },
  { valor: 'entrenamiento', etiqueta: 'Entrenamiento' },
]

const pendientes = computed(() => props.actividades.filter((actividad) => !actividad.completada).length)
const filtradas = computed(() =>
  props.actividades
    .filter((actividad) => !tipoFiltro.value || actividad.tipo_actividad === tipoFiltro.value)
    .filter((actividad) => !animalFiltro.value || actividad.id_animal === animalFiltro.value)
    .filter((actividad) =>
      estadoFiltro.value === 'pendientes' ? !actividad.completada : actividad.completada,
    )
    .sort((a, b) => (a.hora_programada ?? '').localeCompare(b.hora_programada ?? '')),
)

function nombreObjetivo(actividad: Actividad) {
  if (actividad.tipo_actividad === 'limpieza') {
    return props.recintos.find((recinto) => recinto.id_recinto === actividad.id_recinto)?.nombre_recinto
      ?? `Recinto #${actividad.id_recinto}`
  }
  const animal = props.animales.find((item) => item.id_animal === actividad.id_animal)
  return animal?.nombre ?? animal?.taxonomia.nombre_comun ?? `Ejemplar #${actividad.id_animal}`
}

function nombreResponsable(actividad: Actividad) {
  const id = actividad.id_usuario_responsable ?? actividad.id_usuario_programo
  const usuario = props.usuarios.find((item) => item.id_usuario === id)
  return usuario ? `${usuario.nombre} ${usuario.apellido}` : ''
}

function completar(actividad: Actividad, texto?: string) {
  emit('completar', actividad.id_actividad, texto?.trim() || undefined)
  observacionAbierta.value = null
  observacion.value = ''
}

function abrirObservacion(id: number) {
  observacionAbierta.value = observacionAbierta.value === id ? null : id
  observacion.value = ''
}
</script>

<template>
  <section class="checklist">
    <div class="list-heading">
      <div>
        <h1>Tareas de hoy · {{ new Intl.DateTimeFormat('es-EC', { weekday: 'long', day: 'numeric' }).format(new Date()) }}</h1>
      </div>
      <span class="pending-count">{{ pendientes }} pendientes</span>
    </div>

    <div class="filters" aria-label="Filtros de tareas">
      <label class="sr-only" for="filtro-tipo-checklist">Tipo de actividad</label>
      <select id="filtro-tipo-checklist" v-model="tipoFiltro" class="input filter">
        <option value="">Todos los tipos</option>
        <option v-for="tipo in tipos" :key="tipo.valor" :value="tipo.valor">{{ tipo.etiqueta }}</option>
      </select>

      <label class="sr-only" for="filtro-animal-checklist">Ejemplar</label>
      <select id="filtro-animal-checklist" v-model.number="animalFiltro" class="input filter">
        <option :value="0">Todos los ejemplares</option>
        <option v-for="animal in animales" :key="animal.id_animal" :value="animal.id_animal">
          {{ animal.nombre ?? animal.taxonomia.nombre_comun }}
        </option>
      </select>

      <label class="sr-only" for="filtro-estado-checklist">Estado</label>
      <select id="filtro-estado-checklist" v-model="estadoFiltro" class="input filter">
        <option value="pendientes">Pendientes</option>
        <option value="completadas">Completadas</option>
      </select>
    </div>

    <p v-if="error" class="alert-error" role="alert">{{ error }}</p>
    <p v-if="cargando && !actividades.length" class="state-card" role="status">Cargando tareas…</p>
    <p v-else-if="!cargando && !filtradas.length" class="state-card">
      {{ actividades.length ? 'No hay tareas para estos filtros.' : 'No hay actividades programadas para hoy.' }}
    </p>

    <div v-else class="task-list" :class="{ loading: cargando }">
      <article
        v-for="actividad in filtradas"
        :key="actividad.id_actividad"
        class="task-row"
        :class="{ done: actividad.completada }"
      >
        <input
          class="task-check"
          type="checkbox"
          :checked="actividad.completada"
          :disabled="actividad.completada || actualizandoId === actividad.id_actividad"
          :aria-label="`Completar ${nombreObjetivo(actividad)}`"
          @change="completar(actividad)"
        />
        <time class="task-time">{{ actividad.hora_programada?.slice(0, 5) ?? 'Todo el día' }}</time>
        <div class="task-subject">
          <strong>{{ nombreObjetivo(actividad) }}</strong>
          <small v-if="nombreResponsable(actividad)">Responsable: {{ nombreResponsable(actividad) }}</small>
        </div>
        <span class="type-badge" :class="actividad.tipo_actividad">{{ tipos.find((t) => t.valor === actividad.tipo_actividad)?.etiqueta }}</span>
        <div class="observation-control">
          <button
            class="observation-button"
            type="button"
            :disabled="actividad.completada || actualizandoId === actividad.id_actividad"
            @click="abrirObservacion(actividad.id_actividad)"
          >
            + Observación
          </button>
          <form
            v-if="observacionAbierta === actividad.id_actividad"
            class="observation-popover"
            @submit.prevent="completar(actividad, observacion)"
          >
            <label :for="`observacion-${actividad.id_actividad}`">Observación para completar</label>
            <textarea :id="`observacion-${actividad.id_actividad}`" v-model="observacion" rows="3" />
            <div>
              <button type="button" class="text-button" @click="observacionAbierta = null">Cancelar</button>
              <button type="submit" class="btn btn-primary">Completar</button>
            </div>
          </form>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.list-heading {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
  margin-bottom: 16px;
}

h1 {
  font-size: 16px;
  font-weight: 700;
  text-transform: capitalize;
}

.pending-count {
  padding: 6px 10px;
  border-radius: 20px;
  background: #f7edd1;
  color: #825d12;
  font-size: 12px;
  white-space: nowrap;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-bottom: 14px;
}

.filter {
  width: auto;
  min-width: 150px;
  padding: 8px 11px;
  background: var(--color-surface);
  font-size: 12px;
}

.task-list {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  transition: opacity 0.15s;
}

.task-list.loading {
  opacity: 0.65;
}

.task-row {
  position: relative;
  display: grid;
  grid-template-columns: 22px 56px minmax(100px, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  min-height: 58px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
}

.task-row:last-child {
  border-bottom: 0;
}

.task-row.done {
  opacity: 0.64;
}

.task-check {
  width: 18px;
  height: 18px;
  accent-color: var(--color-primary);
}

.task-time {
  color: var(--color-text-muted);
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.task-subject {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.task-subject strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
}

.task-subject small {
  color: var(--color-text-muted);
  font-size: 11px;
}

.type-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 10px;
  white-space: nowrap;
}

.type-badge.alimentacion { background: #f7edd1; color: #805c16; }
.type-badge.limpieza { background: #e0eee0; color: #32633b; }
.type-badge.enriquecimiento { background: #e2edf0; color: #346575; }
.type-badge.entrenamiento { background: #ece5f2; color: #655079; }

.observation-control {
  position: relative;
}

.observation-button,
.text-button {
  padding: 6px 9px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 11px;
}

.observation-popover {
  position: absolute;
  z-index: 3;
  top: calc(100% + 6px);
  right: 0;
  display: grid;
  gap: 7px;
  width: min(300px, 80vw);
  padding: 12px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.observation-popover label {
  color: var(--color-text-muted);
  font-size: 12px;
}

.observation-popover textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-input);
  resize: vertical;
}

.observation-popover > div {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.observation-popover .btn {
  padding: 6px 9px;
  font-size: 11px;
}

.state-card {
  padding: 34px 18px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: var(--color-text-muted);
  text-align: center;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

@media (max-width: 680px) {
  .task-row {
    grid-template-columns: 22px 50px minmax(0, 1fr) auto;
    gap: 8px;
  }

  .type-badge {
    grid-column: 3;
    justify-self: start;
  }

  .observation-control {
    grid-column: 4;
    grid-row: 1 / span 2;
  }
}

@media (max-width: 450px) {
  .list-heading {
    align-items: start;
    flex-direction: column;
  }

  .filter {
    flex: 1;
    min-width: 125px;
  }

  .task-row {
    grid-template-columns: 20px 46px minmax(0, 1fr);
  }

  .type-badge {
    grid-column: 3;
  }

  .observation-control {
    grid-column: 3;
    grid-row: 3;
    justify-self: start;
  }
}
</style>
