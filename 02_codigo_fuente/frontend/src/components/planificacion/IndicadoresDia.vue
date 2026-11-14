<script setup lang="ts">
import { computed, ref } from 'vue'
import BotonesActividad from '@/components/planificacion/BotonesActividad.vue'
import IconoTipo from '@/components/planificacion/IconoTipo.vue'
import {
  TIPOS_ACTIVIDAD,
  TIPO_LABEL,
  describirActividades,
  estaAtrasada,
  horaCorta,
  horaFin,
  type ContextoActividades,
} from '@/config/actividades'
import type { Actividad, TipoActividad } from '@/types/actividades'

// Resumen del día por tipo de actividad. Reemplaza al Checklist y a Monitoreo de alimentación:
// cada tarjeta se despliega con lo que falta hacer y se puede completar desde aquí.
const props = defineProps<{
  fecha: string
  actividades: Actividad[]
  ctx: ContextoActividades
  hoy: string
  ahora: string
  obsPorActividad: Record<number, number>
  actualizandoId: number | null
}>()
const emit = defineEmits<{ completar: [a: Actividad]; observar: [a: Actividad]; abrir: [a: Actividad] }>()

const seleccion = ref<TipoActividad | null>(null)
const modo = ref<'pend' | 'todos'>('pend')

const d = computed(() => describirActividades(props.ctx))
const tarde = (a: Actividad) => estaAtrasada(a, props.hoy, props.ahora)
const delTipo = (tipo: TipoActividad) =>
  props.actividades
    .filter((a) => a.tipo_actividad === tipo)
    .sort((x, y) => horaCorta(x).localeCompare(horaCorta(y)))

const TEXTOS: Record<TipoActividad, { unidad: string; pendientes: string }> = {
  alimentacion: { unidad: 'alimentados', pendientes: 'Pendientes de alimentar' },
  enriquecimiento: { unidad: 'realizados', pendientes: 'Enriquecimientos pendientes' },
  entrenamiento: { unidad: 'realizados', pendientes: 'Entrenamientos pendientes' },
  limpieza: { unidad: 'recintos limpios', pendientes: 'Recintos por limpiar' },
  tratamiento: { unidad: 'dosis aplicadas', pendientes: 'Dosis de tratamiento pendientes' },
}

// Alimentación se cuenta por ejemplar: "alimentado" = se confirmaron TODAS sus tomas registradas ese día
const filasAlimentacion = computed(() => {
  const porAnimal = new Map<number, Actividad[]>()
  for (const t of delTipo('alimentacion')) {
    const id = t.id_animal ?? 0
    porAnimal.set(id, [...(porAnimal.get(id) ?? []), t])
  }
  return [...porAnimal].map(([id, tomas]) => {
    const pendientes = tomas.filter((t) => !t.completada)
    return {
      id,
      tomas,
      comio: tomas.every((t) => t.completada),
      tarde: tomas.some(tarde),
      siguiente: pendientes.find(tarde) ?? pendientes[0] ?? null,
    }
  })
})

const indicadores = computed(() =>
  TIPOS_ACTIVIDAD.map((tipo) => {
    const lista = delTipo(tipo)
    let hechos = lista.filter((a) => a.completada).length
    let total = lista.length
    if (tipo === 'alimentacion') {
      total = filasAlimentacion.value.length
      hechos = filasAlimentacion.value.filter((f) => f.comio).length
    }
    const proxima = props.fecha === props.hoy ? lista.find((a) => !a.completada && !tarde(a)) : undefined
    return {
      tipo,
      ...TEXTOS[tipo],
      hechos,
      total,
      atrasadas: lista.filter(tarde).length,
      proxima: proxima ? horaCorta(proxima) : '',
      pct: total ? Math.round((hechos / total) * 100) : 0,
    }
  }),
)

const actual = computed(() => indicadores.value.find((i) => i.tipo === seleccion.value) ?? null)
// Las tarjetas usan orden par (0, 2, 4…); el detalle toma el impar siguiente a su tarjeta
const ordenDetalle = computed(() => indicadores.value.findIndex((i) => i.tipo === seleccion.value) * 2 + 1)

