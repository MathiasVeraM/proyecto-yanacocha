<script setup lang="ts">
import BaseModal from './BaseModal.vue'

defineProps<{
  open: boolean
  title: string
  loading?: boolean
  error?: string
}>()

const emit = defineEmits<{ close: []; confirm: [] }>()
</script>

<template>
  <BaseModal :open="open" :title="title" width="420px" @close="emit('close')">
    <p class="confirm-text"><slot /></p>
    <p v-if="error" class="alert-error">{{ error }}</p>

    <template #footer>
      <button class="btn btn-secondary" @click="emit('close')">Cancelar</button>
      <button class="btn btn-danger" :disabled="loading" @click="emit('confirm')">
        {{ loading ? 'Eliminando…' : 'Eliminar' }}
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.confirm-text {
  line-height: 1.5;
}

.alert-error {
  margin-top: 12px;
}
</style>
