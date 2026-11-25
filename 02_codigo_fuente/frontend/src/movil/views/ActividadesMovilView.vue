<script setup lang="ts">
import { computed, ref } from 'vue'
import { diaLargo } from '@/config/actividades'
import { estaAtrasada } from '@/config/actividades'
import type { Actividad, CategoriaObservacion, SeveridadObservacion } from '@/types/actividades'
import HojaActividad from '../components/HojaActividad.vue'
import type { ModoHoja } from '../components/HojaActividad.vue'
import TarjetaActividad from '../components/TarjetaActividad.vue'
import { ahoraCentro } from '../offline/tiempo'
import { useActividadesMovilStore } from '../stores/actividades'
import { useSincronizacionStore } from '../stores/sincronizacion'

const store = useActividadesMovilStore()
const sync = useSincronizacionStore()

const filtro = ref<'pendientes' | 'hechas'>('pendientes')
const seleccion = ref<{ id: number; modo: ModoHoja } | null>(null)
const mensaje = ref('')
let temporizadorMensaje: ReturnType<typeof setTimeout> | undefined

const hoy = computed(() => store.hoy)
const hora = computed(() => ahoraCentro().hora)

const delDia = computed(() => store.actividades.filter((a) => a.fecha_programada === hoy.value))
const atrasadas = computed(() => store.actividades.filter((a) => a.fecha_programada < hoy.value && !a.completada))
const hechasHoy = computed(() => delDia.value.filter((a) => a.completada))
const pendientesHoy = computed(() => delDia.value.filter((a) => !a.completada))

// Lo pendiente: primero lo atrasado, luego lo de hoy por hora
const visibles = computed<Actividad[]>(() =>
  filtro.value === 'pendientes' ? [...atrasadas.value, ...pendientesHoy.value] : hechasHoy.value,
)
const progreso = computed(() =>
  delDia.value.length ? Math.round((hechasHoy.value.length / delDia.value.length) * 100) : 0,
)

const actividadSeleccionada = computed(() =>
  seleccion.value ? (store.actividades.find((a) => a.id_actividad === seleccion.value!.id) ?? null) : null,
)

function abrir(actividad: Actividad, modo: ModoHoja) {
  seleccion.value = { id: actividad.id_actividad, modo }
}

function avisar(texto: string) {
  mensaje.value = texto
  clearTimeout(temporizadorMensaje)
  temporizadorMensaje = setTimeout(() => (mensaje.value = ''), 3500)
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
</script>

<template>
  <div class="vista">
    <header class="encabezado">
      <p class="dia">{{ diaLargo(hoy) }}</p>
      <h1>Mis actividades</h1>
      <div class="progreso" role="progressbar" :aria-valuenow="progreso" aria-valuemin="0" aria-valuemax="100">
        <div class="barra" :style="{ width: `${progreso}%` }" />
      </div>
      <p class="cuenta">{{ hechasHoy.length }} de {{ delDia.length }} hechas hoy</p>
    </header>

    <div class="filtros" role="tablist">
      <button class="m-chip" role="tab" :aria-pressed="filtro === 'pendientes'" @click="filtro = 'pendientes'">
        Pendientes ({{ atrasadas.length + pendientesHoy.length }})
      </button>
      <button class="m-chip" role="tab" :aria-pressed="filtro === 'hechas'" @click="filtro = 'hechas'">
        Hechas ({{ hechasHoy.length }})
      </button>
    </div>

    <p v-if="!sync.hayRed && store.actualizado" class="aviso">
      Sin conexión · mostrando lo guardado el {{ store.actualizado.slice(8, 10) }}/{{ store.actualizado.slice(5, 7) }}
      a las {{ store.actualizado.slice(11, 16) }}
    </p>

    <ul v-if="visibles.length" class="lista">
      <li v-for="actividad in visibles" :key="actividad.id_actividad">
        <TarjetaActividad
          :actividad="actividad"
          :describir="store.describir"
          :atrasada="actividad.fecha_programada < hoy || estaAtrasada(actividad, hoy, hora)"
          :pendiente-envio="sync.completadasPendientes.has(actividad.id_actividad)"
          :observaciones-pendientes="sync.observacionesPorActividad.get(actividad.id_actividad) ?? 0"
          @abrir="abrir(actividad, 'detalle')"
          @completar="abrir(actividad, 'completar')"
          @observar="abrir(actividad, 'observar')"
        />
      </li>
    </ul>

    <p v-else-if="store.cargando && !store.actividades.length" class="vacio">Cargando actividades…</p>
    <p v-else-if="filtro === 'pendientes'" class="vacio">
      {{ delDia.length ? '¡Todo al día! No tienes actividades pendientes.' : 'No hay actividades para hoy.' }}
    </p>
    <p v-else class="vacio">Todavía no has marcado actividades como hechas hoy.</p>

    <HojaActividad
      v-if="actividadSeleccionada && seleccion"
      :actividad="actividadSeleccionada"
      :modo="seleccion.modo"
      :describir="store.describir"
      :pendiente-envio="sync.completadasPendientes.has(actividadSeleccionada.id_actividad)"
      @cerrar="seleccion = null"
      @cambiar-modo="seleccion.modo = $event"
      @hecha="marcarHecha"
      @observacion="guardarObservacion"
    />

    <p v-if="mensaje" class="toast" role="status">{{ mensaje }}</p>
  </div>
</template>

<style scoped>
.vista {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
}

.dia {
  font-size: 13px;
  color: var(--color-text-muted);
}

h1 {
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 600;
  margin-bottom: 10px;
}

.progreso {
  height: 8px;
  border-radius: 4px;
  background: var(--color-border);
  overflow: hidden;
}

.barra {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s;
}

.cuenta {
  margin-top: 6px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.filtros {
  display: flex;
  gap: 8px;
}

.aviso {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: #f5e9c4;
  color: #87661a;
  font-size: 13px;
}

.lista {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.vacio {
  padding: 40px 16px;
  text-align: center;
  color: var(--color-text-muted);
}

.toast {
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: calc(80px + env(safe-area-inset-bottom));
  z-index: 60;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: var(--color-dark);
  color: #fff;
  font-size: 14px;
  text-align: center;
}
</style>
