<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import IconoTipo from '@/components/planificacion/IconoTipo.vue'
import { actividadesApi, crucesDeError } from '@/api/actividades'
import { consultas } from '@/api/consultas'
import { ApiError } from '@/api/http'
import { TIPOS_ENRIQUECIMIENTO, TIPO_LABEL, deIso, diaCorto, sumarDias } from '@/config/actividades'
import { useAhora } from '@/composables/useAhora'
import type {
  Actividad,
  ActividadCambios,
  CruceHorario,
  LimitesActividades,
  TipoActividad,
  TipoEnriquecimiento,
} from '@/types/actividades'
import type { Recinto } from '@/types/animales'
import type { AnimalReferencia } from '@/types/actividades'

type TipoCreable = Exclude<TipoActividad, 'alimentacion' | 'tratamiento'>

// Crear (o editar) una actividad desde el panel derecho del calendario.
// Las alimentaciones no se crean aquí: salen de la dieta (Registro de Dietas).
const props = defineProps<{
  animales: AnimalReferencia[]
  recintos: Recinto[]
  fecha: string
  hora: string
  idAnimal?: number
  // Si viene, el panel edita esa actividad en lugar de crear una nueva
  actividad?: Actividad | null
}>()
const emit = defineEmits<{
  close: []
  // cantidad > 1 cuando se creó una actividad repetida
  creada: [actividad: Actividad, cantidad: number]
  editada: [actividad: Actividad]
  // Para dibujar el bloque punteado en el calendario mientras se llena
  borrador: [datos: { fecha: string; hora: string; minutos: number }]
}>()

const { hoy, hora: horaActual } = useAhora()
const editando = computed(() => !!props.actividad)

const TIPOS: TipoCreable[] = ['enriquecimiento', 'entrenamiento', 'limpieza']
const tipo = ref<TipoActividad>('enriquecimiento')
const guardando = ref(false)
const error = ref('')
// Actividades con las que se cruza: se pregunta "¿crear igual?" antes de guardar
const cruces = ref<CruceHorario[] | null>(null)

// Límites del backend (config.py). Mientras llegan se usan los mismos valores por defecto
const limites = ref<LimitesActividades | null>(null)
const duracionMax = computed(() => limites.value?.duracion_max_minutos ?? 240)
const duracionEnriquecimiento = computed(() => limites.value?.duracion_enriquecimiento_minutos ?? 30)
const fechaMax = computed(() => limites.value?.fecha_max ?? sumarDias(hoy.value, 365))
const mesesMax = computed(() => limites.value?.repeticion_meses_max ?? 3)
onMounted(async () => {
  try {
    limites.value = await consultas.limitesActividades()
    if (!editando.value && tipo.value === 'enriquecimiento') aplicarDuracionPorDefecto()
  } catch {
    // Sin límites se usan los valores por defecto; el backend valida igual
  }
})

const f = reactive({
  id_animal: 0,
  id_recinto: 0,
  fecha_programada: '',
  hora_programada: '',
  tipo_enriquecimiento: 'sensorial' as TipoEnriquecimiento,
  descripcion_estimulo: '',
  objetivo_entrenamiento: '',
  tipo_refuerzo: '',
  duracion_horas: 0,
  duracion_minutos: 30,
  observaciones: '',
})

// ---- Repetición: todos los días o ciertos días, hasta una fecha o durante N meses ----
const DIAS_SEMANA = ['L', 'M', 'X', 'J', 'V', 'S', 'D'] // 0 = lunes … 6 = domingo
const NOMBRES_DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
const rep = reactive({
  modo: 'no' as 'no' | 'diario' | 'dias',
  dias: [] as number[],
  termina: 'fecha' as 'fecha' | 'meses',
  hasta: '',
  meses: 1,
})
const diaDeLaSemana = (fecha: string) => (deIso(fecha).getDay() + 6) % 7
function alternarDia(dia: number) {
  rep.dias = rep.dias.includes(dia) ? rep.dias.filter((d) => d !== dia) : [...rep.dias, dia].sort()
}
// Al elegir "ciertos días" se marca el día de la fecha elegida, y la fecha de fin arranca en un mes
watch(
  () => rep.modo,
  (modo) => {
    if (modo === 'dias' && !rep.dias.length && f.fecha_programada) rep.dias = [diaDeLaSemana(f.fecha_programada)]
    if (modo !== 'no' && !rep.hasta && f.fecha_programada) rep.hasta = sumarDias(f.fecha_programada, 29)
  },
)
const hastaMax = computed(() => {
  if (!f.fecha_programada) return fechaMax.value
  const d = deIso(f.fecha_programada)
  const limite = new Date(d.getFullYear(), d.getMonth() + mesesMax.value, d.getDate(), 12)
  const iso = `${limite.getFullYear()}-${String(limite.getMonth() + 1).padStart(2, '0')}-${String(limite.getDate()).padStart(2, '0')}`
  return iso < fechaMax.value ? iso : fechaMax.value
})

