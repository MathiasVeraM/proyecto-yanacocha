<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { actividadesApi } from '@/api/actividades'
import { ApiError } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import type { Animal, Recinto } from '@/types/animales'
import type { TipoActividad, TipoEnriquecimiento, UsuarioResponsable } from '@/types/actividades'

interface DiaSemana {
  fecha: string
  etiqueta: string
}

const props = defineProps<{
  abierto: boolean
  dias: DiaSemana[]
  animales: Animal[]
  recintos: Recinto[]
  usuarios: UsuarioResponsable[]
}>()
const emit = defineEmits<{ close: []; saved: [actividad: { id_actividad: number }, responsableId: number | null] }>()
const auth = useAuthStore()
const guardando = ref(false)
const error = ref('')
const tipo = ref<Exclude<TipoActividad, 'alimentacion'>>('enriquecimiento')
const formulario = reactive({
  id_animal: 0,
  id_recinto: 0,
  fecha_programada: '',
  hora_programada: '08:00',
  observaciones: '',
  tipo_enriquecimiento: 'sensorial' as TipoEnriquecimiento,
  descripcion_estimulo: '',
  objetivo_entrenamiento: '',
  tipo_refuerzo: '',
  duracion_horas: 0,
  duracion_minutos: 30,
  id_usuario_responsable: auth.payload?.id_usuario ?? 0,
})

const opcionesDia = computed(() => props.dias)
const seleccionado = computed(() => props.animales.find((animal) => animal.id_animal === formulario.id_animal))
const nombreSeleccionado = computed(
  () => seleccionado.value?.nombre ?? seleccionado.value?.taxonomia.nombre_comun ?? 'el ejemplar',
)

watch(
  () => props.abierto,
  (abierto) => {
    if (!abierto) return
    error.value = ''
    formulario.fecha_programada = props.dias[0]?.fecha ?? ''
    formulario.id_animal = props.animales[0]?.id_animal ?? 0
    formulario.id_recinto = props.recintos[0]?.id_recinto ?? 0
    formulario.id_usuario_responsable = auth.payload?.id_usuario ?? 0
    tipo.value = 'enriquecimiento'
  },
)

function validar(): string {
  if (!formulario.fecha_programada) return 'Selecciona un día para la actividad.'
  if (
    tipo.value !== 'enriquecimiento' &&
    (formulario.duracion_horas < 0 || formulario.duracion_minutos < 0 || formulario.duracion_minutos > 59)
  ) {
    return 'La duración debe tener horas no negativas y minutos entre 0 y 59.'
  }
  if (tipo.value !== 'enriquecimiento' && formulario.duracion_horas * 60 + formulario.duracion_minutos <= 0) {
    return 'La duración estimada debe ser mayor que cero.'
  }
  if (tipo.value === 'limpieza') {
    if (!formulario.id_recinto) return 'Selecciona un recinto o área.'
  } else if (!formulario.id_animal) {
    return 'Selecciona un ejemplar.'
  }
  if (tipo.value === 'enriquecimiento') {
    if (!formulario.hora_programada) return 'La hora es obligatoria para el enriquecimiento.'
    if (!formulario.descripcion_estimulo.trim()) return 'Describe el estímulo del enriquecimiento.'
  }
  if (tipo.value === 'entrenamiento') {
    if (!formulario.hora_programada) return 'La hora es obligatoria para el entrenamiento.'
    if (!formulario.objetivo_entrenamiento.trim()) return 'Indica el objetivo del entrenamiento.'
    if (!formulario.tipo_refuerzo.trim()) return 'Indica el tipo de refuerzo.'
    if (formulario.tipo_refuerzo.length > 150) return 'El tipo de refuerzo admite hasta 150 caracteres.'
  }
  return ''
}

