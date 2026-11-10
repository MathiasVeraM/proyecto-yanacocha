<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Actividad, TipoActividad } from '@/types/actividades'
import type { Animal, Recinto } from '@/types/animales'

export interface DiaCalendario {
  fecha: string
  etiqueta: string
  numero: number
  corto: string
  esHoy: boolean
}

const props = defineProps<{
  dias: DiaCalendario[]
  actividades: Actividad[]
  animales: Animal[]
  recintos: Recinto[]
  dietas: Record<number, { id_dieta: number; alimentos: { nombre_alimento: string }[] }>
  cargando: boolean
  error: string
}>()
const emit = defineEmits<{ cambiarSemana: [delta: number]; hoy: []; crear: [] }>()

const filtroAnimal = ref(0)
const filtroDia = ref('')
const filtroTipo = ref('')
const filtroEstado = ref('')
const tiposActividad: TipoActividad[] = ['alimentacion', 'enriquecimiento', 'entrenamiento', 'limpieza']

const tituloSemana = computed(() => {
  const primero = props.dias[0]
  const ultimo = props.dias[6]
  if (!primero || !ultimo) return ''
  const inicio = new Date(`${primero.fecha}T12:00:00`)
  const fin = new Date(`${ultimo.fecha}T12:00:00`)
  const mesInicio = new Intl.DateTimeFormat('es-EC', { month: 'long' }).format(inicio)
  const mesFin = new Intl.DateTimeFormat('es-EC', { month: 'long' }).format(fin)
  if (mesInicio === mesFin) {
    return `Semana del ${primero.numero} al ${ultimo.numero} de ${mesFin}`
  }
  return `Semana del ${primero.numero} de ${mesInicio} al ${ultimo.numero} de ${mesFin}`
})

const actividadesFiltradas = computed(() =>
  props.actividades.filter((actividad) => {
    if (filtroAnimal.value && actividad.id_animal !== filtroAnimal.value) return false
    if (filtroDia.value && actividad.fecha_programada !== filtroDia.value) return false
    if (filtroTipo.value && actividad.tipo_actividad !== filtroTipo.value) return false
    if (filtroEstado.value === 'pendiente' && actividad.completada) return false
    if (filtroEstado.value === 'completada' && !actividad.completada) return false
    return true
  }),
)

function actividadesDelDia(fecha: string, todoElDia: boolean) {
  return actividadesFiltradas.value
    .filter((actividad) => actividad.fecha_programada === fecha)
    .filter((actividad) => (actividad.hora_programada === null) === todoElDia)
    .sort((a, b) => (a.hora_programada ?? '').localeCompare(b.hora_programada ?? ''))
}

function tipoLabel(tipo: TipoActividad) {
  return {
    alimentacion: 'Alimentación',
    limpieza: 'Limpieza',
    enriquecimiento: 'Enriquecimiento',
    entrenamiento: 'Entrenamiento',
  }[tipo]
}

function nombreObjetivo(actividad: Actividad) {
  if (actividad.tipo_actividad === 'limpieza') {
    return props.recintos.find((recinto) => recinto.id_recinto === actividad.id_recinto)?.nombre_recinto
      ?? `Recinto #${actividad.id_recinto}`
  }
  const animal = props.animales.find((item) => item.id_animal === actividad.id_animal)
  return animal?.nombre ?? animal?.taxonomia.nombre_comun ?? `Ejemplar #${actividad.id_animal}`
}

function detalle(actividad: Actividad) {
  if (actividad.tipo_actividad === 'alimentacion' && actividad.id_dieta) {
    return props.dietas[actividad.id_dieta]?.alimentos.map((alimento) => alimento.nombre_alimento).join(' + ')
      ?? 'Plan de alimentación'
  }
  if (actividad.tipo_actividad === 'enriquecimiento') {
    return actividad.descripcion_estimulo ?? 'Estímulo programado'
  }
  if (actividad.tipo_actividad === 'entrenamiento') {
    return actividad.objetivo_entrenamiento ?? 'Entrenamiento'
  }
  return 'Limpieza de recinto'
}
</script>

