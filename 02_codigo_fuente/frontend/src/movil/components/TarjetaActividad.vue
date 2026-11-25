<script setup lang="ts">
import IconoTipo from '@/components/planificacion/IconoTipo.vue'
import { TIPO_LABEL, duracionMinutos, horaCorta, textoDuracion } from '@/config/actividades'
import type { describirActividades } from '@/config/actividades'
import type { Actividad } from '@/types/actividades'

defineProps<{
  actividad: Actividad
  describir: ReturnType<typeof describirActividades>
  atrasada: boolean
  // Se marcó en el teléfono y todavía no llegó al servidor
  pendienteEnvio: boolean
  observacionesPendientes: number
  // Según el rol (y el día de la actividad); sin permiso los botones no se muestran
  puedeCompletar: boolean
  puedeObservar: boolean
}>()
const emit = defineEmits<{ abrir: []; completar: []; observar: [] }>()
</script>

<template>
  <article class="tarjeta" :class="[`m-tipo-${actividad.tipo_actividad}`, { hecha: actividad.completada }]">
    <button class="principal" type="button" @click="emit('abrir')">
      <span class="hora">
        <strong>{{ horaCorta(actividad) || '—' }}</strong>
        <small v-if="duracionMinutos(actividad)">{{ textoDuracion(duracionMinutos(actividad)) }}</small>
      </span>

      <span class="texto">
        <span class="tipo">
          <IconoTipo :tipo="actividad.tipo_actividad" />
          {{ TIPO_LABEL[actividad.tipo_actividad] }}
        </span>
        <strong class="titulo">{{ describir.titulo(actividad) }}</strong>
        <span class="detalle">{{ describir.detalle(actividad) }}</span>
        <span v-if="actividad.completada || atrasada || pendienteEnvio || observacionesPendientes" class="etiquetas">
          <span v-if="actividad.completada" class="etiqueta ok">✓ Hecha</span>
          <span v-if="atrasada" class="etiqueta atrasada">Atrasada</span>
          <span v-if="pendienteEnvio" class="etiqueta envio">Sin enviar</span>
          <span v-if="observacionesPendientes" class="etiqueta envio">
            {{ observacionesPendientes }} obs. sin enviar
          </span>
        </span>
      </span>
    </button>

    <div v-if="puedeObservar || (puedeCompletar && !actividad.completada)" class="acciones">
      <button
        v-if="puedeCompletar && !actividad.completada"
        class="redondo hecho"
        type="button"
        aria-label="Marcar como hecha"
        @click="emit('completar')"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
      </button>
      <button
        v-if="puedeObservar"
        class="redondo"
        type="button"
        aria-label="Agregar observación"
        @click="emit('observar')"
      >
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
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.tarjeta.hecha {
  background: var(--color-surface-alt);
  box-shadow: none;
}

.principal {
  flex: 1;
  min-width: 0;
  display: flex;
  gap: 12px;
  padding: 14px 8px 14px 14px;
  border: none;
  background: transparent;
  text-align: left;
}

.hora {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 52px;
  padding-right: 12px;
  border-right: 3px solid var(--m-tipo);
}

.hora strong {
  font-size: 18px;
  font-variant-numeric: tabular-nums;
}

.hora small {
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: center;
}

.texto {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.tipo {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  width: fit-content;
  padding: 2px 9px 2px 7px;
  border-radius: 999px;
  background: var(--m-tipo-soft);
  color: var(--m-tipo);
  font-size: 12px;
  font-weight: 700;
}

.tipo :deep(svg) {
  width: 14px;
  height: 14px;
}

.titulo {
  font-size: 16px;
  line-height: 1.25;
}

.hecha .titulo {
  color: var(--color-text-muted);
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
  margin-top: 4px;
}

.etiqueta {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
}

.ok {
  background: var(--color-primary-soft);
  color: var(--color-primary);
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
  gap: 8px;
  padding: 8px 12px 8px 4px;
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
</style>