// ---- Valores iniciales ----

function proximaHora() {
  // La siguiente hora en punto (para no proponer una hora que ya pasó)
  const h = Number(horaActual.value.slice(0, 2)) + 1
  return h > 23 ? '23:30' : `${String(h).padStart(2, '0')}:00`
}

function aplicarDuracionPorDefecto() {
  const minutos = duracionEnriquecimiento.value
  f.duracion_horas = Math.floor(minutos / 60)
  f.duracion_minutos = minutos % 60
}

watch(
  () => [props.fecha, props.hora, props.idAnimal, props.actividad] as const,
  ([fecha, hora, idAnimal, actividad]) => {
    error.value = ''
    cruces.value = null
    if (actividad) {
      tipo.value = actividad.tipo_actividad
      f.id_animal = actividad.id_animal ?? 0
      f.id_recinto = actividad.id_recinto ?? 0
      f.fecha_programada = actividad.fecha_programada
      f.hora_programada = actividad.hora_programada?.slice(0, 5) ?? ''
      f.duracion_horas = actividad.duracion_horas
      f.duracion_minutos = actividad.duracion_minutos
      f.observaciones = actividad.observaciones ?? ''
      f.tipo_enriquecimiento = (actividad.tipo_enriquecimiento as TipoEnriquecimiento) ?? 'sensorial'
      f.descripcion_estimulo = actividad.descripcion_estimulo ?? ''
      f.objetivo_entrenamiento = actividad.objetivo_entrenamiento ?? ''
      f.tipo_refuerzo = actividad.tipo_refuerzo ?? ''
      return
    }
    // No se programa en el pasado: si el día elegido ya pasó se propone hoy, y la próxima hora
    f.fecha_programada = fecha && fecha >= hoy.value ? fecha : hoy.value
    f.hora_programada = hora || '08:00'
    if (f.fecha_programada === hoy.value && f.hora_programada < horaActual.value) f.hora_programada = proximaHora()
    f.id_animal = idAnimal || props.animales[0]?.id_animal || 0
    f.id_recinto = f.id_recinto || props.recintos[0]?.id_recinto || 0
  },
  { immediate: true },
)

watch(tipo, (nuevo, anterior) => {
  if (editando.value) return
  // El enriquecimiento arranca con su duración por defecto; el resto, con 30 min
  if (nuevo === 'enriquecimiento') aplicarDuracionPorDefecto()
  else if (anterior === 'enriquecimiento') {
    f.duracion_horas = 0
    f.duracion_minutos = 30
  }
})

const minutosTotales = computed(() => (Number(f.duracion_horas) || 0) * 60 + (Number(f.duracion_minutos) || 0))

watch(
  () => [f.fecha_programada, f.hora_programada, minutosTotales.value] as const,
  () => {
    emit('borrador', { fecha: f.fecha_programada, hora: f.hora_programada, minutos: minutosTotales.value || 30 })
  },
  { immediate: true },
)

// Si cambia algo, el aviso de cruce deja de aplicar
watch(
  () => [f.fecha_programada, f.hora_programada, minutosTotales.value, f.id_animal, f.id_recinto, tipo.value, rep.modo, rep.dias, rep.hasta, rep.meses],
  () => (cruces.value = null),
  { deep: true },
)

// La hora mínima solo aplica si la actividad es hoy
const horaMin = computed(() => (f.fecha_programada === hoy.value ? horaActual.value : undefined))

// ---- Validación (las mismas reglas que el backend) ----

