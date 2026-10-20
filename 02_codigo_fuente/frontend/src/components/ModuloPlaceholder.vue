<script setup lang="ts">
defineProps<{
  titulo: string
  descripcion?: string
}>()
</script>

<template>
  <section class="placeholder">
    <h1>{{ titulo }}</h1>
    <p>{{ descripcion ?? 'Esta pantalla estará disponible próximamente.' }}</p>
  </section>
</template>

<style scoped>
.placeholder {
  padding: 64px 24px;
  text-align: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

h1 {
  font-size: 18px;
  font-weight: 700;
}

p {
  margin-top: 6px;
  color: var(--color-text-muted);
}
</style>
