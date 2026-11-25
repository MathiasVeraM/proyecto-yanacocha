<script setup lang="ts">
import { computed, ref } from 'vue'
import { estaAtrasada } from '@/config/actividades'
import { useAuthStore } from '@/stores/auth'
import type { Actividad, CategoriaObservacion, SeveridadObservacion } from '@/types/actividades'
import { ahoraCentro } from '../offline/tiempo'
import { useActividadesMovilStore } from '../stores/actividades'
import { useSincronizacionStore } from '../stores/sincronizacion'
import HojaActividad from './HojaActividad.vue'
import type { ModoHoja } from './HojaActividad.vue'
import TarjetaActividad from './TarjetaActividad.vue'

// Lista de tarjetas con la hoja de detalle, completar y observar. La usan "Hoy" y "Calendario".
defineProps<{ actividades: Actividad[] }>()

const auth = useAuthStore()
const store = useActividadesMovilStore()
const sync = useSincronizacionStore()

const seleccion = ref<{ id: number; modo: ModoHoja } | null>(null)
const mensaje = ref('')
let temporizador: ReturnType<typeof setTimeout> | undefined

// Mismos permisos que la web: solo Manejo de Animales y Voluntarios completan y observan.
// Además, el servidor solo acepta completar actividades de hoy o de días anteriores.
const puedeObservar = computed(() => auth.permisos.completarActividades)
const puedeCompletar = (a: Actividad) => auth.permisos.completarActividades && a.fecha_programada <= store.hoy

const actividadSeleccionada = computed(() =>
  seleccion.value ? (store.actividades.find((a) => a.id_actividad === seleccion.value!.id) ?? null) : null,
)

function avisar(texto: string) {
  mensaje.value = texto
  clearTimeout(temporizador)
  temporizador = setTimeout(() => (mensaje.value = ''), 3500)
}

const textoGuardado = () =>
  sync.hayRed ? 'Guardado. Enviando…' : 'Guardado en el teléfono. Se enviará al volver la señal.'

async function marcarHecha(observaciones: string) {
  if (!actividadSeleccionada.value) return
  await sync.marcarHecha(actividadSeleccionada.value.id_actividad, observaciones)
  seleccion.value = null
  avisar(textoGuardado())
}

async function guardarObservacion(datos: {
  categoria: CategoriaObservacion
  severidad: SeveridadObservacion
  detalle: string
}) {
  if (!actividadSeleccionada.value) return
  await sync.observar(actividadSeleccionada.value.id_actividad, datos)
  seleccion.value = null
  avisar(textoGuardado())
}

const atrasada = (a: Actividad) =>
  a.fecha_programada < store.hoy || estaAtrasada(a, store.hoy, ahoraCentro().hora)
</script>

<template>
  <ul class="lista">
    <li v-for="actividad in actividades" :key="actividad.id_actividad">
      <TarjetaActividad
        :actividad="actividad"
        :describir="store.describir"
        :atrasada="!actividad.completada && atrasada(actividad)"
        :pendiente-envio="sync.completadasPendientes.has(actividad.id_actividad)"
        :observaciones-pendientes="sync.observacionesPorActividad.get(actividad.id_actividad) ?? 0"
        :puede-completar="puedeCompletar(actividad)"
        :puede-observar="puedeObservar"
        @abrir="seleccion = { id: actividad.id_actividad, modo: 'detalle' }"
        @completar="seleccion = { id: actividad.id_actividad, modo: 'completar' }"
        @observar="seleccion = { id: actividad.id_actividad, modo: 'observar' }"
      />
    </li>
  </ul>

  <HojaActividad
    v-if="actividadSeleccionada && seleccion"
    :actividad="actividadSeleccionada"
    :modo="seleccion.modo"
    :describir="store.describir"
    :pendiente-envio="sync.completadasPendientes.has(actividadSeleccionada.id_actividad)"
    :puede-completar="puedeCompletar(actividadSeleccionada)"
    :puede-observar="puedeObservar"
    @cerrar="seleccion = null"
    @cambiar-modo="seleccion.modo = $event"
    @hecha="marcarHecha"
    @observacion="guardarObservacion"
  />

  <p v-if="mensaje" class="toast" role="status">{{ mensaje }}</p>
</template>

<style scoped>
.lista {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: calc(84px + env(safe-area-inset-bottom));
  z-index: 60;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: var(--color-dark);
  color: #fff;
  font-size: 14px;
  text-align: center;
}
</style>