function validar(): string {
  if (!f.fecha_programada) return 'Selecciona un día para la actividad.'
  if (!f.hora_programada) return 'Indica la hora de la actividad.'
  const cambioDeHorario =
    !props.actividad ||
    props.actividad.fecha_programada !== f.fecha_programada ||
    props.actividad.hora_programada?.slice(0, 5) !== f.hora_programada
  if (cambioDeHorario) {
    if (f.fecha_programada < hoy.value || (f.fecha_programada === hoy.value && f.hora_programada < horaActual.value)) {
      return 'No se pueden programar actividades en el pasado.'
    }
    if (f.fecha_programada > fechaMax.value) return 'Solo se pueden programar actividades hasta dentro de un año.'
  }
  if (tipo.value !== 'alimentacion') {
    if (f.duracion_horas < 0 || f.duracion_minutos < 0 || f.duracion_minutos > 59) {
      return 'La duración debe tener horas no negativas y minutos entre 0 y 59.'
    }
    if (tipo.value !== 'enriquecimiento' && minutosTotales.value <= 0) return 'La duración estimada debe ser mayor que cero.'
    if (minutosTotales.value > duracionMax.value) {
      return `La duración máxima de una actividad es de ${duracionMax.value / 60} horas.`
    }
  }
  if (tipo.value === 'limpieza') {
    if (!f.id_recinto) return 'Selecciona un recinto o área.'
  } else if (!f.id_animal) {
    return 'Selecciona un ejemplar.'
  }
  if (tipo.value === 'enriquecimiento' && !f.descripcion_estimulo.trim()) return 'Describe el estímulo del enriquecimiento.'
  if (tipo.value === 'entrenamiento') {
    if (!f.objetivo_entrenamiento.trim()) return 'Indica el objetivo del entrenamiento.'
    if (!f.tipo_refuerzo.trim()) return 'Indica el tipo de refuerzo.'
    if (f.tipo_refuerzo.length > 150) return 'El tipo de refuerzo admite hasta 150 caracteres.'
  }
  if (!editando.value && rep.modo !== 'no') {
    if (rep.modo === 'dias' && !rep.dias.length) return 'Elige al menos un día de la semana para repetir.'
    if (rep.termina === 'fecha') {
      if (!rep.hasta) return 'Indica hasta qué fecha se repite.'
      if (rep.hasta < f.fecha_programada) return 'La fecha de fin de la repetición no puede ser anterior al primer día.'
      if (rep.hasta > hastaMax.value) return `La repetición puede durar como máximo ${mesesMax.value} meses.`
    }
  }
  return ''
}

// ---- Guardar ----

function datosComunes() {
  const observaciones = f.observaciones.trim() || undefined
  const duracion = { duracion_horas: Number(f.duracion_horas) || 0, duracion_minutos: Number(f.duracion_minutos) || 0 }
  if (tipo.value === 'enriquecimiento') {
    return {
      id_animal: f.id_animal,
      tipo_enriquecimiento: f.tipo_enriquecimiento,
      descripcion_estimulo: f.descripcion_estimulo.trim(),
      observaciones,
      ...duracion,
    }
  }
  if (tipo.value === 'entrenamiento') {
    return {
      id_animal: f.id_animal,
      objetivo_entrenamiento: f.objetivo_entrenamiento.trim(),
      tipo_refuerzo: f.tipo_refuerzo.trim(),
      observaciones,
      ...duracion,
    }
  }
  return { id_recinto: f.id_recinto, observaciones, ...duracion }
}

