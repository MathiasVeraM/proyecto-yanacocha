<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import BotonesActividad from '@/components/planificacion/BotonesActividad.vue'
import IconoTipo from '@/components/planificacion/IconoTipo.vue'
import {
  TIPOS_ACTIVIDAD,
  TIPO_LABEL,
  aMinutos,
  deIso,
  describirActividades,
  diaCorto,
  diaLargo,
  duracionMinutos,
  estaAtrasada,
  horaCorta,
  horaFin,
  lunesDe,
  sumarDias,
  type ContextoActividades,
} from '@/config/actividades'
import type { Actividad, TipoActividad } from '@/types/actividades'

export type VistaCalendario = 'dia' | 'semana' | 'mes'

const props = defineProps<{
  vista: VistaCalendario
  ancla: string
  actividades: Actividad[]
  ctx: ContextoActividades
  hoy: string
  ahora: string
  obsPorActividad: Record<number, number>
  seleccion: string | null
  enfoque: number | null
  actualizandoId: number | null
  // Bloque punteado mientras se crea una actividad
  fantasma: { fecha: string; hora: string; minutos: number } | null
}>()
const emit = defineEmits<{
  abrir: [a: Actividad]
  lista: [clave: string, titulo: string, items: Actividad[]]
  crear: [fecha: string, hora: string]
  completar: [a: Actividad]
  observar: [a: Actividad]
  verDia: [fecha: string]
  enfocado: []
}>()

const ALTO_HORA = 60
const scroll = ref<HTMLElement | null>(null)
const d = computed(() => describirActividades(props.ctx))
const tarde = (a: Actividad) => estaAtrasada(a, props.hoy, props.ahora)
const y = (hora: string) => (aMinutos(hora) / 60) * ALTO_HORA

const dias = computed(() =>
  props.vista === 'dia' ? [props.ancla] : Array.from({ length: 7 }, (_, i) => sumarDias(lunesDe(props.ancla), i)),
)

const porDia = computed(() => {
  const mapa: Record<string, Actividad[]> = {}
  for (const a of props.actividades) (mapa[a.fecha_programada] ??= []).push(a)
  return mapa
})
const delDia = (fecha: string) => porDia.value[fecha] ?? []
const sinHora = (fecha: string) => delDia(fecha).filter((a) => !a.hora_programada)
const haySinHora = computed(() => dias.value.some((f) => sinHora(f).length))

interface Bloque {
  id: string
  hora: string
  items: Actividad[]
  esAlimentacion: boolean
  ini: number
  fin: number
  carril: number
  carriles: number
}

// Alimentaciones de la misma hora van juntas en un chip; el resto es una tarjeta.
// Si se cruzan en el tiempo, se reparten en carriles lado a lado.
function bloques(fecha: string) {
  const lista: Bloque[] = []
  const porHora = new Map<string, Bloque>()
  for (const a of delDia(fecha)) {
    if (!a.hora_programada) continue
    const hora = horaCorta(a)
    const ini = aMinutos(hora)
    if (a.tipo_actividad === 'alimentacion') {
      let grupo = porHora.get(hora)
      if (!grupo) {
        grupo = { id: `${fecha}-al-${hora}`, hora, items: [], esAlimentacion: true, ini, fin: ini + 26, carril: 0, carriles: 1 }
        porHora.set(hora, grupo)
        lista.push(grupo)
      }
      grupo.items.push(a)
    } else {
      lista.push({
        id: `a-${a.id_actividad}`,
        hora,
        items: [a],
        esAlimentacion: false,
        ini,
        fin: ini + Math.max(duracionMinutos(a), 45),
        carril: 0,
        carriles: 1,
      })
    }
  }
  lista.sort((a, b) => a.ini - b.ini || b.fin - a.fin)
  let grupo: Bloque[] = []
  let finGrupo = -1
  const cerrar = () => {
    const carriles: number[] = []
    for (const b of grupo) {
      let i = carriles.findIndex((fin) => fin <= b.ini)
      if (i < 0) {
        i = carriles.length
        carriles.push(0)
      }
      carriles[i] = b.fin
      b.carril = i
    }
    for (const b of grupo) b.carriles = carriles.length
  }
  for (const b of lista) {
    if (grupo.length && b.ini >= finGrupo) {
      cerrar()
      grupo = []
      finGrupo = -1
    }
    grupo.push(b)
    finGrupo = Math.max(finGrupo, b.fin)
  }
  if (grupo.length) cerrar()
  return lista
}

