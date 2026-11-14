<script setup lang="ts">
import { computed } from 'vue'
import BotonesActividad from '@/components/planificacion/BotonesActividad.vue'
import IconoTipo from '@/components/planificacion/IconoTipo.vue'
import {
  CATEGORIAS_OBSERVACION,
  TIPOS_ENRIQUECIMIENTO,
  describirActividades,
  diaLargo,
  duracionMinutos,
  estaAtrasada,
  horaCorta,
  horaFin,
  textoDuracion,
  type ContextoActividades,
} from '@/config/actividades'
import type { Actividad, Observacion } from '@/types/actividades'

// Panel derecho del calendario: el detalle de una actividad o la lista de un grupo
const props = defineProps<{
  modo: 'detalle' | 'lista'
  actividad?: Actividad | null
  items?: Actividad[]
  tituloLista?: string
  // Si el detalle se abrió desde una lista, se puede volver a ella
  volverA?: string
  ctx: ContextoActividades
  hoy: string
  ahora: string
  observaciones: Observacion[]
  cargandoObservaciones: boolean
  obsPorActividad: Record<number, number>
  actualizandoId: number | null
}>()
const emit = defineEmits<{
  close: []
  volver: []
  abrir: [a: Actividad]
  completar: [a: Actividad]
  reabrir: [a: Actividad]
  observar: [a: Actividad]
  editar: [a: Actividad]
  eliminar: [a: Actividad]
}>()

// Se puede editar o eliminar mientras esté pendiente; las dosis se manejan desde el tratamiento
const modificable = (a: Actividad) => !a.completada && a.tipo_actividad !== 'tratamiento'
// Solo se completan actividades de hoy o de días anteriores
const esFutura = (a: Actividad) => a.fecha_programada > props.hoy

const d = computed(() => describirActividades(props.ctx))
const tarde = (a: Actividad) => estaAtrasada(a, props.hoy, props.ahora)
const estado = (a: Actividad) =>
  a.completada ? { texto: 'Hecha', clase: 'b-hecha' } : tarde(a) ? { texto: 'Atrasada', clase: 'b-tarde' } : { texto: 'Pendiente', clase: 'b-pend' }

const a = computed(() => props.actividad ?? null)
const tipoPanel = computed(() => a.value?.tipo_actividad ?? props.items?.[0]?.tipo_actividad ?? 'alimentacion')
const dieta = computed(() => (a.value?.id_dieta ? props.ctx.dietasPorId[a.value.id_dieta] : undefined))
const hechasLista = computed(() => (props.items ?? []).filter((x) => x.completada).length)

