<script setup lang="ts">
import { computed } from 'vue'
import type { Actividad, Dieta, UsuarioActividad } from '@/types/actividades'
import type { Animal } from '@/types/animales'

const props = defineProps<{
  actividades: Actividad[]
  animales: Animal[]
  dietas: Record<number, Dieta>
  usuariosAuditoria: UsuarioActividad[]
  cargando: boolean
  error: string
  actualizandoId: number | null
}>()
const emit = defineEmits<{ completar: [id: number, observaciones?: string] }>()

const tomas = computed(() =>
  props.actividades
    .filter((actividad) => actividad.tipo_actividad === 'alimentacion')
    .sort((a, b) => (a.hora_programada ?? '').localeCompare(b.hora_programada ?? '')),
)
const realizadas = computed(() => tomas.value.filter((toma) => toma.completada).length)

function nombreAnimal(actividad: Actividad) {
  const animal = props.animales.find((item) => item.id_animal === actividad.id_animal)
  return animal?.nombre ?? animal?.taxonomia.nombre_comun ?? `Ejemplar #${actividad.id_animal}`
}

function plan(actividad: Actividad) {
  if (!actividad.id_dieta) return 'Sin dieta asociada'
  return props.dietas[actividad.id_dieta]?.alimentos.map((alimento) => alimento.nombre_alimento).join(' + ')
    ?? 'Plan alimenticio'
}

function usuarioCompleto(actividad: Actividad) {
  if (!actividad.id_usuario_completo) return ''
  const usuario = props.usuariosAuditoria.find((item) => item.id_usuario === actividad.id_usuario_completo)
  return usuario ? `${usuario.nombre} ${usuario.apellido}` : `Usuario #${actividad.id_usuario_completo}`
}
</script>

<template>
  <section class="monitoring">
    <div class="monitor-heading">
      <div>
        <h1>Monitoreo de alimentación</h1>
        <p>Seguimiento de las tomas programadas para hoy.</p>
      </div>
      <div class="progress" role="status">
        <strong>{{ realizadas }} / {{ tomas.length }}</strong>
        <span>tomas completadas</span>
      </div>
    </div>

    <p v-if="error" class="alert-error" role="alert">{{ error }}</p>
    <p v-if="cargando && !actividades.length" class="state-card" role="status">Cargando tomas…</p>
    <p v-else-if="!cargando && !tomas.length" class="state-card">No hay tomas programadas para hoy.</p>

    <div v-else class="feeding-list">
      <article v-for="toma in tomas" :key="toma.id_actividad" class="feeding-card" :class="{ done: toma.completada }">
        <span class="time">{{ toma.hora_programada?.slice(0, 5) ?? '—' }}</span>
        <div class="animal">
          <strong>{{ nombreAnimal(toma) }}</strong>
          <small>{{ plan(toma) }}</small>
          <small v-if="toma.completada && usuarioCompleto(toma)">
            Completada por: {{ usuarioCompleto(toma) }}
          </small>
        </div>
        <span class="status" :class="{ complete: toma.completada }">
          {{ toma.completada ? 'Completada' : 'Pendiente' }}
        </span>
        <button
          v-if="!toma.completada"
          class="btn btn-primary"
          type="button"
          :disabled="actualizandoId === toma.id_actividad"
          @click="emit('completar', toma.id_actividad)"
        >
          Registrar toma
        </button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.monitor-heading {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
  margin-bottom: 18px;
}

h1 {
  font-size: 16px;
  font-weight: 700;
}

.monitor-heading p {
  margin-top: 6px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.progress {
  display: grid;
  gap: 2px;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  text-align: right;
}

.progress strong {
  color: var(--color-primary);
  font-size: 18px;
}

.progress span {
  color: var(--color-text-muted);
  font-size: 11px;
}

.feeding-list {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.feeding-card {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.feeding-card:last-child {
  border-bottom: 0;
}

.feeding-card.done {
  opacity: 0.68;
}

.time {
  color: var(--color-text-muted);
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 13px;
}

.animal {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.animal strong {
  font-size: 13px;
}

.animal small {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status {
  color: #825d12;
  font-size: 11px;
}

.status.complete {
  color: var(--color-primary);
}

.feeding-card .btn {
  padding: 7px 10px;
  font-size: 11px;
}

.state-card {
  padding: 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: var(--color-text-muted);
  text-align: center;
}

@media (max-width: 700px) {
  .feeding-card {
    grid-template-columns: 50px minmax(0, 1fr);
  }

  .status,
  .feeding-card .btn {
    grid-column: 2;
    justify-self: start;
  }

  .monitor-heading {
    align-items: start;
    flex-direction: column;
  }
}
</style>
