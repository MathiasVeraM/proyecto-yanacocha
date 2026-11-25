<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { diaCorto, diaLargo, deIso, lunesDe, nombreMes, sumarDias } from '@/config/actividades'
import ListaActividadesMovil from '../components/ListaActividadesMovil.vue'
import { useActividadesMovilStore } from '../stores/actividades'
import { useSincronizacionStore } from '../stores/sincronizacion'

const store = useActividadesMovilStore()
const sync = useSincronizacionStore()

// Vista diaria: se elige un día de la semana y se ven sus actividades
const fecha = ref(store.hoy)
const semana = computed(() => {
  const lunes = lunesDe(fecha.value)
  return Array.from({ length: 7 }, (_, i) => sumarDias(lunes, i))
})

const delDia = computed(() => store.delDia(fecha.value))
const hechas = computed(() => delDia.value.filter((a) => a.completada).length)

// Punto de cada día: verde si todo está hecho, ámbar si queda algo pendiente
function estadoDia(dia: string): 'ninguna' | 'pendiente' | 'completo' {
  const lista = store.delDia(dia)
  if (!lista.length) return 'ninguna'
  return lista.every((a) => a.completada) ? 'completo' : 'pendiente'
}

const mesAnio = computed(() => {
  const mes = nombreMes(fecha.value)
  return `${mes.charAt(0).toUpperCase()}${mes.slice(1)} ${deIso(fecha.value).getFullYear()}`
})

const etiquetaDia = computed(() => {
  if (fecha.value === store.hoy) return `Hoy · ${diaLargo(fecha.value)}`
  if (fecha.value === sumarDias(store.hoy, -1)) return `Ayer · ${diaLargo(fecha.value)}`
  return diaLargo(fecha.value)
})

onMounted(() => void store.cargarSemana(fecha.value))
watch(fecha, (nueva) => void store.cargarSemana(nueva))

const mover = (dias: number) => (fecha.value = sumarDias(fecha.value, dias))
</script>

<template>
  <div class="vista">
    <header class="cabecera">
      <h1>Calendario</h1>
      <button v-if="fecha !== store.hoy" class="hoy" @click="fecha = store.hoy">Ir a hoy</button>
    </header>

    <section class="semana" aria-label="Semana">
      <div class="mes">
        <button class="flecha" aria-label="Semana anterior" @click="mover(-7)">‹</button>
        <strong>{{ mesAnio }}</strong>
        <button class="flecha" aria-label="Semana siguiente" @click="mover(7)">›</button>
      </div>
      <div class="dias">
        <button
          v-for="dia in semana"
          :key="dia"
          class="dia"
          :class="{ activo: dia === fecha, hoy: dia === store.hoy }"
          :aria-pressed="dia === fecha"
          @click="fecha = dia"
        >
          <small>{{ diaCorto(dia) }}</small>
          <strong>{{ Number(dia.slice(8)) }}</strong>
          <span class="punto" :class="estadoDia(dia)" />
        </button>
      </div>
    </section>

    <p v-if="!sync.hayRed" class="aviso">Sin conexión · se muestra lo que se guardó en el teléfono.</p>

    <section>
      <h2>
        {{ etiquetaDia }}
        <span v-if="delDia.length">{{ hechas }}/{{ delDia.length }} hechas</span>
      </h2>

      <ListaActividadesMovil v-if="delDia.length" :actividades="delDia" />
      <p v-else-if="store.cargando" class="vacio">Cargando…</p>
      <p v-else class="vacio">No hay actividades este día.</p>
    </section>
  </div>
</template>

<style scoped>
.vista {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

h1 {
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 600;
}

.hoy {
  min-height: 44px;
  padding: 0 16px;
  border: 1px solid var(--color-primary);
  border-radius: 999px;
  background: transparent;
  color: var(--color-primary);
  font-weight: 600;
}

.semana {
  padding: 12px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
}

.mes {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.flecha {
  width: 48px;
  height: 44px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
  font-size: 24px;
  line-height: 1;
}

.dias {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.dia {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-height: 66px;
  padding: 8px 0 6px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
}

.dia small {
  font-size: 11px;
  text-transform: capitalize;
  color: var(--color-text-muted);
}

.dia strong {
  font-size: 17px;
}

.dia.hoy strong {
  color: var(--color-primary);
}

.dia.activo {
  background: var(--color-primary);
}

.dia.activo small,
.dia.activo strong {
  color: #fff;
}

.punto {
  width: 6px;
  height: 6px;
  margin-top: 2px;
  border-radius: 50%;
  background: transparent;
}

.punto.pendiente {
  background: #d9a233;
}

.punto.completo {
  background: var(--color-primary);
}

.dia.activo .punto.completo,
.dia.activo .punto.pendiente {
  background: #fff;
}

h2 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 15px;
  color: var(--color-text-muted);
}

h2 span {
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--color-border);
  font-size: 12px;
}

.aviso {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: #f5e9c4;
  color: #87661a;
  font-size: 13px;
}

.vacio {
  padding: 36px 16px;
  text-align: center;
  color: var(--color-text-muted);
}
</style>
