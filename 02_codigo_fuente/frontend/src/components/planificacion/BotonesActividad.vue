<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

// Los dos botones rápidos de una actividad: marcarla como hecha y agregar una observación.
// Solo los ven los roles que pueden completar actividades (Manejo de Animales y Voluntarios)
const auth = useAuthStore()
defineProps<{
  hecha: boolean
  observaciones: number
  nombre: string
  ocupado?: boolean
  compacto?: boolean
  sinCheck?: boolean
}>()
const emit = defineEmits<{ completar: []; observar: [] }>()
</script>

<template>
  <span v-if="auth.permisos.completarActividades" class="botones" :class="{ compacto }">
    <button
      v-if="!sinCheck"
      type="button"
      class="mini ok"
      :class="{ on: hecha }"
      :disabled="hecha || ocupado"
      :title="hecha ? 'Hecha' : 'Marcar como hecha'"
      :aria-label="hecha ? `${nombre}: hecha` : `Marcar como hecha: ${nombre}`"
      @click.stop="emit('completar')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
    </button>
    <button
      type="button"
      class="mini"
      title="Agregar observación"
      :aria-label="`Agregar observación: ${nombre}`"
      @click.stop="emit('observar')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16Z" /><path d="m13.5 6.5 4 4" /></svg>
      <b v-if="observaciones">{{ observaciones }}</b>
    </button>
  </span>
</template>

<style scoped>
.botones {
  display: inline-flex;
  gap: 4px;
}

.mini {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-width: 26px;
  height: 26px;
  padding: 0 5px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-muted);
  cursor: pointer;
}

.mini svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.mini b {
  font-size: 10.5px;
  font-variant-numeric: tabular-nums;
}

.mini:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.mini:disabled {
  opacity: 1;
  cursor: default;
}

.mini.ok.on {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.compacto .mini {
  min-width: 20px;
  height: 20px;
  padding: 0 3px;
  border-radius: 5px;
}

.compacto .mini svg {
  width: 12px;
  height: 12px;
}
</style>