const filas = computed(() => {
  if (seleccion.value === 'alimentacion') {
    const lista = modo.value === 'pend'
      ? filasAlimentacion.value.filter((f) => !f.comio || f.tarde)
      : filasAlimentacion.value
    return [...lista].sort(
      (a, b) =>
        Number(b.tarde) - Number(a.tarde) ||
        Number(a.comio) - Number(b.comio) ||
        (a.siguiente ? horaCorta(a.siguiente) : '99').localeCompare(b.siguiente ? horaCorta(b.siguiente) : '99'),
    )
  }
  return []
})
const actividadesFila = computed(() => {
  if (!seleccion.value || seleccion.value === 'alimentacion') return []
  const lista = delTipo(seleccion.value)
  return modo.value === 'pend' ? lista.filter((a) => !a.completada) : lista
})
const cantidadFilas = computed(() =>
  seleccion.value === 'alimentacion' ? filas.value.length : actividadesFila.value.length,
)

function alternar(tipo: TipoActividad) {
  seleccion.value = seleccion.value === tipo ? null : tipo
}

const iniciales = (texto: string) => texto.trim().slice(0, 2).toUpperCase()
</script>

<template>
  <section class="indicadores" aria-label="Resumen del día">

    <div class="grid">
      <button
        v-for="(ind, i) in indicadores"
        :key="ind.tipo"
        type="button"
        class="ind"
        :class="[`t-${ind.tipo}`, { sel: seleccion === ind.tipo }]"
        :style="{ order: i * 2 }"
        :aria-expanded="seleccion === ind.tipo"
        @click="alternar(ind.tipo)"
      >
        <span class="ico"><IconoTipo :tipo="ind.tipo" /></span>
        <span class="txt">
          <span class="tit">{{ TIPO_LABEL[ind.tipo] }}</span>
          <span class="big">{{ ind.hechos }}<small>/{{ ind.total }}</small> <em>{{ ind.unidad }}</em></span>
          <span class="pie">
            <span v-if="ind.atrasadas" class="tarde">{{ ind.atrasadas }} atrasada{{ ind.atrasadas > 1 ? 's' : '' }}</span>
            <span v-else-if="ind.total && ind.hechos === ind.total" class="aldia">Todo al día</span>
            <span v-else-if="!ind.total">Sin actividades</span>
            <span v-else>{{ ind.total - ind.hechos }} pendiente{{ ind.total - ind.hechos === 1 ? '' : 's' }}</span>
            <span v-if="ind.proxima"> · próxima {{ ind.proxima }}</span>
          </span>
        </span>
        <span class="ring" :style="{ '--p': ind.pct }"><span>{{ ind.pct }}%</span></span>
        <span class="caret" aria-hidden="true">{{ seleccion === ind.tipo ? '▴' : '▾' }}</span>
      </button>
      <!-- El detalle aparece justo debajo de la tarjeta a la que pertenece -->
      <div v-if="actual" class="detalle" :class="`t-${actual.tipo}`" :style="{ order: ordenDetalle }">
        <div class="det-h">
          <h3>
            {{ modo === 'pend' ? actual.pendientes : `${TIPO_LABEL[actual.tipo]} del día` }}
            <span class="cnt">{{ cantidadFilas }}</span>
          </h3>
          <span class="det-acc">
            <span class="seg" role="group" aria-label="Mostrar">
              <button type="button" :class="{ on: modo === 'pend' }" @click="modo = 'pend'">Pendientes</button>
              <button type="button" :class="{ on: modo === 'todos' }" @click="modo = 'todos'">Todos</button>
            </span>
            <button class="cerrar" type="button" aria-label="Cerrar detalle" @click="seleccion = null">×</button>
          </span>
        </div>

        <p v-if="!cantidadFilas" class="vacio">
          {{ actual.total ? 'No queda nada pendiente. Todo al día.' : 'No hay actividades de este tipo para este día.' }}
        </p>

        <ul v-else-if="actual.tipo === 'alimentacion'" class="filas">
          <li v-for="f in filas" :key="f.id">
            <span class="avatar">{{ iniciales(d.nombreAnimal(f.id)) }}</span>
            <button type="button" class="quien" @click="emit('abrir', f.siguiente ?? f.tomas[f.tomas.length - 1]!)">
              <strong>{{ d.nombreAnimal(f.id) }}</strong>
              <small>{{ d.animal(f.id)?.taxonomia.nombre_comun }} · {{ d.lugar(f.tomas[0]!) }} · {{ d.alimentos(f.tomas[0]!) }}</small>
            </button>
            <span class="tomas">
              <button
                v-for="t in f.tomas"
                :key="t.id_actividad"
                type="button"
                class="toma"
                :class="{ hecha: t.completada, tarde: tarde(t) }"
                :title="t.completada ? 'Hecha' : tarde(t) ? 'Atrasada · ver detalle' : 'Pendiente · ver detalle'"
                @click="emit('abrir', t)"
              >
                {{ horaCorta(t) }}
              </button>
            </span>
            <button
              v-if="f.siguiente"
              class="btn btn-primary chico"
              type="button"
              :disabled="actualizandoId === f.siguiente.id_actividad"
              @click="emit('completar', f.siguiente)"
            >
              ✓ Hecha {{ horaCorta(f.siguiente) }}
            </button>
            <span v-else class="ok">Alimentado ✓</span>
            <BotonesActividad
              sin-check
              :hecha="false"
              :observaciones="f.tomas.reduce((n, t) => n + (obsPorActividad[t.id_actividad] ?? 0), 0)"
              :nombre="d.nombreAnimal(f.id)"
              @observar="emit('observar', f.siguiente ?? f.tomas[f.tomas.length - 1]!)"
            />
          </li>
        </ul>

        <ul v-else class="filas">
          <li v-for="a in actividadesFila" :key="a.id_actividad" :class="{ hecha: a.completada }">
            <span class="avatar"><IconoTipo :tipo="a.tipo_actividad" /></span>
            <button type="button" class="quien" @click="emit('abrir', a)">
              <strong>{{ d.titulo(a) }}</strong>
              <small>{{ d.detalle(a) }}</small>
            </button>
            <span class="hora" :class="{ tarde: tarde(a) }">
              {{ horaCorta(a) || 'Sin hora' }}{{ horaFin(a) && horaFin(a) !== horaCorta(a) ? `–${horaFin(a)}` : '' }}{{ tarde(a) ? ' · atrasada' : '' }}
            </span>
            <span class="badge" :class="a.completada ? 'b-hecha' : tarde(a) ? 'b-tarde' : 'b-pend'">
              {{ a.completada ? 'Hecha' : tarde(a) ? 'Atrasada' : 'Pendiente' }}
            </span>
            <BotonesActividad
              :hecha="a.completada"
              :ocupado="actualizandoId === a.id_actividad"
              :observaciones="obsPorActividad[a.id_actividad] ?? 0"
              :nombre="d.titulo(a)"
              @completar="emit('completar', a)"
              @observar="emit('observar', a)"
            />
          </li>
        </ul>
      </div>
    </div>

  </section>
