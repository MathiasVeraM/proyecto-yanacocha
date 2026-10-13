<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'

const props = defineProps<{
  open: boolean
  title: string
  subtitle?: string
  width?: string
}>()

const emit = defineEmits<{ close: [] }>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

watch(
  () => props.open,
  (abierto) => {
    if (abierto) window.addEventListener('keydown', onKeydown)
    else window.removeEventListener('keydown', onKeydown)
  },
)

onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="overlay" @mousedown.self="emit('close')">
        <div class="modal" :style="{ maxWidth: width ?? '480px' }" role="dialog" aria-modal="true">
          <header class="modal-header">
            <div>
              <h2>{{ title }}</h2>
              <p v-if="subtitle">{{ subtitle }}</p>
            </div>
            <button class="close" aria-label="Cerrar" @click="emit('close')">×</button>
          </header>

          <div class="modal-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(35, 40, 31, 0.45);
}

.modal {
  width: 100%;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 22px 24px 0;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.modal-header p {
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.close {
  border: none;
  background: none;
  font-size: 22px;
  line-height: 1;
  color: var(--color-text-muted);
}

.modal-body {
  padding: 20px 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0 24px 22px;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.15s;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
