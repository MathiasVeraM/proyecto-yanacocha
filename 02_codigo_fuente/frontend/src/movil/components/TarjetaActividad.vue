<script setup lang="ts">
import IconoTipo from '@/components/planificacion/IconoTipo.vue'
import { TIPO_LABEL, diaCorto, horaCorta } from '@/config/actividades'
import type { describirActividades } from '@/config/actividades'
import type { Actividad } from '@/types/actividades'

defineProps<{
  actividad: Actividad
  describir: ReturnType<typeof describirActividades>
  atrasada: boolean
  // Se marcó en el teléfono y todavía no llegó al servidor
  pendienteEnvio: boolean
  observacionesPendientes: number
}>()
const emit = defineEmits<{ abrir: []; completar: []; observar: [] }>()
</script>

<template>
  <article class="tarjeta" :class="[`m-tipo-${actividad.tipo_actividad}`, { hecha: actividad.completada }]">
    <button class="cuerpo" type="button" @click="emit('abrir')">
      <span class="icono"><IconoTipo :tipo="actividad.tipo_actividad" /></span>
      <span class="texto">
        <span class="meta">
          {{ TIPO_LABEL[actividad.tipo_actividad] }}
          <template v-if="horaCorta(actividad)"> · {{ horaCorta(actividad) }}</template>
          <template v-if="atrasada"> · {{ diaCorto(actividad.fecha_programada) }} {{ actividad.fecha_programada.slice(8) }}</template>
        </span>
        <strong>{{ describir.titulo(actividad) }}</strong>
        <span class="detalle">{{ describir.detalle(actividad) }}</span>
        <span v-if="atrasada || pendienteEnvio || observacionesPendientes" class="etiquetas">
          <span v-if="atrasada" class="etiqueta atrasada">Atrasada</span>
          <span v-if="pendienteEnvio" class="etiqueta envio">Pendiente de envío</span>
          <span v-if="observacionesPendientes" class="etiqueta envio">
            {{ observacionesPendientes }} observación{{ observacionesPendientes > 1 ? 'es' : '' }} sin enviar
          </span>
        </span>
      </span>
    </button>

    <div class="acciones">
      <button
        v-if="!actividad.completada"
        class="redondo hecho"
        type="button"
        aria-label="Marcar como hecha"
        @click="emit('completar')"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
      </button>
      <span v-else class="redondo listo" aria-label="Hecha">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
      </span>
      <button class="redondo" type="button" aria-label="Agregar observación" @click="emit('observar')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 5.5h16v10H9l-5 4Z" />
        </svg>
      </button>
    </div>
  </article>
</template>

<style scoped>
.tarjeta {
  display: flex;
  align-items: stretch;
  gap: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 5px solid var(--m-tipo);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.tarjeta.hecha {
  opacity: 0.72;
}

.cuerpo {
  flex: 1;
  min-width: 0;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 8px 14px 12px;
  border: none;
  background: transparent;
  text-align: left;
}

.icono {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--m-tipo-soft);
  color: var(--m-tipo);
}

.icono :deep(svg) {
  width: 20px;
  height: 20px;
}

.texto {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.meta {
  font-size: 12px;
  font-weight: 600;
  color: var(--m-tipo);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

strong {
  font-size: 16px;
}

.detalle {
  font-size: 14px;
  color: var(--color-text-muted);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.etiquetas {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.etiqueta {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.atrasada {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.envio {
  background: #f5e9c4;
  color: #87661a;
}

.acciones {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  padding: 6px 8px 6px 0;
}

.redondo {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border: 1px solid var(--color-border-strong);
  border-radius: 50%;
  background: var(--color-surface-alt);
  color: var(--color-text-muted);
}

.redondo svg {
  width: 22px;
  height: 22px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.redondo.hecho {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.redondo.listo {
  background: var(--color-primary-soft);
  border-color: transparent;
  color: var(--color-primary);
}
</style>
