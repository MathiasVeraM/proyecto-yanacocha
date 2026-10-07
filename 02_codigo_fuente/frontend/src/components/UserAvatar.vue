<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ nombre: string; apellido?: string }>()

const iniciales = computed(() => {
  const partes = props.apellido ? [props.nombre, props.apellido] : props.nombre.split(/[\s.@_]+/)
  return partes
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]!.toUpperCase())
    .join('')
})
</script>

<template>
  <span class="avatar">{{ iniciales }}</span>
</template>

<style scoped>
.avatar {
  flex-shrink: 0;
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
}
</style>
