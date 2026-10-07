<script setup lang="ts">
export type BadgeTone = 'green' | 'blue' | 'amber' | 'indigo' | 'gray'

defineProps<{ tone?: BadgeTone }>()
</script>

<template>
  <span class="badge" :class="tone ?? 'gray'"><slot /></span>
</template>

<style scoped>
.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.green {
  background: #e2ebd6;
  color: #2e6b34;
}

.blue {
  background: #dde9f3;
  color: #2d6a9a;
}

.amber {
  background: #f5e9c4;
  color: #87661a;
}

.indigo {
  background: #e3e6f3;
  color: #4a538f;
}

.gray {
  background: #ebe7da;
  color: #6b6a5c;
}
</style>
