<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseModal from './BaseModal.vue'
import { animalesApi } from '@/api/animales'
import { ApiError } from '@/api/http'
import type { Animal, EstadoAnimal } from '@/types/animales'

const props = defineProps<{
  open: boolean
  animal: Animal | null
}>()

const emit = defineEmits<{ close: []; saved: [animal: Animal] }>()

// La salida no borra al animal (HU-02): solo cambia su estado y conserva toda su ficha
const RAZONES: { estado: EstadoAnimal; label: string; detalle: string }[] = [
  { estado: 'fallecido', label: 'Deceso', detalle: 'El ejemplar falleció en el centro.' },
  { estado: 'trasladado', label: 'Traslado', detalle: 'El ejemplar se trasladó a otra institución.' },
  { estado: 'liberado', label: 'Liberación', detalle: 'El ejemplar fue reintroducido a su hábitat.' },
]

const razon = ref<EstadoAnimal | null>(null)
const error = ref('')
const guardando = ref(false)

watch(
  () => props.open,
  (abierto) => {
    if (!abierto) return
    razon.value = null
    error.value = ''
  },
)

async function confirmar() {
  if (!props.animal || !razon.value) return
  error.value = ''
  guardando.value = true
  try {
    emit('saved', await animalesApi.actualizar(props.animal.id_animal, { estado_actual: razon.value }))
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo registrar la salida'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    title="Registrar salida del ejemplar"
    :subtitle="animal ? `${animal.codigo_animal} · ${animal.taxonomia.nombre_comun}` : ''"
    width="520px"
    @close="emit('close')"
  >
    <p class="etiqueta">Razón de salida</p>
    <div class="razones">
      <button
        v-for="r in RAZONES"
        :key="r.estado"
        type="button"
        class="razon"
        :class="{ activa: razon === r.estado }"
        @click="razon = r.estado"
      >
        {{ r.label }}
      </button>
    </div>

    <p class="detalle">
      <template v-if="razon">
        {{ RAZONES.find((r) => r.estado === razon)?.detalle }}
        La ficha y su historial se conservan; el ejemplar dejará de figurar como presente en el centro.
      </template>
      <template v-else>Elige el motivo de la salida.</template>
    </p>

    <p v-if="error" class="alert-error">{{ error }}</p>

    <template #footer>
      <button type="button" class="btn btn-secondary" @click="emit('close')">Cancelar</button>
      <button type="button" class="btn btn-danger" :disabled="!razon || guardando" @click="confirmar">
        {{ guardando ? 'Registrando…' : 'Confirmar salida' }}
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.etiqueta {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.razones {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 10px;
}

.razon {
  padding: 11px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-weight: 500;
}

.razon:hover {
  background: var(--color-surface-alt);
}

.razon.activa {
  border-color: var(--color-danger);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.detalle {
  margin-top: 14px;
  padding: 14px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.5;
  text-align: center;
  color: var(--color-text-muted);
}

.alert-error {
  margin-top: 12px;
}
</style>