function fechaHora(valor: string) {
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return valor
  return fecha.toLocaleString('es-EC', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}
const capitalizar = (texto: string) => texto.charAt(0).toUpperCase() + texto.slice(1)
</script>

<template>
  <aside class="panel" :class="`t-${tipoPanel}`" aria-label="Detalle de actividades">
    <!-- Detalle -->
    <template v-if="modo === 'detalle' && a">
      <header class="p-h">
        <span class="p-ico"><IconoTipo :tipo="a.tipo_actividad" /></span>
        <div class="p-tit">
          <button v-if="volverA" type="button" class="volver" @click="emit('volver')">‹ Volver a {{ volverA.toLowerCase() }}</button>
          <h3>{{ d.titulo(a) }}</h3>
          <p>
            {{ diaLargo(a.fecha_programada) }}
            <template v-if="a.hora_programada"> · {{ horaCorta(a) }}<template v-if="horaFin(a) !== horaCorta(a)">–{{ horaFin(a) }}</template></template>
          </p>
        </div>
        <button class="cerrar" type="button" aria-label="Cerrar panel" @click="emit('close')">×</button>
      </header>

      <div class="p-b">
        <dl class="datos">
          <div><dt>Estado</dt><dd><span class="badge" :class="estado(a).clase">{{ estado(a).texto }}</span></dd></div>
          <div v-if="a.id_animal"><dt>Ejemplar</dt><dd>{{ d.nombreAnimal(a.id_animal) }} · {{ d.animal(a.id_animal)?.taxonomia.nombre_comun }}</dd></div>
          <div><dt>Lugar</dt><dd>{{ d.lugar(a) }}</dd></div>
          <div v-if="duracionMinutos(a)"><dt>Duración</dt><dd>{{ textoDuracion(duracionMinutos(a)) }}</dd></div>
          <div v-if="a.tipo_actividad === 'alimentacion'">
            <dt>Dieta</dt>
            <dd>
              <template v-if="dieta">
                <span v-for="al in dieta.alimentos" :key="al.id_dieta_alimento" class="alimento">
                  {{ al.nombre_alimento }} · {{ al.cantidad_gramos }} {{ al.unidad_cantidad ?? 'g' }}
                </span>
              </template>
              <template v-else>{{ d.alimentos(a) }}</template>
            </dd>
          </div>
          <div v-if="a.tipo_enriquecimiento"><dt>Tipo</dt><dd>{{ TIPOS_ENRIQUECIMIENTO[a.tipo_enriquecimiento] }}</dd></div>
          <div v-if="a.descripcion_estimulo"><dt>Estímulo</dt><dd>{{ a.descripcion_estimulo }}</dd></div>
          <div v-if="a.objetivo_entrenamiento"><dt>Objetivo</dt><dd>{{ a.objetivo_entrenamiento }}</dd></div>
          <div v-if="a.tipo_refuerzo"><dt>Refuerzo</dt><dd>{{ a.tipo_refuerzo }}</dd></div>
          <div v-if="a.observaciones"><dt>Nota</dt><dd>{{ a.observaciones }}</dd></div>
          <div><dt>Programada por</dt><dd>{{ d.usuario(a.id_usuario_programo) }}</dd></div>
          <div v-if="a.completada">
            <dt>Completada por</dt>
            <dd>{{ d.usuario(a.id_usuario_completo) }}<template v-if="a.fecha_completada"> · {{ fechaHora(a.fecha_completada) }}</template></dd>
          </div>
        </dl>

        <section class="obs">
          <h4>Observaciones <span>{{ observaciones.length }}</span></h4>
          <p v-if="cargandoObservaciones" class="tenue">Cargando observaciones…</p>
          <p v-else-if="!observaciones.length" class="tenue">
            Aún no hay observaciones. Registra lo que notes del comportamiento, el recinto o el estado físico.
          </p>
          <article v-for="o in observaciones" :key="o.id_observacion" class="obs-item">
            <div class="obs-tags">
              <span class="badge b-pend">{{ CATEGORIAS_OBSERVACION[o.categoria].label }}</span>
              <span class="badge" :class="`sev-${o.severidad}`">Severidad {{ o.severidad }}</span>
              <span class="obs-meta">{{ fechaHora(o.fecha_registro) }} · {{ d.usuario(o.id_usuario) }}</span>
            </div>
            <p>{{ o.detalle }}</p>
            <small v-if="o.genera_alerta" class="obs-alerta">Alerta para el veterinario y el encargado de manejo animal</small>
          </article>
        </section>
      </div>

      <footer class="p-f">
        <div v-if="modificable(a)" class="p-f-gestion">
          <button class="btn btn-secondary" type="button" @click="emit('editar', a)">Editar</button>
          <button class="btn btn-peligro" type="button" @click="emit('eliminar', a)">Eliminar</button>
        </div>
        <button class="btn btn-secondary" type="button" @click="emit('observar', a)">
          <svg class="ico-btn" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16Z" /><path d="m13.5 6.5 4 4" /></svg>
          Agregar observación
        </button>
        <button
          v-if="a.completada"
          class="btn btn-secondary"
          type="button"
          :disabled="actualizandoId === a.id_actividad"
          @click="emit('reabrir', a)"
        >
          Marcar como pendiente
        </button>
        <button
          v-else
          class="btn btn-primary"
          type="button"
          :disabled="actualizandoId === a.id_actividad || esFutura(a)"
          :title="esFutura(a) ? 'Solo se pueden completar actividades de hoy o de días anteriores' : undefined"
          @click="emit('completar', a)"
        >
          <svg class="ico-btn" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
          Marcar como hecha
        </button>
      </footer>
    </template>

    <!-- Lista de un grupo (alimentación de una hora o un tipo en la vista mes) -->
    <template v-else-if="modo === 'lista'">
      <header class="p-h">
        <span class="p-ico"><IconoTipo :tipo="tipoPanel" /></span>
        <div class="p-tit">
          <h3>{{ capitalizar(tituloLista ?? '') }}</h3>
          <p>{{ hechasLista }} de {{ items?.length ?? 0 }} hechas</p>
        </div>
        <button class="cerrar" type="button" aria-label="Cerrar panel" @click="emit('close')">×</button>
      </header>
      <div class="p-b">
        <ul class="lista">
          <li v-for="x in items" :key="x.id_actividad" :class="{ hecha: x.completada }">
            <button type="button" class="abrir" :title="`Ver detalle de ${d.titulo(x)}`" @click="emit('abrir', x)">
              <strong>{{ x.tipo_actividad === 'alimentacion' ? d.nombreAnimal(x.id_animal) : d.titulo(x) }}</strong>
              <small>{{ horaCorta(x) || 'Sin hora' }} · {{ d.detalle(x) }}</small>
              <span class="badge" :class="estado(x).clase">{{ estado(x).texto }}</span>
            </button>
            <BotonesActividad
              :hecha="x.completada"
              :ocupado="actualizandoId === x.id_actividad"
              :observaciones="obsPorActividad[x.id_actividad] ?? 0"
              :nombre="d.titulo(x)"
              @completar="emit('completar', x)"
              @observar="emit('observar', x)"
            />
          </li>
        </ul>
        <p class="tenue">Toca una actividad para ver toda su información.</p>
      </div>
    </template>
  </aside>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-left: 1px solid var(--color-border);
  background: var(--color-surface);
}

