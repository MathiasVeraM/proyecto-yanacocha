<script lang="ts">
// Fotos ya descargadas en esta sesión. La url_imagen cambia (?v=...) cada vez que se sube una foto nueva,
// así que una misma url siempre es la misma imagen y se puede reutilizar entre el catálogo y la ficha
const cache = new Map<string, Promise<string>>()
</script>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { animalesApi } from '@/api/animales'
import { iniciales } from '@/config/animales'

const props = defineProps<{ url: string | null; nombre: string }>()

const src = ref<string | null>(null)

function obtener(url: string) {
  let promesa = cache.get(url)
  if (!promesa) {
    // La foto está detrás del gateway, que exige el token: no basta con ponerla en un <img>
    promesa = animalesApi.descargarImagen(url).then((blob) => URL.createObjectURL(blob))
    promesa.catch(() => cache.delete(url))
    cache.set(url, promesa)
  }
  return promesa
}

watch(
  () => props.url,
  async (url) => {
    src.value = null
    if (!url) return
    try {
      const objeto = await obtener(url)
      // Si mientras tanto cambió la foto, se ignora la respuesta vieja
      if (url === props.url) src.value = objeto
    } catch {
      // Sin foto se muestra el marcador con las iniciales
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="foto">
    <img v-if="src" :src="src" :alt="nombre" @error="src = null" />
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
