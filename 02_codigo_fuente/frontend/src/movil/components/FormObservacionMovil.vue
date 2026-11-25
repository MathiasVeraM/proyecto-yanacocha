<script setup lang="ts">
import { computed, reactive } from 'vue'
import { CATEGORIAS_OBSERVACION, SEVERIDADES, generaAlerta } from '@/config/actividades'
import type { Actividad, CategoriaObservacion, SeveridadObservacion } from '@/types/actividades'

const props = defineProps<{ actividad: Actividad }>()
const emit = defineEmits<{
  guardar: [datos: { categoria: CategoriaObservacion; severidad: SeveridadObservacion; detalle: string }]
}>()

// Listas cerradas: solo se puede elegir entre las opciones (HU-10 CA-02)
const categorias = Object.entries(CATEGORIAS_OBSERVACION) as [
  CategoriaObservacion,
  (typeof CATEGORIAS_OBSERVACION)[CategoriaObservacion],
][]

const form = reactive({
  // En una limpieza lo normal es observar el recinto; en lo demás, el comportamiento
  categoria: (props.actividad.tipo_actividad === 'limpieza' ? 'recinto' : 'comportamiento') as CategoriaObservacion,
  severidad: 'bajo' as SeveridadObservacion,
  detalle: '',
  error: '',
})

const alerta = computed(() => generaAlerta(form.categoria, form.severidad))
const ejemplo = computed(() => CATEGORIAS_OBSERVACION[form.categoria].ejemplo)
const faltan = computed(() => Math.max(0, 10 - form.detalle.trim().length))

function guardar() {
  const detalle = form.detalle.trim()
  if (detalle.length < 10) {
    form.error = 'Describe la observación con al menos 10 caracteres.'
    return
  }
  emit('guardar', { categoria: form.categoria, severidad: form.severidad, detalle })
}
</script>

<template>
  <form class="form" @submit.prevent="guardar">
    <fieldset>
      <legend>Categoría</legend>
      <div class="opciones">
        <button
          v-for="[valor, info] in categorias"
          :key="valor"
          type="button"
          class="m-chip"
          :aria-pressed="form.categoria === valor"
          @click="form.categoria = valor"
        >
          {{ info.label }}
        </button>
      </div>
      <p class="ayuda">{{ CATEGORIAS_OBSERVACION[form.categoria].ayuda }}</p>
    </fieldset>

    <fieldset>
      <legend>Severidad</legend>
      <div class="opciones">
        <button
          v-for="nivel in SEVERIDADES"
          :key="nivel"
          type="button"
          class="m-chip"
          :aria-pressed="form.severidad === nivel"
          @click="form.severidad = nivel"
        >
          {{ nivel.charAt(0).toUpperCase() + nivel.slice(1) }}
        </button>
      </div>
      <p v-if="alerta" class="aviso">Quedará marcada como alerta para el personal responsable.</p>
    </fieldset>

    <div class="campo">
      <label for="detalle">Descripción</label>
      <textarea
        id="detalle"
        v-model="form.detalle"
        class="m-input"
        rows="4"
        :placeholder="ejemplo"
        @input="form.error = ''"
      />
      <p v-if="form.error" class="error">{{ form.error }}</p>
      <p v-else-if="faltan" class="ayuda">Faltan {{ faltan }} caracteres como mínimo.</p>
    </div>

    <button type="submit" class="m-btn m-btn-primario m-btn-bloque">Guardar observación</button>
  </form>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

fieldset {
  border: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

legend,
label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 6px;
}

.opciones {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.campo {
  display: flex;
  flex-direction: column;
}

textarea {
  resize: none;
}

.ayuda {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.aviso {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: #f5e9c4;
  color: #87661a;
  font-size: 14px;
}

.error {
  margin-top: 6px;
  font-size: 14px;
  color: var(--color-danger);
}
</style>