</template>

<style scoped>
.indicadores {
  display: grid;
  gap: 12px;
  margin-bottom: 18px;
}

.ind-h {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}

.ind-h h2 {
  font-size: 17px;
  font-weight: 700;
}

.ind-h span {
  font-size: 13px;
  color: var(--color-text-muted);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 10px;
}

.ind {
  position: relative;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) 46px;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-surface);
  text-align: left;
}

.ind:hover {
  border-color: var(--c);
}

.ind.sel {
  border-color: var(--c);
  background: var(--cb);
}

.ico {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: var(--cb);
  color: var(--c);
}

.ind.sel .ico {
  background: var(--color-surface);
}

.ico :deep(svg) {
  width: 20px;
  height: 20px;
}

.txt {
  display: grid;
  gap: 1px;
  min-width: 0;
}

.tit {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.big {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--c);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.big small {
  font-size: 15px;
  opacity: 0.6;
}

.big em {
  font-family: var(--font-sans);
  font-size: 12.5px;
  font-style: normal;
  font-weight: 500;
  color: var(--color-text);
}

.pie {
  overflow: hidden;
  font-size: 11.5px;
  color: var(--color-text-muted);
  white-space: nowrap;
  text-overflow: ellipsis;
}

.pie .tarde {
  font-weight: 600;
  color: var(--color-danger);
}

.pie .aldia {
  font-weight: 600;
  color: var(--color-primary);
}

.ring {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), var(--color-surface-alt) 0);
}