const estiloBloque = (b: Bloque, alto = true) => ({
  top: `${(b.ini / 60) * ALTO_HORA + 2}px`,
  ...(alto ? { height: `${Math.max(((b.fin - b.ini) / 60) * ALTO_HORA - 4, 24)}px` } : {}),
  left: `calc(${(b.carril / b.carriles) * 100}% + 3px)`,
  [alto ? 'width' : 'maxWidth']: `calc(${100 / b.carriles}% - 6px)`,
})
const altoBloque = (b: Bloque) => Math.max(((b.fin - b.ini) / 60) * ALTO_HORA - 4, 24)
const conBotones = (b: Bloque) => b.carriles === 1 || props.vista === 'dia'

function clicHueco(evento: MouseEvent, fecha: string) {
  const minutos = Math.floor((evento.offsetY / ALTO_HORA) * 2) * 30
  emit('crear', fecha, `${String(Math.floor(minutos / 60)).padStart(2, '0')}:${String(minutos % 60).padStart(2, '0')}`)
}

// ---- Mes ----
const celdasMes = computed(() => {
  const ancla = deIso(props.ancla)
  const primero = new Date(ancla.getFullYear(), ancla.getMonth(), 1, 12)
  const ultimo = new Date(ancla.getFullYear(), ancla.getMonth() + 1, 0, 12)
  const inicio = lunesDe(`${primero.getFullYear()}-${String(primero.getMonth() + 1).padStart(2, '0')}-01`)
  const dias = Math.round((ultimo.getTime() - deIso(inicio).getTime()) / 864e5) + 1
  const total = Math.ceil(dias / 7) * 7
  return Array.from({ length: total }, (_, i) => {
    const fecha = sumarDias(inicio, i)
    return { fecha, numero: deIso(fecha).getDate(), fuera: deIso(fecha).getMonth() !== ancla.getMonth() }
  })
})

const chipsMes = (fecha: string) =>
  TIPOS_ACTIVIDAD.map((tipo: TipoActividad) => {
    const items = delDia(fecha).filter((a) => a.tipo_actividad === tipo)
    return { tipo, items, hechas: items.filter((a) => a.completada).length, tarde: items.some(tarde) }
  }).filter((c) => c.items.length)

// Al abrir la semana o el día, la rejilla arranca en el horario de trabajo (06:00)
function desplazar() {
  void nextTick(() => {
    if (!scroll.value) return
    const maximo = scroll.value.scrollHeight - scroll.value.clientHeight
    scroll.value.scrollTop = Math.min(6 * ALTO_HORA + 10, maximo)
  })
}
function enfocarActividad(actividad: Actividad) {
  void nextTick(() => {
    if (props.vista === 'mes') {
      emit('enfocado')
      return
    }
    if (!scroll.value) return
    const margen = 2 * ALTO_HORA
    const posicion = actividad.hora_programada
      ? Math.max(0, y(actividad.hora_programada) - margen)
      : 6 * ALTO_HORA + 10
    const maximo = scroll.value.scrollHeight - scroll.value.clientHeight
    scroll.value.scrollTop = Math.min(posicion, maximo)
    emit('enfocado')
  })
}
onMounted(desplazar)
watch(() => [props.vista, props.ancla], desplazar)
watch(
  () => props.enfoque
    ? props.actividades.find((actividad) => actividad.id_actividad === props.enfoque) ?? null
    : null,
  (actividad) => {
    if (actividad) enfocarActividad(actividad)
  },
)
</script>

