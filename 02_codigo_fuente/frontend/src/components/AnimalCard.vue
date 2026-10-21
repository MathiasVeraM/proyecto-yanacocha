<script setup lang="ts">
import AnimalFoto from './AnimalFoto.vue'
import { ESTADOS_ANIMAL, formatearFecha, iniciales, nombreClase } from '@/config/animales'
import type { Animal } from '@/types/animales'

defineProps<{ animal: Animal }>()
</script>

<template>
  <RouterLink :to="{ name: 'ficha-animal', params: { id: animal.id_animal } }" class="card">
    <AnimalFoto :url="animal.url_imagen" :nombre="animal.taxonomia.nombre_comun" class="foto">
      <span v-if="animal.estado_actual !== 'en_centro'" class="estado" :class="animal.estado_actual">
        {{ ESTADOS_ANIMAL[animal.estado_actual].label }}
      </span>
      <span class="codigo">{{ animal.codigo_animal }}</span>
    </AnimalFoto>

    <div class="cuerpo">
      <div class="titulo">
        <span class="avatar">{{ iniciales(animal.nombre ?? animal.taxonomia.nombre_comun) }}</span>
        <!-- Con nombre propio: "Yaku / Caimán de anteojos"; sin él: "Caimán de anteojos / Caiman crocodilus" -->
        <div>
          <strong>{{ animal.nombre ?? animal.taxonomia.nombre_comun }}</strong>
          <em>{{ animal.nombre ? animal.taxonomia.nombre_comun : animal.taxonomia.especie }}</em>
        </div>
      </div>

      <dl>
        <div>
          <dt>Clase</dt>
          <dd>{{ nombreClase(animal.taxonomia.clase) }}</dd>
        </div>
        <div>
          <dt>Recinto</dt>
          <dd class="mono">{{ animal.recinto.nombre_recinto }}</dd>
        </div>
        <div>
          <dt>Ingreso</dt>
          <dd>{{ formatearFecha(animal.fecha_ingreso) }}</dd>
        </div>
      </dl>
    </div>
  </RouterLink>
</template>

<style scoped>
.card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: box-shadow 0.15s, transform 0.15s;
}

.card:hover {
  box-shadow: var(--shadow-card);
  transform: translateY(-2px);
}

.foto {
  height: 160px;
}

.estado {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #fff;
  background: var(--color-text-muted);
}

.estado.en_tratamiento {
  background: var(--color-danger);
}

.estado.liberado {
  background: #2d6a9a;
}

.estado.trasladado {
  background: #4a538f;
}

.codigo {
  position: absolute;
  left: 10px;
  bottom: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(35, 40, 31, 0.55);
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 11px;
  color: #fff;
}

.cuerpo {
  padding: 16px 18px 18px;
}

.titulo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border);
}

.avatar {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
  font-size: 12px;
  font-weight: 700;
  color: #87661a;
}

.titulo strong {
  display: block;
  font-size: 16px;
  font-weight: 600;
}

.titulo em {
  font-size: 13px;
  color: var(--color-text-muted);
}

dl > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

dl > div:last-child {
  border-bottom: none;
}

dt {
  color: var(--color-text-muted);
}

dd {
  margin: 0;
  font-weight: 500;
  text-align: right;
}

.mono {
  font-family: ui-monospace, 'Cascadia Code', monospace;
}
</style>
