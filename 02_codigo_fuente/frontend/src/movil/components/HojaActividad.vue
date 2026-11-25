<script setup lang="ts">
import { computed, ref } from 'vue'
import IconoTipo from '@/components/planificacion/IconoTipo.vue'
import { TIPO_LABEL, diaLargo, horaCorta, horaFin, textoDuracion, duracionMinutos } from '@/config/actividades'
import type { describirActividades } from '@/config/actividades'
import type { Actividad, CategoriaObservacion, SeveridadObservacion } from '@/types/actividades'
import FormObservacionMovil from './FormObservacionMovil.vue'
import HojaInferior from './HojaInferior.vue'

export type ModoHoja = 'detalle' | 'completar' | 'observar'

const props = defineProps<{
  actividad: Actividad
  modo: ModoHoja
  describir: ReturnType<typeof describirActividades>
  pendienteEnvio: boolean
}>()
const emit = defineEmits<{
  cerrar: []
  cambiarModo: [modo: ModoHoja]
  hecha: [observaciones: string]
  observacion: [datos: { categoria: CategoriaObservacion; severidad: SeveridadObservacion; detalle: string }]
}>()

const nota = ref('')
const titulo = computed(() =>
  props.modo === 'observar' ? 'Nueva observación' : props.modo === 'completar' ? 'Marcar como hecha' : TIPO_LABEL[props.actividad.tipo_actividad],
)
const hora = computed(() => {
  const inicio = horaCorta(props.actividad)
  return inicio ? `${inicio} – ${horaFin(props.actividad)} (${textoDuracion(duracionMinutos(props.actividad))})` : 'Sin hora'
})
</script>

<template>
  <HojaInferior :titulo="titulo" @cerrar="emit('cerrar')">
    <div class="resumen" :class="`m-tipo-${actividad.tipo_actividad}`">
      <span class="icono"><IconoTipo :tipo="actividad.tipo_actividad" /></span>
      <div>
        <strong>{{ describir.titulo(actividad) }}</strong>
        <p>{{ describir.detalle(actividad) }}</p>
      </div>
    </div>

    <!-- Detalle -->
    <template v-if="modo === 'detalle'">
      <dl class="datos">
        <div><dt>Día</dt><dd>{{ diaLargo(actividad.fecha_programada) }}</dd></div>
        <div><dt>Horario</dt><dd>{{ hora }}</dd></div>
        <div><dt>Lugar</dt><dd>{{ describir.lugar(actividad) }}</dd></div>
        <div v-if="actividad.observaciones"><dt>Indicaciones</dt><dd>{{ actividad.observaciones }}</dd></div>
        <div v-if="actividad.completada">
          <dt>Estado</dt>
          <dd>Hecha{{ pendienteEnvio ? ' · pendiente de envío' : '' }}</dd>
        </div>
      </dl>
      <div class="acciones">
        <button v-if="!actividad.completada" class="m-btn m-btn-primario" @click="emit('cambiarModo', 'completar')">
          Marcar como hecha
        </button>
        <button class="m-btn m-btn-secundario" @click="emit('cambiarModo', 'observar')">Agregar observación</button>
      </div>
    </template>

    <!-- Confirmar cumplimiento: la fecha y hora salen del reloj del teléfono -->
    <template v-else-if="modo === 'completar'">
      <p class="nota-hora">Se registrará la fecha y hora actuales de este dispositivo.</p>
      <label class="etiqueta" for="nota">Comentario (opcional)</label>
      <textarea id="nota" v-model="nota" class="m-input" rows="3" placeholder="Algo que quieras dejar anotado" />
      <div class="acciones">
        <button class="m-btn m-btn-primario" @click="emit('hecha', nota)">Confirmar como hecha</button>
      </div>
    </template>

    <FormObservacionMovil v-else :actividad="actividad" @guardar="emit('observacion', $event)" />
  </HojaInferior>
</template>

<style scoped>
.resumen {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  margin-bottom: 14px;
  background: var(--m-tipo-soft);
  border-radius: var(--radius-md);
  color: var(--m-tipo);
}

.resumen p {
  color: var(--color-text);
  font-size: 14px;
  margin-top: 2px;
}

.icono {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--color-surface);
}

.icono :deep(svg) {
  width: 20px;
  height: 20px;
}

.datos {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.datos div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-border);
}

dt {
  color: var(--color-text-muted);
  font-size: 14px;
}

dd {
  text-align: right;
  font-weight: 500;
}

.acciones {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 18px;
}

.nota-hora {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 12px;
}

.etiqueta {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
}

textarea {
  resize: none;
}
</style>