<template>
  <section class="calendar">
    <div class="calendar-heading">
      <div class="week-controls">
        <button class="nav-button" type="button" aria-label="Semana anterior" @click="emit('cambiarSemana', -1)">‹</button>
        <h1>{{ tituloSemana }}</h1>
        <button class="nav-button" type="button" aria-label="Semana siguiente" @click="emit('cambiarSemana', 1)">›</button>
        <button class="today-button" type="button" @click="emit('hoy')">Hoy</button>
      </div>
      <button class="btn btn-primary" type="button" @click="emit('crear')">+ Crear actividad</button>
    </div>

    <div class="filters">
      <label class="sr-only" for="cal-filtro-animal">Ejemplar</label>
      <select id="cal-filtro-animal" v-model.number="filtroAnimal" class="input filter">
        <option :value="0">Todos los ejemplares</option>
        <option v-for="animal in animales" :key="animal.id_animal" :value="animal.id_animal">
          {{ animal.nombre ?? animal.taxonomia.nombre_comun }}
        </option>
      </select>
      <label class="sr-only" for="cal-filtro-dia">Día</label>
      <select id="cal-filtro-dia" v-model="filtroDia" class="input filter">
        <option value="">Todos los días</option>
        <option v-for="dia in dias" :key="dia.fecha" :value="dia.fecha">{{ dia.etiqueta }}</option>
      </select>
      <label class="sr-only" for="cal-filtro-tipo">Tipo</label>
      <select id="cal-filtro-tipo" v-model="filtroTipo" class="input filter">
        <option value="">Todos los tipos</option>
        <option v-for="tipo in tiposActividad" :key="tipo" :value="tipo">
          {{ tipoLabel(tipo) }}
        </option>
      </select>
      <label class="sr-only" for="cal-filtro-estado">Estado</label>
      <select id="cal-filtro-estado" v-model="filtroEstado" class="input filter">
        <option value="">Todos los estados</option>
        <option value="pendiente">Pendientes</option>
        <option value="completada">Completadas</option>
      </select>
    </div>

    <p v-if="error" class="alert-error" role="alert">{{ error }}</p>
    <p v-if="cargando && !actividades.length" class="state-card" role="status">Cargando calendario…</p>

    <div class="calendar-scroll" :class="{ loading: cargando }">
      <div class="week-grid">
        <section v-for="dia in dias" :key="dia.fecha" class="day-column" :class="{ today: dia.esHoy }">
          <header class="day-heading">
            <span>{{ dia.corto }}</span>
            <strong>{{ dia.numero }}</strong>
          </header>
          <div class="day-content">
            <p class="all-day-label">Todo el día</p>
            <p v-if="!actividadesDelDia(dia.fecha, true).length" class="empty-all-day">—</p>
            <article
              v-for="actividad in actividadesDelDia(dia.fecha, true)"
              :key="actividad.id_actividad"
              class="calendar-event all-day-event"
              :class="[actividad.tipo_actividad, { completed: actividad.completada }]"
            >
              <strong>{{ tipoLabel(actividad.tipo_actividad) }}</strong>
              <span>{{ nombreObjetivo(actividad) }}</span>
              <small>{{ detalle(actividad) }}</small>
            </article>
            <article
              v-for="actividad in actividadesDelDia(dia.fecha, false)"
              :key="actividad.id_actividad"
              class="calendar-event"
              :class="[actividad.tipo_actividad, { completed: actividad.completada }]"
            >
              <strong>{{ actividad.hora_programada?.slice(0, 5) }} · {{ tipoLabel(actividad.tipo_actividad) }}</strong>
              <span>{{ nombreObjetivo(actividad) }}</span>
              <small>{{ detalle(actividad) }}</small>
            </article>
            <p v-if="!actividadesDelDia(dia.fecha, false).length" class="empty-day">
              {{ actividadesDelDia(dia.fecha, true).length ? '' : 'Sin actividades' }}
            </p>
          </div>
        </section>
      </div>
    </div>
    <p v-if="!cargando && !actividadesFiltradas.length" class="calendar-empty">
      No hay actividades para este rango o los filtros seleccionados.
    </p>
  </section>
</template>

<style scoped>
.calendar-heading,
.week-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.calendar-heading {
  justify-content: space-between;
  margin-bottom: 16px;
}

.week-controls h1 {
  margin: 0 2px;
  font-size: 16px;
  font-weight: 700;
}

.nav-button,
.today-button {
  display: grid;
  place-items: center;
  min-width: 34px;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-primary);
}

.nav-button {
  font-size: 22px;
  line-height: 1;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-bottom: 14px;
}

.filter {
  width: auto;
  min-width: 145px;
  padding: 8px 11px;
  background: var(--color-surface);
  font-size: 12px;
}

.calendar-scroll {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.calendar-scroll.loading {
  opacity: 0.65;
}

.week-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(128px, 1fr));
  min-width: 900px;
}

.day-column {
  min-height: 330px;
  border-right: 1px solid var(--color-border);
}

.day-column:last-child {
  border-right: 0;
}

.day-heading {
  display: grid;
  justify-items: center;
  gap: 3px;
  padding: 11px 6px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-alt);
  color: var(--color-text-muted);
  font-size: 10px;
  text-transform: uppercase;
}

.day-heading strong {
  color: var(--color-text);
  font-size: 15px;
}

.day-column.today .day-heading {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.day-column.today .day-heading strong {
  color: var(--color-primary);
}

.day-content {
  display: grid;
  align-content: start;
  gap: 7px;
  min-height: 280px;
  padding: 8px;
}

.all-day-label {
  margin-top: 1px;
  color: var(--color-text-muted);
  font-size: 10px;
}

.empty-all-day,
.empty-day {
  color: var(--color-text-subtle);
  font-size: 11px;
}

.empty-day {
  margin-top: 8px;
  text-align: center;
}

.calendar-event {
  display: grid;
  gap: 3px;
  padding: 8px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-size: 10px;
  overflow-wrap: anywhere;
}

.calendar-event strong {
  font-size: 10px;
}

.calendar-event span {
  font-weight: 600;
}

.calendar-event small {
  color: inherit;
  opacity: 0.8;
}

.calendar-event.alimentacion { background: #f7efd9; border-color: #e8d8ae; color: #70551d; }
.calendar-event.limpieza { background: #e4efe2; border-color: #c9dec5; color: #315c38; }
.calendar-event.enriquecimiento { background: #e3eef1; border-color: #c4dce2; color: #315d69; }
.calendar-event.entrenamiento { background: #eee8f3; border-color: #d9cbe4; color: #5e4d72; }
.calendar-event.completed { opacity: 0.58; }

.all-day-event {
  padding: 6px;
}

.calendar-empty,
.state-card {
  padding: 20px;
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

@media (max-width: 650px) {
  .calendar-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .week-controls {
    flex-wrap: wrap;
  }

  .week-controls h1 {
    flex: 1;
  }
}
</style>
