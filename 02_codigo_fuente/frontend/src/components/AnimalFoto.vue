<script setup lang="ts">
import { ref, watch } from 'vue'
import { iniciales } from '@/config/animales'

const props = defineProps<{ url: string | null; nombre: string }>()

// Si la imagen no carga (URL rota), se muestra el marcador con las iniciales
const fallo = ref(false)
watch(
  () => props.url,
  () => (fallo.value = false),
)
</script>

<template>
  <div class="foto">
    <img v-if="url && !fallo" :src="url" :alt="nombre" loading="lazy" @error="fallo = true" />
    <span v-else class="marcador">{{ iniciales(nombre) }}</span>
    <slot />
  </div>
</template>

<style scoped>
.foto {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #cfdcc0, #a9bf94);
}

img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.marcador {
  display: grid;
  place-items: center;
  height: 100%;
  font-family: var(--font-serif);
  font-size: 34px;
  font-weight: 600;
  color: rgba(46, 107, 52, 0.55);
}
</style>
