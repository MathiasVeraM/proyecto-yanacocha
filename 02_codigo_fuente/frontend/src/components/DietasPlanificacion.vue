<script setup lang="ts">
import { computed, ref } from 'vue'
import { iniciales } from '@/config/animales'
import type { Dieta, UnidadCantidad } from '@/types/actividades'
import type { Animal } from '@/types/animales'

const props = defineProps<{
  animales: Animal[]
  dietasVigentes: Record<number, Dieta>
  historiales: Record<number, Dieta[]>
  extrasPorDieta: Record<number, { unidades: UnidadCantidad[]; restriccion: boolean }>
  cargando: boolean
  error: string
}>()
const emit = defineEmits<{ registrar: [] }>()
const historialAbierto = ref<number | null>(null)

const filas = computed(() =>
  props.animales
    .map((animal) => ({ animal, dieta: props.dietasVigentes[animal.id_animal] }))
    .filter((fila): fila is { animal: Animal; dieta: Dieta } => Boolean(fila.dieta))
    .sort((a, b) => (a.animal.nombre ?? a.animal.taxonomia.nombre_comun).localeCompare(b.animal.nombre ?? b.animal.taxonomia.nombre_comun)),
)

function frecuencia(dieta: Dieta) {
  const unidad = { horas: 'horas', dias: 'días', semanas: 'semanas' }[dieta.frecuencia_unidad]
  return `Cada ${dieta.frecuencia_valor} ${unidad}`
}

function alimentos(dieta: Dieta) {
  return dieta.alimentos.map((alimento) => alimento.nombre_alimento).join(' + ')
}

function cantidad(dieta: Dieta) {
  const extra = props.extrasPorDieta[dieta.id_dieta]
  return dieta.alimentos
    .map((alimento, indice) => {
      const unidad = extra?.unidades[indice] ?? 'g'
      const valor = unidad === 'kg' ? alimento.cantidad_gramos / 1000 : alimento.cantidad_gramos
      return `${Number.isInteger(valor) ? valor : valor.toFixed(2)} ${unidad}`
    })
    .join(' + ')
}

function toggleHistorial(idAnimal: number) {
  historialAbierto.value = historialAbierto.value === idAnimal ? null : idAnimal
}
</script>

<template>
  <section class="diets">
    <div class="diet-heading">
      <div>
        <h1>Dietas planificadas</h1>
        <p class="description">
          Plan nutricional asignado a cada ejemplar. Las restricciones vienen de indicaciones veterinarias.
        </p>
      </div>
      <button class="btn btn-primary" type="button" @click="emit('registrar')">+ Registrar dieta</button>
    </div>

    <p v-if="error" class="alert-error" role="alert">{{ error }}</p>
    <p v-if="cargando && !filas.length" class="state-card" role="status">Cargando dietas…</p>
    <p v-else-if="!cargando && !filas.length" class="state-card">
      No hay dietas vigentes. Puedes registrar el primer plan nutricional.
    </p>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Ejemplar</th>
            <th>Alimento</th>
            <th>Cantidad</th>
            <th>Frecuencia</th>
            <th>Restricción</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="{ animal, dieta } in filas" :key="dieta.id_dieta">
            <tr>
              <td>
                <div class="animal-cell">
                  <span class="avatar">{{ iniciales(animal.nombre ?? animal.taxonomia.nombre_comun) }}</span>
                  <span>
                    <strong>{{ animal.nombre ?? animal.taxonomia.nombre_comun }}</strong>
                    <small>{{ animal.taxonomia.nombre_comun }}</small>
                  </span>
                </div>
              </td>
              <td>{{ alimentos(dieta) }}</td>
              <td>{{ cantidad(dieta) }}</td>
              <td>{{ frecuencia(dieta) }}</td>
              <td>
                <span v-if="extrasPorDieta[dieta.id_dieta]?.restriccion || dieta.es_restriccion" class="restriction-badge">
                  Indicación veterinaria
                </span>
                <span v-else class="neutral-badge">Vigente</span>
              </td>
              <td>
                <div class="actions">
                  <button class="history-button" type="button" @click="toggleHistorial(animal.id_animal)">
                    {{ historialAbierto === animal.id_animal ? 'Ocultar historial' : 'Historial' }}
                  </button>
                  <button
                    class="finish-button"
                    type="button"
                    disabled
                    title="TODO: el backend aún no tiene endpoint para finalizar una dieta"
                  >
                    Finalizar dieta
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="historialAbierto === animal.id_animal" class="history-row">
              <td colspan="6">
                <div class="history-content">
                  <strong>Historial de {{ animal.nombre ?? animal.taxonomia.nombre_comun }}</strong>
                  <p v-if="!(historiales[animal.id_animal] ?? []).some((item) => !item.vigente)">
                    No hay dietas anteriores registradas.
                  </p>
                  <ul v-else>
                    <li v-for="anterior in (historiales[animal.id_animal] ?? []).filter((item) => !item.vigente)" :key="anterior.id_dieta">
                      {{ anterior.fecha_inicio }} — {{ anterior.fecha_fin ?? 'Sin fecha de cierre' }} ·
                      {{ alimentos(anterior) }} · {{ frecuencia(anterior) }}
                    </li>
                  </ul>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <p class="backend-note">
      El servicio aún no persiste unidad de cantidad ni indicador de restricción; Finalizar dieta está deshabilitado hasta que exista endpoint.
    </p>
  </section>
</template>

<style scoped>
.diet-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  margin-bottom: 16px;
}

h1 {
  font-size: 16px;
  font-weight: 700;
}

.description {
  margin-top: 7px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

table {
  width: 100%;
  min-width: 800px;
  border-collapse: collapse;
  text-align: left;
}

th,
td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

th {
  background: var(--color-surface-alt);
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

tbody tr:last-child td {
  border-bottom: 0;
}

.animal-cell {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 145px;
}

.animal-cell > span:last-child {
  display: grid;
  gap: 2px;
}

.animal-cell strong {
  font-size: 12px;
}

.animal-cell small {
  color: var(--color-text-muted);
  font-size: 10px;
}

.avatar {
  display: grid;
  place-items: center;
  flex: 0 0 30px;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 700;
}

.restriction-badge,
.neutral-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  background: #f7edd1;
  color: #805c16;
  font-size: 10px;
  white-space: nowrap;
}

.neutral-badge {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.history-button,
.finish-button {
  padding: 6px 8px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-primary);
  font-size: 10px;
  white-space: nowrap;
}

.finish-button {
  color: var(--color-danger);
}

.history-row td {
  padding: 0;
  background: #f5f1e7;
}

.history-content {
  display: grid;
  gap: 8px;
  padding: 12px 16px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.history-content ul {
  display: grid;
  gap: 4px;
  padding-left: 18px;
}

.backend-note,
.state-card {
  margin-top: 12px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.state-card {
  padding: 35px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  font-size: 14px;
  text-align: center;
}

@media (max-width: 650px) {
  .diet-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .diet-heading .btn {
    width: 100%;
  }
}
</style>