<template>
  <!-- Semana / Día -->
  <div v-if="vista !== 'mes'" class="rejilla">
    <div class="cols cabeza" :style="{ '--n': dias.length }">
      <div class="gutter">Hora</div>
      <div v-for="f in dias" :key="f" :class="{ 'hoy-columna': f === hoy }">
        <button type="button" class="dia" :class="{ hoy: f === hoy }" :title="`Ver ${diaLargo(f)}`" @click="emit('verDia', f)">
          <span class="n">{{ deIso(f).getDate() }}</span>
          <span class="w">{{ vista === 'dia' ? diaLargo(f).split(' ')[0] : diaCorto(f) }}</span>
        </button>
      </div>
    </div>

    <div v-if="haySinHora" class="cols sin-hora" :style="{ '--n': dias.length }">
      <div class="gutter">Sin hora</div>
      <div v-for="f in dias" :key="f">
        <button
          v-for="a in sinHora(f)"
          :key="a.id_actividad"
          type="button"
          class="chip-sh"
          :class="[`t-${a.tipo_actividad}`, { hecha: a.completada, tarde: tarde(a) }]"
          @click="emit('abrir', a)"
        >
          {{ d.tituloTarjeta(a) }}
        </button>
      </div>
    </div>

    <div ref="scroll" class="scroll">
      <div class="cols cuerpo" :style="{ '--n': dias.length }">
        <div class="horas">
          <div v-for="h in 24" :key="h"><span v-if="h > 1">{{ String(h - 1).padStart(2, '0') }}:00</span></div>
        </div>
        <div
          v-for="f in dias"
          :key="f"
          class="col"
          :class="{ 'hoy-columna': f === hoy }"
          @click.self="clicHueco($event, f)"
        >
          <div
            v-if="fantasma && fantasma.fecha === f && fantasma.hora"
            class="fantasma"
            :style="{ top: `${y(fantasma.hora) + 2}px`, height: `${Math.max((fantasma.minutos / 60) * ALTO_HORA - 4, 26)}px` }"
          >
            {{ fantasma.hora }} · Nueva actividad
          </div>
          <template v-for="b in bloques(f)" :key="b.id">
            <button
              v-if="b.esAlimentacion"
              type="button"
              class="alim"
              :class="{ hecha: b.items.every((a) => a.completada), tarde: b.items.some(tarde), sel: seleccion === b.id || (b.items.length === 1 && seleccion === `a-${b.items[0]!.id_actividad}`) }"
              :style="estiloBloque(b, false)"
              :title="`Alimentación de las ${b.hora}: ${b.items.map((a) => d.nombreAnimal(a.id_animal)).join(', ')}`"
              @click="b.items.length > 1 ? emit('lista', b.id, `Alimentación de las ${b.hora}`, b.items) : emit('abrir', b.items[0]!)"
            >
              Alimentación · {{ b.items.length > 1 ? b.items.length : d.nombreAnimal(b.items[0]!.id_animal) }}
            </button>
            <div
              v-else
              role="button"
              tabindex="0"
              class="ev"
              :class="[`t-${b.items[0]!.tipo_actividad}`, { hecha: b.items[0]!.completada, tarde: tarde(b.items[0]!), sel: seleccion === b.id, corta: altoBloque(b) < 52, 'con-botones': conBotones(b) }]"
              :style="estiloBloque(b)"
              :aria-label="`${d.titulo(b.items[0]!)}, ${b.hora}`"
              @click="emit('abrir', b.items[0]!)"
              @keydown.enter.self="emit('abrir', b.items[0]!)"
            >
              <span class="ev-t">{{ d.tituloTarjeta(b.items[0]!) }}</span>
              <span class="ev-m">
                <b v-if="tarde(b.items[0]!)" class="txt-tarde">Atrasada · </b>{{ b.hora }}{{ horaFin(b.items[0]!) !== b.hora ? ` – ${horaFin(b.items[0]!)}` : '' }}<template v-if="altoBloque(b) >= 52"> · {{ d.detalle(b.items[0]!) }}</template>
              </span>
              <BotonesActividad
                v-if="conBotones(b)"
                class="ev-botones"
                compacto
                :hecha="b.items[0]!.completada"
                :ocupado="actualizandoId === b.items[0]!.id_actividad"
                :observaciones="obsPorActividad[b.items[0]!.id_actividad] ?? 0"
                :nombre="d.titulo(b.items[0]!)"
                @completar="emit('completar', b.items[0]!)"
                @observar="emit('observar', b.items[0]!)"
              />
            </div>
          </template>
        </div>
        <div v-if="dias.includes(hoy)" class="ahora" :style="{ top: `${y(ahora)}px` }" :title="`Ahora · ${ahora}`"><i /></div>
      </div>
    </div>
  </div>

  <!-- Mes -->
  <div v-else class="mes">
    <div class="mes-cabeza"><div v-for="w in ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']" :key="w">{{ w }}</div></div>
    <div class="mes-grid">
      <div
        v-for="c in celdasMes"
        :key="c.fecha"
        class="celda"
        :class="{ fuera: c.fuera, hoy: c.fecha === hoy }"
        @click.self="emit('crear', c.fecha, '')"
      >
        <button class="num" type="button" :aria-label="`Ver ${diaLargo(c.fecha)}`" @click="emit('verDia', c.fecha)">{{ c.numero }}</button>
        <button
          v-for="ch in chipsMes(c.fecha)"
          :key="ch.tipo"
          type="button"
          class="chip"
          :class="[`t-${ch.tipo}`, { tarde: ch.tarde, hecha: ch.hechas === ch.items.length }]"
          @click="emit('lista', `${c.fecha}-${ch.tipo}`, `${TIPO_LABEL[ch.tipo]} · ${diaLargo(c.fecha)}`, ch.items)"
        >
          <IconoTipo :tipo="ch.tipo" /><span>{{ TIPO_LABEL[ch.tipo] }}</span><b>{{ ch.items.length }}</b>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rejilla {
  display: grid;
  grid-template-rows: auto auto 1fr;
  min-width: 0;
  overflow-x: auto;
}

