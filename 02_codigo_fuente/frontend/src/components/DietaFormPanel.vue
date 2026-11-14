<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { actividadesApi } from '@/api/actividades'
import { consultas } from '@/api/consultas'
import { sumarDias } from '@/config/actividades'
import { ApiError } from '@/api/http'
import { hoyIso, iniciales } from '@/config/animales'
import type { Animal } from '@/types/animales'
import type { Dieta, DietaCreate, UnidadCantidad, UnidadFrecuencia } from '@/types/actividades'

const props = defineProps<{
  abierto: boolean
  animales: Animal[]
  dietasVigentes: Record<number, Dieta>
  extrasPorDieta: Record<number, { unidades: UnidadCantidad[]; restriccion: boolean }>
}>()
const emit = defineEmits<{
  close: []
  saved: [dieta: Dieta, extras: { unidades: UnidadCantidad[]; restriccion: boolean }]
}>()

interface AlimentoForm {
  nombre_alimento: string
  cantidad: string
  unidad: UnidadCantidad
}

const guardando = ref(false)
const error = ref('')
const animalId = ref(0)
const fechaInicio = ref(hoyIso())
// Opcional: si no se indica, la dieta sigue hasta que se finalice o se reemplace
const fechaFin = ref('')
// Límite hacia el futuro definido en el backend (30 días por defecto)
const inicioMax = ref(sumarDias(hoyIso(), 30))
onMounted(async () => {
  try {
    inicioMax.value = (await consultas.limitesActividades()).dieta_inicio_fecha_max
  } catch {
    // Se usa el valor por defecto; el backend valida igual
  }
})
const frecuenciaValor = ref(1)
const frecuenciaUnidad = ref<UnidadFrecuencia>('dias')
const restriccion = ref(false)
const alimentos = ref<AlimentoForm[]>([nuevoAlimento()])

function nuevoAlimento(): AlimentoForm {
  return { nombre_alimento: '', cantidad: '', unidad: 'g' }
}

const animalSeleccionado = computed(() => props.animales.find((animal) => animal.id_animal === animalId.value))
const dietaAnterior = computed(() => props.dietasVigentes[animalId.value])
// La dieta nueva debe empezar después del inicio de la vigente
const inicioMin = computed(() => (dietaAnterior.value ? sumarDias(dietaAnterior.value.fecha_inicio, 1) : undefined))
const nombreAnimal = computed(
  () => animalSeleccionado.value?.nombre ?? animalSeleccionado.value?.taxonomia.nombre_comun ?? 'el ejemplar',
)

watch(
  () => props.abierto,
  (abierto) => {
    if (!abierto) return
    error.value = ''
    animalId.value = props.animales[0]?.id_animal ?? 0
    fechaInicio.value = hoyIso()
    fechaFin.value = ''
    frecuenciaValor.value = 1
    frecuenciaUnidad.value = 'dias'
    restriccion.value = false
    alimentos.value = [nuevoAlimento()]
  },
)

function agregarAlimento() {
  alimentos.value.push(nuevoAlimento())
}

function quitarAlimento(indice: number) {
  if (alimentos.value.length > 1) alimentos.value.splice(indice, 1)
}

function validar(): string {
  if (!animalId.value) return 'Selecciona un ejemplar.'
  if (!fechaInicio.value) return 'Indica la fecha de inicio de la dieta.'
  if (fechaInicio.value > inicioMax.value) return 'La dieta puede empezar como máximo 30 días hacia adelante.'
  if (inicioMin.value && fechaInicio.value < inicioMin.value) {
    return `La dieta nueva debe empezar después del inicio de la dieta vigente (${dietaAnterior.value!.fecha_inicio}).`
  }
  if (fechaFin.value && fechaFin.value < fechaInicio.value) return 'La fecha de fin no puede ser anterior a la de inicio.'
  if (!Number.isInteger(frecuenciaValor.value) || frecuenciaValor.value <= 0) {
    return 'La frecuencia debe ser un número entero mayor que cero.'
  }
  if (
    alimentos.value.some(
      (alimento) =>
        !alimento.nombre_alimento.trim() ||
        !Number.isFinite(Number(alimento.cantidad)) ||
        Number(alimento.cantidad) <= 0,
    )
  ) {
    return 'Cada alimento debe tener nombre y cantidad mayor que cero.'
  }
  return ''
}

