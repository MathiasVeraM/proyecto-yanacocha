<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { App } from '@capacitor/app'

// Panel que sube desde abajo: en el móvil reemplaza a los modales de la versión web porque se
// alcanza con el pulgar y deja ver el contexto detrás.
defineProps<{ titulo: string }>()
const emit = defineEmits<{ cerrar: [] }>()

// El botón "atrás" de Android cierra la hoja en vez de salir de la app
let escucha: { remove: () => Promise<void> } | null = null
onMounted(async () => {
  try {
    escucha = await App.addListener('backButton', () => emit('cerrar'))
  } catch {
    // En el navegador no existe el botón atrás de Android
  }
})
onBeforeUnmount(() => void escucha?.remove())
</script>

<template>
  <div class="velo" @click.self="emit('cerrar')">
    <section class="hoja" role="dialog" aria-modal="true" :aria-label="titulo">
      <div class="asa" aria-hidden="true" />
      <header class="cabecera">
        <h2>{{ titulo }}</h2>
        <button class="cerrar" type="button" aria-label="Cerrar" @click="emit('cerrar')">✕</button>
      </header>
      <div class="cuerpo">
        <slot />
      </div>
    </section>
  </div>
</template>

<style scoped>
.velo {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: flex-end;
  background: rgba(35, 40, 31, 0.5);
  animation: velo 0.18s ease-out;
}

.hoja {
  width: 100%;
  max-height: 92dvh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  box-shadow: 0 -10px 30px rgba(35, 40, 31, 0.2);
  padding-bottom: env(safe-area-inset-bottom);
  animation: subir 0.22s ease-out;
}

.asa {
  width: 40px;
  height: 4px;
  margin: 8px auto 0;
  border-radius: 2px;
  background: var(--color-border-strong);
}

.cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 16px 8px 20px;
}

h2 {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
}

.cerrar {
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 50%;
  background: transparent;
  font-size: 18px;
  color: var(--color-text-muted);
}

.cuerpo {
  overflow-y: auto;
  padding: 4px 20px 20px;
}

@keyframes subir {
  from { transform: translateY(40px); opacity: 0; }
  to { transform: none; opacity: 1; }
}

@keyframes velo {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