.ind.sel .ring {
  background: conic-gradient(var(--c) calc(var(--p) * 1%), var(--color-surface) 0);
}

.ring span {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-surface);
  font-size: 11px;
  font-weight: 700;
  color: var(--c);
}

.caret {
  position: absolute;
  top: 6px;
  right: 9px;
  font-size: 9px;
  color: var(--color-text-subtle);
}

.detalle {
  /* Ocupa toda la fila de la cuadrícula, debajo de su tarjeta */
  grid-column: 1 / -1;
  display: grid;
  gap: 4px;
  min-width: 0;
  max-width: 100%;
  padding: 14px 18px;
  border: 1px solid var(--c);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.det-h {
  display: flex;
  min-width: 0;
  max-width: 100%;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.det-h h3 {
  display: flex;
  min-width: 0;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
}

.cnt {
  min-width: 22px;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--cb);
  color: var(--c);
  font-size: 12px;
  text-align: center;
}

.det-acc {
  display: flex;
  min-width: 0;
  max-width: 100%;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.seg {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border-radius: 999px;
  background: var(--color-surface-alt);
}

.seg button {
  padding: 5px 12px;
  border: none;
  border-radius: 999px;
  background: none;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.seg button.on {
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: 0 1px 3px rgba(35, 40, 31, 0.15);
}

.cerrar {
  border: none;
  background: none;
  font-size: 20px;
  line-height: 1;
  color: var(--color-text-muted);
}

.vacio {
  padding: 14px 0 4px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.filas {
  display: grid;
  min-width: 0;
  max-width: 100%;
  padding: 0;
  list-style: none;
}

.filas li {
  display: grid;
  min-width: 0;
  grid-template-columns: 34px minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid var(--color-border);
}

.filas li:last-child {
  border-bottom: none;
}

.avatar {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--cb);
  color: var(--c);
  font-size: 11px;
  font-weight: 700;
}

.avatar :deep(svg) {
  width: 15px;
  height: 15px;
}

.quien {
  display: grid;
  min-width: 0;
  max-width: 100%;
  padding: 0;
  border: none;
  background: none;
  text-align: left;
}

.quien:hover strong {
  text-decoration: underline;
}

.quien strong {
  font-size: 14px;
}

.quien small {
  min-width: 0;
  overflow: visible;
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: normal;
  overflow-wrap: anywhere;
}

li.hecha .quien strong {
  color: var(--color-text-muted);
  text-decoration: line-through;
}

.tomas {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 4px;
}

.toma {
  padding: 3px 9px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: var(--color-surface-alt);
  font-size: 12px;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.toma:hover {
  border-color: var(--color-border-strong);
}

.toma.hecha {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  text-decoration: line-through;
}

.toma.tarde {
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-weight: 600;
}

.hora {
  font-size: 13px;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.hora.tarde {
  font-weight: 600;
  color: var(--color-danger);
}

.chico {
  padding: 6px 12px;
  font-size: 13px;
  white-space: nowrap;
}

.ok {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  white-space: nowrap;
}

@media (max-width: 760px) {
  .filas li {
    grid-template-columns: minmax(0, 1fr);
  }

  .filas li > * {
    grid-column: 1;
    justify-self: start;
    max-width: 100%;
  }

  .filas li .avatar {
    display: none;
  }

  .filas li .tomas {
    justify-content: flex-start;
  }
}
</style>