function cantidadParaBackend(alimento: AlimentoForm): number {
  const cantidad = Number(alimento.cantidad)
  return alimento.unidad === 'kg' ? cantidad * 1000 : cantidad
}

async function guardar() {
  error.value = validar()
  if (error.value) return
  if (dietaAnterior.value && !window.confirm(`Registrar esta dieta finalizará la dieta vigente de ${nombreAnimal.value}. ¿Continuar?`)) {
    return
  }

  const extras = {
    unidades: alimentos.value.map((alimento) => alimento.unidad),
    restriccion: restriccion.value,
  }
  const datos: DietaCreate = {
    id_animal: animalId.value,
    fecha_inicio: fechaInicio.value,
    ...(fechaFin.value ? { fecha_fin: fechaFin.value } : {}),
    frecuencia_valor: frecuenciaValor.value,
    frecuencia_unidad: frecuenciaUnidad.value,
    es_restriccion: restriccion.value,
    alimentos: alimentos.value.map((alimento) => ({
      nombre_alimento: alimento.nombre_alimento.trim(),
      cantidad_gramos: cantidadParaBackend(alimento),
      unidad_cantidad: alimento.unidad,
    })),
  }

  guardando.value = true
  try {
    const dieta = await actividadesApi.crearDieta(datos)
    emit('saved', dieta, extras)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo registrar la dieta.'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div v-if="abierto" class="form-backdrop" @click.self="emit('close')" @keydown.esc="emit('close')">
    <section
      class="diet-form card"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dieta-form-title"
      tabindex="-1"
    >
      <div class="form-heading">
        <div>
          <p class="eyebrow">Plan nutricional</p>
          <h2 id="dieta-form-title">Nueva dieta</h2>
        </div>
        <button class="close-button" type="button" aria-label="Cerrar formulario" @click="emit('close')">×</button>
      </div>

      <form class="diet-fields" @submit.prevent="guardar">
      <div class="field">
        <label for="dieta-animal">Ejemplar</label>
        <select id="dieta-animal" v-model.number="animalId" class="input" required>
          <option :value="0" disabled>Seleccionar ejemplar…</option>
          <option v-for="animal in animales" :key="animal.id_animal" :value="animal.id_animal">
            {{ animal.nombre ?? animal.taxonomia.nombre_comun }} — {{ animal.recinto.nombre_recinto }}
          </option>
        </select>
      </div>

      <div class="foods">
        <div v-for="(alimento, indice) in alimentos" :key="indice" class="food-row">
          <div class="field">
            <label :for="`alimento-${indice}`">Alimento</label>
            <input
              :id="`alimento-${indice}`"
              v-model="alimento.nombre_alimento"
              class="input"
              :placeholder="indice === 0 ? 'Ej. Fruta picada + insectos' : 'Nombre del alimento'"
              required
            />
          </div>
          <div class="field">
            <label :for="`cantidad-${indice}`">Cantidad</label>
            <div class="amount-input">
              <input
                :id="`cantidad-${indice}`"
                v-model="alimento.cantidad"
                class="input"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="Ej. 400"
                required
              />
              <select v-model="alimento.unidad" class="input unit-select" :aria-label="`Unidad de ${alimento.nombre_alimento || 'cantidad'}`">
                <option value="g">g</option>
                <option value="kg">kg</option>
                <option value="unidad">unidad</option>
              </select>
            </div>
          </div>
          <button
            v-if="alimentos.length > 1"
            class="remove-food"
            type="button"
            :aria-label="`Quitar alimento ${indice + 1}`"
            @click="quitarAlimento(indice)"
          >
            Quitar
          </button>
        </div>
        <button class="add-food" type="button" @click="agregarAlimento">+ Agregar otro alimento</button>
      </div>

      <div class="form-grid">
        <div class="field">
          <label for="fecha-inicio">Fecha de inicio</label>
          <input id="fecha-inicio" v-model="fechaInicio" class="input" type="date" :min="inicioMin" :max="inicioMax" required />
        </div>
        <div class="field">
          <label for="fecha-fin">Fecha de fin <span class="opcional">(opcional)</span></label>
          <input id="fecha-fin" v-model="fechaFin" class="input" type="date" :min="fechaInicio" />
        </div>
        <div class="field">
          <label for="frecuencia">Frecuencia</label>
          <div class="amount-input">
            <input id="frecuencia" v-model.number="frecuenciaValor" class="input" type="number" min="1" step="1" required />
            <select v-model="frecuenciaUnidad" class="input unit-select" aria-label="Unidad de frecuencia">
              <option value="horas">horas</option>
              <option value="dias">días</option>
              <option value="semanas">semanas</option>
            </select>
          </div>
        </div>
      </div>

      <label class="restriction">
        <input v-model="restriccion" type="checkbox" />
        <span>Es una restricción alimenticia (indicación veterinaria)</span>
      </label>

      <p v-if="dietaAnterior" class="replacement-notice" role="status">
        Registrar esta dieta finalizará la dieta vigente de <strong>{{ nombreAnimal }}</strong>.
      </p>
      <p class="backend-note">
        El backend aún almacena cantidades solo en gramos y no guarda la unidad ni la marca de restricción.
      </p>
      <p v-if="error" class="alert-error" role="alert">{{ error }}</p>

      <div class="form-actions">
        <button class="btn btn-secondary" type="button" @click="emit('close')">Cancelar</button>
        <button class="btn btn-primary" type="submit" :disabled="guardando">
          {{ guardando ? 'Guardando…' : 'Guardar dieta' }}
        </button>
      </div>
      </form>
    </section>
  </div>
</template>

<style scoped>
.opcional {
  font-weight: 400;
  color: var(--color-text-muted);
}

.form-backdrop {
  position: fixed;
  z-index: 1000;
  inset: 0;
  display: grid;
  place-items: center;
  overflow-y: auto;
  padding: 18px;
  background: rgb(25 34 27 / 48%);
}

.diet-form {
  width: min(760px, 100%);
  max-height: calc(100dvh - 36px);
  overflow-y: auto;
  margin: auto;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.form-heading,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.form-heading {
  margin-bottom: 16px;
}

.form-heading h2 {
  font-size: 19px;
  font-weight: 700;
}

.eyebrow {
  margin-bottom: 3px;
  color: var(--color-text-muted);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.close-button {
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 24px;
}

.diet-fields {
  display: grid;
  gap: 16px;
}

.foods {
  display: grid;
  gap: 10px;
}

.food-row,
.form-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(210px, 1fr) auto;
  align-items: end;
  gap: 12px;
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.amount-input {
  display: flex;
  gap: 6px;
}

.amount-input .input:first-child {
  min-width: 0;
}

.unit-select {
  width: auto;
  min-width: 76px;
  padding-right: 24px;
}

.add-food,
.remove-food {
  width: fit-content;
  padding: 7px 10px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-primary);
}

.remove-food {
  margin-bottom: 2px;
  color: var(--color-danger);
}

.restriction {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.restriction input {
  accent-color: var(--color-primary);
}

.replacement-notice {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-soft);
  color: var(--color-text);
}

.backend-note {
  color: var(--color-text-muted);
  font-size: 12px;
}

.form-actions {
  justify-content: flex-end;
}

@media (max-width: 650px) {
  .form-backdrop {
    align-items: start;
    padding: 10px;
  }

  .diet-form {
    max-height: calc(100dvh - 20px);
    padding: 16px;
  }

  .food-row,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }
}
</style>