.p-h {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 16px 18px 12px;
  border-bottom: 1px solid var(--color-border);
}

.p-ico {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--cb);
  color: var(--c);
}

.p-tit {
  flex: 1;
  min-width: 0;
}

.p-tit h3 {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.25;
}

.p-tit p {
  margin-top: 3px;
  font-size: 12.5px;
  color: var(--color-text-muted);
}

.volver {
  display: block;
  margin-bottom: 4px;
  padding: 0;
  border: none;
  background: none;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-primary);
}

.volver:hover {
  text-decoration: underline;
}

.cerrar {
  border: none;
  background: none;
  font-size: 20px;
  line-height: 1;
  color: var(--color-text-muted);
}

.p-b {
  display: grid;
  flex: 1;
  align-content: start;
  gap: 16px;
  overflow-y: auto;
  padding: 14px 18px;
}

.p-f {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 18px 16px;
  border-top: 1px solid var(--color-border);
}

.p-f .btn {
  flex: 1;
  padding: 9px 10px;
  font-size: 13px;
}

/* Editar y eliminar ocupan su propia fila arriba de las acciones del día */
.p-f-gestion {
  display: flex;
  flex: 1 1 100%;
  gap: 8px;
}

.btn-peligro {
  border: 1px solid #e6b8b2;
  background: var(--color-surface);
  color: var(--color-danger);
}

.btn-peligro:hover {
  background: var(--color-danger-soft);
}

.ico-btn {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.datos > div {
  display: grid;
  grid-template-columns: minmax(78px, 0.4fr) minmax(0, 0.6fr);
  align-items: start;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

.datos dt {
  color: var(--color-text-muted);
}

.datos dd {
  min-width: 0;
  margin: 0;
  font-weight: 500;
  overflow-wrap: anywhere;
  text-align: left;
}

.alimento {
  display: block;
}

.obs {
  display: grid;
  gap: 8px;
}

.obs h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 700;
}

.obs h4 span {
  min-width: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--color-surface-alt);
  font-size: 11.5px;
  color: var(--color-text-muted);
  text-align: center;
}

.tenue {
  font-size: 12.5px;
  color: var(--color-text-muted);
}

.obs-item {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.obs-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
}

.obs-meta {
  margin-left: auto;
  font-size: 11.5px;
  color: var(--color-text-subtle);
}

.obs-item p {
  font-size: 13px;
  line-height: 1.45;
}

.obs-alerta {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--color-danger);
}

.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.b-hecha,
.sev-bajo {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.b-pend {
  background: var(--color-surface-alt);
  color: var(--color-text-muted);
}

.b-tarde,
.sev-alto {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.sev-medio {
  background: #f5e9c4;
  color: #87661a;
}

.lista {
  display: grid;
  padding: 0;
  list-style: none;
}

.lista li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--color-border);
}

.lista li:last-child {
  border-bottom: none;
}

.abrir {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  column-gap: 8px;
  margin-left: -6px;
  padding: 4px 6px;
  border: none;
  border-radius: 8px;
  background: none;
  text-align: left;
}

.abrir:hover {
  background: var(--color-surface-alt);
}

.abrir strong {
  font-size: 13.5px;
}

.abrir small {
  overflow: hidden;
  grid-column: 1;
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
  text-overflow: ellipsis;
}

.abrir .badge {
  grid-row: 1 / 3;
  grid-column: 2;
}

li.hecha .abrir strong {
  color: var(--color-text-muted);
  text-decoration: line-through;
}
</style>