.cols {
  display: grid;
  grid-template-columns: 62px repeat(var(--n), minmax(118px, 1fr));
}

.cabeza {
  border-bottom: 1px solid var(--linea);
}

.cabeza > div {
  display: grid;
  place-items: center;
  padding: 8px 4px;
  border-left: 1px solid var(--linea);
}

.gutter {
  font-size: 12px;
  color: var(--color-text-muted);
}

.cabeza > .gutter,
.sin-hora > .gutter {
  border-left: none;
}

.dia {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 6px;
  border: none;
  border-radius: 999px;
  background: none;
  font-size: 13px;
  text-transform: capitalize;
}

.dia:hover {
  background: var(--color-surface-alt);
}

.dia .n {
  display: grid;
  place-items: center;
  min-width: 26px;
  height: 26px;
  border-radius: 50%;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.dia .w {
  color: var(--color-text-muted);
}

.dia.hoy .n {
  background: var(--color-primary);
  color: var(--color-surface);
  font-weight: 700;
}

.dia.hoy .w {
  font-weight: 600;
  color: var(--color-primary);
}

.cabeza > div.hoy-columna {
  background: rgba(46, 107, 52, 0.1);
}

.dia.hoy {
  padding: 3px 8px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 700;
}

.sin-hora {
  border-bottom: 1px solid var(--linea);
}

.sin-hora > div {
  display: grid;
  align-content: start;
  gap: 3px;
  min-height: 30px;
  padding: 4px;
  border-left: 1px solid var(--linea);
}

.sin-hora > .gutter {
  padding-top: 9px;
  font-size: 11px;
  text-align: right;
}

.chip-sh {
  overflow: hidden;
  padding: 3px 7px;
  border: none;
  border-left: 3px solid var(--c);
  border-radius: 3px;
  background: var(--cb);
  font-size: 11px;
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chip-sh.hecha {
  border-left-color: var(--color-border-strong);
  background: var(--color-surface-alt);
  color: var(--color-text-muted);
}

.chip-sh.tarde {
  border-left-color: var(--color-danger);
}

.scroll {
  min-height: 0;
  max-height: 66vh;
  overflow-y: auto;
}

.cuerpo {
  position: relative;
  background-image:
    repeating-linear-gradient(to bottom, var(--linea) 0, var(--linea) 1px, transparent 1px, transparent 60px),
    repeating-linear-gradient(to bottom, transparent 0, transparent 30px, var(--linea-suave) 30px, var(--linea-suave) 31px, transparent 31px, transparent 60px);
}

.horas > div {
  position: relative;
  height: 60px;
}

.horas span {
  position: absolute;
  top: -7px;
  right: 10px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.col {
  position: relative;
  border-left: 1px solid var(--linea);
  cursor: copy;
}

.col:hover {
  background: rgba(46, 107, 52, 0.02);
}

.col.hoy-columna {
  background-color: rgba(46, 107, 52, 0.055);
  box-shadow: inset 1px 0 rgba(46, 107, 52, 0.16), inset -1px 0 rgba(46, 107, 52, 0.16);
}

/* Tarjeta: fondo pastel con franja del color del tipo */
.ev {
  position: absolute;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
  padding: 5px 8px;
  border-left: 3px solid var(--c);
  border-radius: 3px;
  background: var(--cb);
  cursor: pointer;
}

.ev:hover {
  z-index: 4;
  box-shadow: 0 6px 16px rgba(35, 40, 31, 0.12);
}

.ev:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.ev.sel {
  z-index: 4;
  box-shadow: 0 0 0 1.5px var(--c);
}

.ev-t {
  overflow: hidden;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.ev-m {
  overflow: hidden;
  font-size: 11px;
  color: var(--color-text-muted);
  white-space: nowrap;
  text-overflow: ellipsis;
  font-variant-numeric: tabular-nums;
}

.ev.con-botones .ev-t {
  padding-right: 46px;
}

.ev-botones {
  position: absolute;
  top: 4px;
  right: 4px;
}

.ev.corta {
  justify-content: center;
  gap: 0;
  padding: 3px 8px;
}

.ev.hecha {
  border-left-color: var(--color-border-strong);
  background: var(--color-surface-alt);
}

.ev.hecha .ev-t {
  color: var(--color-text-muted);
}

.ev.tarde {
  border-left-color: var(--color-danger);
}

.txt-tarde {
  color: var(--color-danger);
}

/* Alimentaciones agrupadas: chip pequeño */
.alim {
  position: absolute;
  z-index: 3;
  overflow: hidden;
  height: 18px;
  padding: 0 7px 0 6px;
  border: none;
  border-left: 3px solid var(--alim);
  border-radius: 2px;
  background: var(--alim-bg);
  font-size: 10.5px;
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.alim:hover {
  z-index: 4;
  box-shadow: 0 6px 16px rgba(35, 40, 31, 0.12);
}

.alim.hecha {
  border-left-color: var(--color-border-strong);
  background: var(--color-surface-alt);
  color: var(--color-text-muted);
  text-decoration: line-through;
}

.alim.tarde {
  border-left-color: var(--color-danger);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.alim.sel {
  box-shadow: 0 0 0 1.5px var(--alim);
}

.fantasma {
  position: absolute;
  z-index: 3;
  left: 3px;
  right: 3px;
  padding: 5px 8px;
  border: 1.5px dashed var(--color-primary);
  border-left-width: 3px;
  border-radius: 3px;
  background: rgba(226, 235, 214, 0.75);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  pointer-events: none;
}

/* Hora actual: línea gris que cruza la semana, con punto rojo */
.ahora {
  position: absolute;
  left: 62px;
  right: 0;
  z-index: 5;
  border-top: 1.5px solid #8d8a7a;
  pointer-events: none;
}

.ahora i {
  position: absolute;
  top: -4.5px;
  left: -4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
}

/* ---- Mes ---- */
.mes {
  display: grid;
  grid-template-rows: auto 1fr;
  padding: 0 14px 14px;
  overflow-x: auto;
}

.mes-cabeza {
  display: grid;
  grid-template-columns: repeat(7, minmax(110px, 1fr));
  gap: 8px;
  padding: 10px 0 8px;
}

.mes-cabeza div {
  padding-left: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.mes-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(110px, 1fr));
  grid-auto-rows: minmax(112px, auto);
  gap: 8px;
}

.celda {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 8px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-surface);
  cursor: copy;
}

.celda:hover {
  border-color: var(--color-border-strong);
}

.celda.fuera {
  border-style: dashed;
  background: transparent;
}

.celda.fuera .num {
  color: var(--color-text-subtle);
}

.num {
  display: grid;
  place-items: center;
  align-self: flex-end;
  min-width: 28px;
  height: 28px;
  padding: 0 6px;
  border: none;
  border-radius: 999px;
  background: none;
  font-size: 13px;
  font-weight: 700;
}

.num:hover {
  background: var(--color-surface-alt);
}

.celda.hoy .num {
  background: var(--color-primary);
  color: #fff;
}

.celda.hoy {
  border: 2px solid var(--color-primary);
  background: rgba(46, 107, 52, 0.09);
  box-shadow: 0 2px 8px rgba(46, 107, 52, 0.12);
}

.celda.hoy .num {
  box-shadow: 0 0 0 3px rgba(46, 107, 52, 0.14);
}

.chip {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 4px 6px 4px 7px;
  border: 1px solid var(--cd);
  border-radius: 8px;
  background: var(--cb);
  color: var(--c);
  font-size: 12px;
  font-weight: 600;
  text-align: left;
}

.chip:hover {
  box-shadow: 0 4px 12px rgba(35, 40, 31, 0.12);
}

.chip span {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chip b {
  min-width: 20px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-surface);
  font-size: 11px;
  text-align: center;
}

.chip.tarde b {
  background: var(--color-danger);
  color: #fff;
}

.chip.hecha {
  border-color: var(--color-border);
  background: var(--color-surface-alt);
  color: var(--color-text-muted);
}
</style>
