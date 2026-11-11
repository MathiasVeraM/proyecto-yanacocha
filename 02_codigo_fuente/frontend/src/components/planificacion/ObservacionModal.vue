<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { CATEGORIAS_OBSERVACION, SEVERIDADES, generaAlerta } from '@/config/actividades'
import type { Actividad, CategoriaObservacion, ObservacionCreate, SeveridadObservacion } from '@/types/actividades'

const props = defineProps<{
  actividad: Actividad | null
  titulo: string
  subtitulo: string
  guardando: boolean
  error: string
}>()
const emit = defineEmits<{ close: []; guardar: [datos: ObservacionCreate, marcarHecha: boolean] }>()

const form = reactive({
  categoria: 'comportamiento' as CategoriaObservacion,
  severidad: 'bajo' as SeveridadObservacion,
  detalle: '',
  marcarHecha: false,
  error: '',
})

// Al abrir: en una limpieza lo normal es observar el recinto; en lo demás, el comportamiento
watch(
  () => props.actividad,
  (actividad) => {
    if (!actividad) return
    form.categoria = actividad.tipo_actividad === 'limpieza' ? 'recinto' : 'comportamiento'
    form.severidad = 'bajo'
    form.detalle = ''
    form.marcarHecha = false
    form.error = ''
  },
  { immediate: true },
)

const alerta = computed(() => generaAlerta(form.categoria, form.severidad))
const categorias = Object.entries(CATEGORIAS_OBSERVACION) as [CategoriaObservacion, (typeof CATEGORIAS_OBSERVACION)[CategoriaObservacion]][]

function guardar() {
  const detalle = form.detalle.trim()
  if (detalle.length < 10) {
    form.error = 'Describe la observación con al menos 10 caracteres para que el equipo la entienda.'
    return
  }
  form.error = ''
  emit('guardar', { categoria: form.categoria, severidad: form.severidad, detalle }, form.marcarHecha)
}

const capitalizar = (texto: string) => texto.charAt(0).toUpperCase() + texto.slice(1)
</script>

<template>
  <div v-if="actividad" class="velo" @click.self="emit('close')" @keydown.esc="emit('close')">
    <form class="modal" role="dialog" aria-modal="true" aria-labelledby="obs-titulo" @submit.prevent="guardar">
      <header class="modal-h">
        <div>
          <h3 id="obs-titulo">Agregar observación</h3>
          <p>{{ titulo }} · {{ subtitulo }}</p>
        </div>
        <button class="cerrar" type="button" aria-label="Cerrar" @click="emit('close')">×</button>
      </header>

      <div class="modal-b">
        <div class="campo">
          <span id="obs-cat" class="etiqueta">Categoría</span>
          <div class="opciones" role="radiogroup" aria-labelledby="obs-cat">
            <button
              v-for="[clave, cat] in categorias"
              :key="clave"
              type="button"
              role="radio"
              class="opcion"
              :class="{ on: form.categoria === clave }"
              :aria-checked="form.categoria === clave"
              @click="form.categoria = clave"
            >
              <strong>{{ cat.label }}</strong>
              <small>{{ cat.ayuda }}</small>
            </button>
          </div>
        </div>

        <div class="campo">
          <span id="obs-sev" class="etiqueta">Nivel de severidad</span>
          <div class="severidades" role="radiogroup" aria-labelledby="obs-sev">
            <button
              v-for="sev in SEVERIDADES"
              :key="sev"
              type="button"
              role="radio"
              class="sev"
              :class="[`sev-${sev}`, { on: form.severidad === sev }]"
              :aria-checked="form.severidad === sev"
              @click="form.severidad = sev"
            >
              <i aria-hidden="true" />{{ capitalizar(sev) }}
            </button>
          </div>
        </div>

        <div class="campo">
          <label class="etiqueta" for="obs-detalle">Detalle de la observación</label>
          <textarea
            id="obs-detalle"
            v-model="form.detalle"
            class="input"
            rows="4"
            :placeholder="CATEGORIAS_OBSERVACION[form.categoria].ejemplo"
          />
        </div>

        <p v-if="alerta" class="aviso" role="status">
          <strong>Se generará una alerta automática</strong> para el veterinario y el encargado de manejo
          animal, porque es {{ CATEGORIAS_OBSERVACION[form.categoria].label.toLowerCase() }} con severidad
          {{ form.severidad }}.
        </p>

        <label v-if="!actividad.completada" class="check" for="obs-hecha">
          <input id="obs-hecha" v-model="form.marcarHecha" type="checkbox" />
          Marcar también la actividad como hecha
        </label>

        <p v-if="form.error || error" class="alert-error" role="alert">{{ form.error || error }}</p>
      </div>

      <footer class="modal-f">
        <button class="btn btn-secondary" type="button" @click="emit('close')">Cancelar</button>
        <button class="btn btn-primary" type="submit" :disabled="guardando">
          {{ guardando ? 'Guardando…' : 'Guardar observación' }}
        </button>
      </footer>
    </form>
  </div>
</template>

<style scoped>
.velo {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(34, 40, 29, 0.45);
}

.modal {
  width: min(560px, 100%);
  max-height: calc(100vh - 32px);
  overflow: auto;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.modal-h {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 20px 22px 0;
}

.modal-h h3 {
  font-family: var(--font-serif);
  font-size: 19px;
  font-weight: 600;
}

.modal-h p {
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.cerrar {
  border: none;
  background: none;
  font-size: 20px;
  line-height: 1;
  color: var(--color-text-muted);
}

.modal-b {
  display: grid;
  gap: 16px;
  padding: 18px 22px;
}

.modal-f {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 22px 20px;
}

.campo {
  display: grid;
  gap: 6px;
}

.etiqueta {
  font-size: 12px;
  color: var(--color-text-muted);
}

.opciones {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.opcion {
  display: grid;
  gap: 2px;
  padding: 10px 12px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  text-align: left;
}

.opcion strong {
  font-size: 13.5px;
}

.opcion small {
  font-size: 11.5px;
  color: var(--color-text-muted);
}

.opcion:hover {
  border-color: var(--color-primary);
}

.opcion.on {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  box-shadow: inset 0 0 0 1px var(--color-primary);
}

.severidades {
  display: flex;
  gap: 8px;
}

.sev {
  display: inline-flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 9px 12px;
  border: 1px solid var(--color-border-strong);
  border-radius: 999px;
  background: var(--color-surface);
  font-size: 13px;
  font-weight: 600;
}

.sev i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.sev-bajo i {
  background: var(--color-primary);
}

.sev-medio i {
  background: #c99a2e;
}

.sev-alto i {
  background: var(--color-danger);
}

.sev.on.sev-bajo {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.sev.on.sev-medio {
  border-color: #c99a2e;
  background: #f5e9c4;
  color: #87661a;
}

.sev.on.sev-alto {
  border-color: var(--color-danger);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.aviso {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: 12.5px;
  line-height: 1.45;
}

.check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.check input {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
}

@media (max-width: 560px) {
  .opciones {
    grid-template-columns: 1fr;
  }
}
</style>