async function crear(permitirCruce: boolean): Promise<[Actividad, number]> {
  if (rep.modo !== 'no') {
    const base = { ...datosComunes(), fecha_programada: f.fecha_programada, hora_programada: f.hora_programada }
    const lista = await actividadesApi.crearRepetida(
      {
        tipo_actividad: tipo.value,
        ...base,
        repeticion: {
          dias_semana: rep.modo === 'dias' ? rep.dias : null,
          ...(rep.termina === 'fecha' ? { fecha_fin: rep.hasta } : { meses: rep.meses }),
        },
      },
      permitirCruce,
    )
    return [lista[0]!, lista.length]
  }
  if (tipo.value === 'enriquecimiento') {
    return [
      await actividadesApi.programarEnriquecimiento(
        {
          id_animal: f.id_animal,
          tipo_enriquecimiento: f.tipo_enriquecimiento,
          descripcion_estimulo: f.descripcion_estimulo.trim(),
          fecha_programada: f.fecha_programada,
          hora_programada: f.hora_programada,
          duracion_horas: Number(f.duracion_horas) || 0,
          duracion_minutos: Number(f.duracion_minutos) || 0,
          observaciones: f.observaciones.trim() || undefined,
        },
        permitirCruce,
      ),
      1,
    ]
  }
  if (tipo.value === 'entrenamiento') {
    return [
      await actividadesApi.programarEntrenamiento(
        {
          id_animal: f.id_animal,
          fecha_programada: f.fecha_programada,
          hora_programada: f.hora_programada,
          duracion_horas: Number(f.duracion_horas) || 0,
          duracion_minutos: Number(f.duracion_minutos) || 0,
          objetivo_entrenamiento: f.objetivo_entrenamiento.trim(),
          tipo_refuerzo: f.tipo_refuerzo.trim(),
          observaciones: f.observaciones.trim() || undefined,
        },
        permitirCruce,
      ),
      1,
    ]
  }
  return [
    await actividadesApi.programarLimpieza(
      {
        id_recinto: f.id_recinto,
        fecha_programada: f.fecha_programada,
        hora_programada: f.hora_programada,
        duracion_horas: Number(f.duracion_horas) || 0,
        duracion_minutos: Number(f.duracion_minutos) || 0,
        observaciones: f.observaciones.trim() || undefined,
      },
      permitirCruce,
    ),
    1,
  ]
}

function cambiosDeEdicion(): ActividadCambios {
  const cambios: ActividadCambios = {
    fecha_programada: f.fecha_programada,
    hora_programada: f.hora_programada,
    observaciones: f.observaciones.trim() || null,
  }
  if (tipo.value !== 'alimentacion') {
    cambios.duracion_horas = Number(f.duracion_horas) || 0
    cambios.duracion_minutos = Number(f.duracion_minutos) || 0
  }
  if (tipo.value === 'enriquecimiento') {
    cambios.tipo_enriquecimiento = f.tipo_enriquecimiento
    cambios.descripcion_estimulo = f.descripcion_estimulo.trim()
  }
  if (tipo.value === 'entrenamiento') {
    cambios.objetivo_entrenamiento = f.objetivo_entrenamiento.trim()
    cambios.tipo_refuerzo = f.tipo_refuerzo.trim()
  }
  return cambios
}

async function guardar(permitirCruce = false) {
  error.value = validar()
  if (error.value) return
  guardando.value = true
  try {
    if (props.actividad) {
      emit('editada', await actividadesApi.editar(props.actividad.id_actividad, cambiosDeEdicion(), permitirCruce))
    } else {
      const [actividad, cantidad] = await crear(permitirCruce)
      emit('creada', actividad, cantidad)
    }
    cruces.value = null
  } catch (e) {
    const conflictos = crucesDeError(e)
    if (conflictos) cruces.value = conflictos
    else error.value = e instanceof ApiError ? e.message : 'No se pudo guardar la actividad.'
  } finally {
    guardando.value = false
  }
}

const nombreAnimal = (a: AnimalReferencia) => (a.nombre ? `${a.nombre} · ${a.taxonomia.nombre_comun}` : a.taxonomia.nombre_comun)
const textoCruce = (c: CruceHorario) => {
  const dia = deIso(c.fecha_programada)
  const fecha = `${diaCorto(c.fecha_programada)} ${dia.getDate()}/${dia.getMonth() + 1}`
  return `${TIPO_LABEL[c.tipo_actividad]} · ${fecha} ${c.hora_programada ?? ''}${c.duracion_minutos ? ` (${c.duracion_minutos} min)` : ''}`
}
const textoBoton = computed(() => {
  if (guardando.value) return 'Guardando…'
  if (editando.value) return 'Guardar cambios'
  return rep.modo === 'no' ? 'Crear actividad' : 'Crear repetición'
})
</script>

