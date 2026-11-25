<script setup lang="ts">
import { computed } from 'vue'
import { diaLargo } from '@/config/actividades'
import { useAuthStore } from '@/stores/auth'
import ListaActividadesMovil from '../components/ListaActividadesMovil.vue'
import { useActividadesMovilStore } from '../stores/actividades'
import { useSincronizacionStore } from '../stores/sincronizacion'

const auth = useAuthStore()
const store = useActividadesMovilStore()
const sync = useSincronizacionStore()

// Esta pantalla solo muestra el día de hoy; los días anteriores están en "Calendario"
const delDia = computed(() => store.delDia(store.hoy))
const pendientes = computed(() => delDia.value.filter((a) => !a.completada))
const hechas = computed(() => delDia.value.filter((a) => a.completada))
const porcentaje = computed(() =>
  delDia.value.length ? Math.round((hechas.value.length / delDia.value.length) * 100) : 0,
)

// Anillo de avance (circunferencia de un círculo de radio 34)
const CIRCUNFERENCIA = 2 * Math.PI * 34
const trazo = computed(() => CIRCUNFERENCIA * (1 - porcentaje.value / 100))

const registra = computed(() => auth.permisos.completarActividades)
</script>

<template>
  <div class="vista">
    <section class="resumen">
      <div class="anillo" aria-hidden="true">
        <svg viewBox="0 0 80 80">
          <circle class="fondo" cx="40" cy="40" r="34" />
          <circle
            class="avance"
            cx="40"
            cy="40"
            r="34"
            :stroke-dasharray="CIRCUNFERENCIA"
            :stroke-dashoffset="trazo"
          />
        </svg>
        <span>{{ porcentaje }}%</span>
      </div>
      <div>
        <p class="dia">{{ diaLargo(store.hoy) }}</p>
        <h1>Hoy</h1>
        <p class="cuenta">
          <template v-if="delDia.length">{{ hechas.length }} de {{ delDia.length }} actividades hechas</template>
          <template v-else>Sin actividades programadas</template>
        </p>
      </div>
    </section>

    <p v-if="!sync.hayRed && store.actualizado" class="aviso">
      Sin conexión · mostrando lo guardado el {{ store.actualizado.slice(8, 10) }}/{{ store.actualizado.slice(5, 7) }}
      a las {{ store.actualizado.slice(11, 16) }}
    </p>
    <p v-if="!registra" class="aviso info">Tu rol puede consultar las actividades, pero no marcarlas ni observarlas.</p>

    <p v-if="store.cargando && !store.actividades.length" class="vacio">Cargando actividades…</p>
    <p v-else-if="!delDia.length" class="vacio">No hay actividades para hoy.</p>

    <template v-else>
      <section v-if="pendientes.length">
        <h2>Por hacer <span>{{ pendientes.length }}</span></h2>
        <ListaActividadesMovil :actividades="pendientes" />
      </section>
      <p v-else class="vacio listo">¡Todo al día! Completaste las actividades de hoy.</p>

      <section v-if="hechas.length">
        <h2>Hechas <span>{{ hechas.length }}</span></h2>
        <ListaActividadesMovil :actividades="hechas" />
      </section>
    </template>
  </div>
</template>

<style scoped>
.vista {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.resumen {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #2e6b34, #1d3a1c);
  color: #fff;
}

.anillo {
  position: relative;
  width: 76px;
  height: 76px;
  flex-shrink: 0;
}

.anillo svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.anillo circle {
  fill: none;
  stroke-width: 7;
}

.fondo {
  stroke: rgba(255, 255, 255, 0.22);
}

.avance {
  stroke: #fff;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.4s;
}

.anillo span {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 16px;
}

.dia {
  font-size: 13px;
  opacity: 0.8;
}

h1 {
  font-family: var(--font-serif);
  font-size: 30px;
  font-weight: 600;
  line-height: 1.1;
}

.cuenta {
  margin-top: 4px;
  font-size: 14px;
  opacity: 0.9;
}

h2 {
  display: flex;
  align-items: center;
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

.aviso.info {
  background: #dde9f3;
  color: #2d6a9a;
}

.vacio {
  padding: 36px 16px;
  text-align: center;
  color: var(--color-text-muted);
}

.vacio.listo {
  padding: 20px 16px;
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
}
</style>
