<script setup lang="ts">
import type { TipoActividad } from '@/types/actividades'

// Ícono de cada tipo: plato (alimentación), destello (enriquecimiento), diana (entrenamiento), gota (limpieza)
defineProps<{ tipo: TipoActividad }>()
</script>

<template>
  <svg class="icono-tipo" viewBox="0 0 24 24" aria-hidden="true">
    <template v-if="tipo === 'alimentacion'">
      <path d="M3.5 11h17a8.5 8.5 0 0 1-17 0Z" />
      <path d="M9 7.5c0-1.5 1-2 1-3.5M14 7.5c0-1.5 1-2 1-3.5" />
    </template>
    <template v-else-if="tipo === 'enriquecimiento'">
      <path d="M11 3.5l1.7 4.6 4.6 1.7-4.6 1.7L11 16.1l-1.7-4.6-4.6-1.7 4.6-1.7Z" />
      <path d="M18 14.5l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8Z" />
    </template>
    <template v-else-if="tipo === 'entrenamiento'">
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4.5" />
      <circle cx="12" cy="12" r="1" />
    </template>
    <path v-else d="M12 3.5c3 4 6 7 6 10.5a6 6 0 0 1-12 0c0-3.5 3-6.5 6-10.5Z" />
  </svg>
</template>

<style scoped>
.icono-tipo {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