<template>
  <form class="panel" :class="`t-${tipo}`" :aria-label="editando ? 'Editar actividad' : 'Crear actividad'" @submit.prevent="guardar()">
    <header class="p-h">
      <span class="p-ico"><IconoTipo :tipo="tipo" /></span>
      <div class="p-tit">
        <!-- El día y la hora se eligen (y se ven) en los campos de abajo -->
        <h3>{{ editando ? `Editar ${TIPO_LABEL[tipo].toLowerCase()}` : 'Crear actividad' }}</h3>
      </div>
      <button class="cerrar" type="button" aria-label="Cerrar panel" @click="emit('close')">×</button>
    </header>

    <div class="p-b">
      <template v-if="!editando">
        <div class="tipos" role="radiogroup" aria-label="Tipo de actividad">
          <button
            v-for="t in TIPOS"
            :key="t"
            type="button"
            role="radio"
            :class="[`t-${t}`, { on: tipo === t }]"
            :aria-checked="tipo === t"
            @click="tipo = t"
          >
            <IconoTipo :tipo="t" />{{ TIPO_LABEL[t] }}
          </button>
        </div>
        <p class="info">Las alimentaciones se generan solas desde Registro de Dietas.</p>

        <div v-if="tipo === 'limpieza'" class="field">
          <label for="crear-recinto">Recinto o área</label>
          <select id="crear-recinto" v-model.number="f.id_recinto" class="input">
            <option v-for="r in recintos" :key="r.id_recinto" :value="r.id_recinto">
              {{ r.nombre_recinto }}{{ r.tipo ? ` · ${r.tipo}` : '' }}
            </option>
          </select>
        </div>
        <div v-else class="field">
          <label for="crear-animal">Ejemplar</label>
          <select id="crear-animal" v-model.number="f.id_animal" class="input">
            <option v-for="a in animales" :key="a.id_animal" :value="a.id_animal">{{ nombreAnimal(a) }}</option>
          </select>
        </div>
      </template>

      <div class="dos">
        <div class="field">
          <label for="crear-fecha">Día</label>
          <input id="crear-fecha" v-model="f.fecha_programada" class="input" type="date" :min="hoy" :max="fechaMax" />
        </div>
        <div class="field">
          <label for="crear-hora">Hora</label>
          <input id="crear-hora" v-model="f.hora_programada" class="input" type="time" :min="horaMin" />
        </div>
      </div>

      <template v-if="tipo === 'enriquecimiento'">
        <div class="field">
          <label for="crear-tipo-enr">Tipo de enriquecimiento</label>
          <select id="crear-tipo-enr" v-model="f.tipo_enriquecimiento" class="input">
            <option v-for="(label, valor) in TIPOS_ENRIQUECIMIENTO" :key="valor" :value="valor">{{ label }}</option>
          </select>
        </div>
        <div class="field">
          <label for="crear-estimulo">Descripción del estímulo</label>
          <textarea id="crear-estimulo" v-model="f.descripcion_estimulo" class="input" rows="2" />
        </div>
      </template>

      <template v-if="tipo === 'entrenamiento'">
        <div class="field">
          <label for="crear-objetivo">Objetivo</label>
          <input id="crear-objetivo" v-model="f.objetivo_entrenamiento" class="input" />
        </div>
        <div class="field">
          <label for="crear-refuerzo">Tipo de refuerzo</label>
          <input id="crear-refuerzo" v-model="f.tipo_refuerzo" class="input" maxlength="150" />
        </div>
      </template>

      <div v-if="tipo !== 'alimentacion'" class="field">
        <span class="lbl">Duración estimada (máx. {{ duracionMax / 60 }} h)</span>
        <div class="duracion">
          <input v-model.number="f.duracion_horas" class="input" type="number" min="0" :max="Math.floor(duracionMax / 60)" aria-label="Horas de duración" />
          <span>h</span>
          <input v-model.number="f.duracion_minutos" class="input" type="number" min="0" max="59" aria-label="Minutos de duración" />
          <span>min</span>
        </div>
      </div>

      <!-- Repetición (solo al crear) -->
      <div v-if="!editando" class="field repetir">
        <label for="crear-repetir">Repetir</label>
        <select id="crear-repetir" v-model="rep.modo" class="input">
          <option value="no">No se repite</option>
          <option value="diario">Todos los días</option>
          <option value="dias">Ciertos días de la semana</option>
        </select>

        <div v-if="rep.modo === 'dias'" class="dias" role="group" aria-label="Días de la semana">
          <button
            v-for="(letra, i) in DIAS_SEMANA"
            :key="i"
            type="button"
            :class="{ on: rep.dias.includes(i) }"
            :aria-pressed="rep.dias.includes(i)"
            :aria-label="NOMBRES_DIAS[i]"
            :title="NOMBRES_DIAS[i]"
            @click="alternarDia(i)"
          >
            {{ letra }}
          </button>
        </div>

        <div v-if="rep.modo !== 'no'" class="termina">
          <label class="opcion">
            <input v-model="rep.termina" type="radio" value="fecha" />
            Hasta el
            <input v-model="rep.hasta" class="input" type="date" :min="f.fecha_programada" :max="hastaMax" :disabled="rep.termina !== 'fecha'" aria-label="Fecha de fin de la repetición" />
          </label>
          <label class="opcion">
            <input v-model="rep.termina" type="radio" value="meses" />
            Durante
            <select v-model.number="rep.meses" class="input" :disabled="rep.termina !== 'meses'" aria-label="Meses de repetición">
              <option v-for="m in mesesMax" :key="m" :value="m">{{ m }} {{ m === 1 ? 'mes' : 'meses' }}</option>
            </select>
          </label>
        </div>
      </div>

      <div class="field">
        <label for="crear-nota">Nota</label>
        <input id="crear-nota" v-model="f.observaciones" class="input" />
      </div>

      <!-- Cruce de horario: se pregunta antes de guardar -->
      <div v-if="cruces" class="aviso-cruce" role="alert">
        <strong>Se cruza en horario con:</strong>
        <ul>
          <li v-for="c in cruces.slice(0, 5)" :key="c.id_actividad">{{ textoCruce(c) }}</li>
          <li v-if="cruces.length > 5">y {{ cruces.length - 5 }} más</li>
        </ul>
        <p>¿Quieres {{ editando ? 'guardarla' : 'crearla' }} igual?</p>
        <div class="aviso-acciones">
          <button class="btn btn-secondary" type="button" @click="cruces = null">Cambiar horario</button>
          <button class="btn btn-primary" type="button" :disabled="guardando" @click="guardar(true)">
            {{ editando ? 'Guardar igual' : 'Crear igual' }}
          </button>
        </div>
      </div>

      <p v-if="error" class="alert-error" role="alert">{{ error }}</p>
    </div>

    <footer class="p-f">
      <button class="btn btn-secondary" type="button" @click="emit('close')">Cancelar</button>
      <button class="btn btn-primary" type="submit" :disabled="guardando || !!cruces">{{ textoBoton }}</button>
    </footer>
  </form>
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
}