async function guardar() {
  error.value = validar()
  if (error.value) return

  guardando.value = true
  try {
    const responsable = formulario.id_usuario_responsable || undefined
    const observaciones = formulario.observaciones.trim() || undefined
    let actividad: { id_actividad: number }
    if (tipo.value === 'enriquecimiento') {
      actividad = await actividadesApi.programarEnriquecimiento({
        id_animal: formulario.id_animal,
        tipo_enriquecimiento: formulario.tipo_enriquecimiento,
        fecha_programada: formulario.fecha_programada,
        hora_programada: formulario.hora_programada,
        descripcion_estimulo: formulario.descripcion_estimulo.trim(),
        observaciones,
        id_usuario_responsable: responsable,
      })
    } else if (tipo.value === 'entrenamiento') {
      actividad = await actividadesApi.programarEntrenamiento({
        id_animal: formulario.id_animal,
        fecha_programada: formulario.fecha_programada,
        hora_programada: formulario.hora_programada,
        duracion_horas: formulario.duracion_horas,
        duracion_minutos: formulario.duracion_minutos,
        objetivo_entrenamiento: formulario.objetivo_entrenamiento.trim(),
        tipo_refuerzo: formulario.tipo_refuerzo.trim(),
        observaciones,
        id_usuario_responsable: responsable,
      })
    } else {
      actividad = await actividadesApi.programarLimpieza({
        id_recinto: formulario.id_recinto,
        fecha_programada: formulario.fecha_programada,
        hora_programada: formulario.hora_programada || undefined,
        duracion_horas: formulario.duracion_horas,
        duracion_minutos: formulario.duracion_minutos,
        observaciones,
        id_usuario_responsable: responsable,
      })
    }
    emit('saved', actividad, formulario.id_usuario_responsable || auth.payload?.id_usuario || null)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo guardar la actividad.'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div v-if="abierto" class="form-backdrop" @click.self="emit('close')" @keydown.esc="emit('close')">
    <section
      class="form-card"
      role="dialog"
      aria-modal="true"
      aria-labelledby="actividad-form-title"
      tabindex="-1"
    >
      <div class="form-heading">
        <div>
          <p class="eyebrow">Planificación</p>
          <h2 id="actividad-form-title">Nueva actividad</h2>
        </div>
        <button class="close-button" type="button" aria-label="Cerrar formulario" @click="emit('close')">×</button>
      </div>

      <form class="activity-form" @submit.prevent="guardar">
      <div class="form-grid">
        <div class="field">
          <label for="tipo-actividad">Tipo</label>
          <select id="tipo-actividad" v-model="tipo" class="input">
            <option value="enriquecimiento">Enriquecimiento</option>
            <option value="entrenamiento">Entrenamiento</option>
            <option value="limpieza">Limpieza</option>
          </select>
        </div>

        <div v-if="tipo === 'limpieza'" class="field">
          <label for="actividad-recinto">Recinto o área</label>
          <select id="actividad-recinto" v-model.number="formulario.id_recinto" class="input">
            <option :value="0" disabled>Seleccionar recinto…</option>
            <option v-for="recinto in recintos" :key="recinto.id_recinto" :value="recinto.id_recinto">
              {{ recinto.nombre_recinto }}
            </option>
          </select>
        </div>
        <div v-else class="field">
          <label for="actividad-animal">Ejemplar</label>
          <select id="actividad-animal" v-model.number="formulario.id_animal" class="input">
            <option :value="0" disabled>Seleccionar ejemplar…</option>
            <option v-for="animal in animales" :key="animal.id_animal" :value="animal.id_animal">
              {{ animal.nombre ?? animal.taxonomia.nombre_comun }} — {{ animal.recinto.nombre_recinto }}
            </option>
          </select>
        </div>

        <div class="field">
          <label for="actividad-dia">Día</label>
          <select id="actividad-dia" v-model="formulario.fecha_programada" class="input">
            <option v-for="dia in opcionesDia" :key="dia.fecha" :value="dia.fecha">{{ dia.etiqueta }}</option>
          </select>
        </div>

        <div class="field">
          <label for="actividad-hora">Hora {{ tipo === 'limpieza' ? '(opcional)' : '' }}</label>
          <input
            id="actividad-hora"
            v-model="formulario.hora_programada"
            class="input"
            type="time"
            :required="tipo !== 'limpieza'"
          />
        </div>
      </div>

      <div v-if="tipo === 'enriquecimiento'" class="form-grid">
        <div class="field">
          <label for="tipo-enriquecimiento">Tipo de enriquecimiento</label>
          <select id="tipo-enriquecimiento" v-model="formulario.tipo_enriquecimiento" class="input">
            <option value="social">Social</option>
            <option value="sensorial">Sensorial</option>
            <option value="alimenticio">Alimenticio</option>
            <option value="cognitivo">Cognitivo</option>
          </select>
        </div>
        <div class="field field-wide">
          <label for="estimulo">Descripción del estímulo</label>
          <textarea id="estimulo" v-model="formulario.descripcion_estimulo" class="input" rows="2" required />
        </div>
      </div>

      <div v-if="tipo === 'entrenamiento'" class="form-grid">
        <div class="field">
          <label for="objetivo">Objetivo</label>
          <input id="objetivo" v-model="formulario.objetivo_entrenamiento" class="input" required />
        </div>
        <div class="field">
          <label for="refuerzo">Tipo de refuerzo</label>
          <input id="refuerzo" v-model="formulario.tipo_refuerzo" class="input" maxlength="150" required />
        </div>
      </div>

      <div v-if="tipo !== 'enriquecimiento'" class="form-grid form-grid-bottom">
        <div class="field">
          <label>Duración estimada</label>
          <div class="duration-inputs">
            <input v-model.number="formulario.duracion_horas" class="input" type="number" min="0" max="32767" aria-label="Horas de duración" />
            <span>h</span>
            <input v-model.number="formulario.duracion_minutos" class="input" type="number" min="0" max="59" aria-label="Minutos de duración" />
            <span>min</span>
          </div>
        </div>
        <div v-if="tipo === 'limpieza'" class="field field-wide">
          <label for="limpieza-nota">Nota (opcional)</label>
          <input id="limpieza-nota" v-model="formulario.observaciones" class="input" />
        </div>
      </div>

      <div v-if="tipo === 'enriquecimiento'" class="field">
        <label for="enriquecimiento-nota">Nota (opcional)</label>
        <input id="enriquecimiento-nota" v-model="formulario.observaciones" class="input" />
      </div>
      <div v-if="tipo === 'entrenamiento'" class="field">
        <label for="entrenamiento-nota">Nota (opcional)</label>
        <input id="entrenamiento-nota" v-model="formulario.observaciones" class="input" />
      </div>

      <div class="field responsible-field">
        <label for="responsable">Responsable de la actividad</label>
        <select id="responsable" v-model.number="formulario.id_usuario_responsable" class="input">
          <option :value="0">Usar usuario de la sesión</option>
          <option v-for="usuario in usuarios" :key="usuario.id_usuario" :value="usuario.id_usuario">
            {{ usuario.nombre }} {{ usuario.apellido }}
          </option>
        </select>
        <small v-if="tipo !== 'limpieza' && seleccionado">Ejemplar: {{ nombreSeleccionado }}</small>
      </div>

      <p v-if="error" class="alert-error" role="alert">{{ error }}</p>
      <div class="form-actions">
        <button class="btn btn-secondary" type="button" @click="emit('close')">Cancelar</button>
        <button class="btn btn-primary" type="submit" :disabled="guardando">
          {{ guardando ? 'Guardando…' : 'Agregar al calendario' }}
        </button>
      </div>
      <p class="backend-note">
        El backend aún no guarda el responsable seleccionado; por ahora identifica al usuario que programó la actividad.
      </p>
      </form>
    </section>
  </div>
</template>

<style scoped>
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

.form-card {
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
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.close-button {
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 24px;
}

.activity-form {
  display: grid;
  gap: 14px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field-wide {
  grid-column: span 2;
}

.input {
  min-width: 0;
  background: var(--color-surface);
}

textarea.input {
  resize: vertical;
}

.duration-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration-inputs .input {
  width: 82px;
}

.duration-inputs span,
.responsible-field small,
.backend-note {
  color: var(--color-text-muted);
  font-size: 12px;
}

.responsible-field {
  max-width: 520px;
}

.form-actions {
  justify-content: flex-end;
  padding-top: 4px;
}

.backend-note {
  text-align: right;
}

@media (max-width: 640px) {
  .form-backdrop {
    align-items: start;
    padding: 10px;
  }

  .form-card {
    max-height: calc(100dvh - 20px);
    padding: 16px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .field-wide {
    grid-column: auto;
  }

  .form-actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }
}
</style>