.p-tit h3 {
  font-size: 16px;
  font-weight: 700;
}

.p-tit p {
  margin-top: 3px;
  font-size: 12.5px;
  color: var(--color-text-muted);
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
  gap: 12px;
  overflow-y: auto;
  padding: 14px 18px;
}

.p-f {
  display: flex;
  gap: 8px;
  padding: 12px 18px 16px;
  border-top: 1px solid var(--color-border);
}

.p-f .btn {
  flex: 1;
}

.tipos {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.tipos button {
  display: grid;
  justify-items: center;
  gap: 4px;
  padding: 9px 4px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.tipos button.on {
  border-color: var(--c);
  background: var(--cb);
  color: var(--c);
}

.info {
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-alt);
  font-size: 12px;
  color: var(--color-text-muted);
}

.dos {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.lbl {
  font-size: 12px;
  color: var(--color-text-muted);
}

.duracion {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.input {
  padding: 9px 11px;
}

/* ---- Repetición ---- */
.repetir {
  gap: 8px;
}

.dias {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.dias button {
  height: 32px;
  border: 1px solid var(--color-border-strong);
  border-radius: 50%;
  background: var(--color-surface);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.dias button.on {
  border-color: var(--c);
  background: var(--c);
  color: #fff;
}

.termina {
  display: grid;
  gap: 6px;
}

.opcion {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.opcion input[type='radio'] {
  accent-color: var(--color-primary);
}

.opcion .input {
  padding: 6px 9px;
}

/* ---- Aviso de cruce de horario ---- */
.aviso-cruce {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border: 1px solid #e6c98a;
  border-radius: var(--radius-md);
  background: #fbf1da;
  font-size: 13px;
}

.aviso-cruce ul {
  margin: 0;
  padding-left: 18px;
  color: var(--color-text-muted);
}

.aviso-acciones {
  display: flex;
  gap: 8px;
}

.aviso-acciones .btn {
  flex: 1;
  padding: 7px 10px;
}
</style>
