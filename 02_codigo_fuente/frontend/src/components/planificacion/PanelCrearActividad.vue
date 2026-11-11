<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import IconoTipo from '@/components/planificacion/IconoTipo.vue'
import { actividadesApi } from '@/api/actividades'
import { ApiError } from '@/api/http'
import { TIPOS_ENRIQUECIMIENTO, TIPO_LABEL, diaLargo } from '@/config/actividades'
import type { Actividad, TipoActividad, TipoEnriquecimiento } from '@/types/actividades'
import type { Animal, Recinto } from '@/types/animales'

type TipoCreable = Exclude<TipoActividad, 'alimentacion'>

// Crear una actividad desde el panel derecho del calendario.
// Las alimentaciones no se crean aquí: salen de la dieta (Registro de Dietas).
const props = defineProps<{
  animales: Animal[]
  recintos: Recinto[]
  fecha: string
  hora: string
  idAnimal?: number
}>()
const emit = defineEmits<{
  close: []
  creada: [actividad: Actividad]
  // Para dibujar el bloque punteado en el calendario mientras se llena
  borrador: [datos: { fecha: string; hora: string; minutos: number }]
}>()

const TIPOS: TipoCreable[] = ['enriquecimiento', 'entrenamiento', 'limpieza']
const tipo = ref<TipoCreable>('enriquecimiento')
const guardando = ref(false)
const error = ref('')
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

watch(
  () => [props.fecha, props.hora, props.idAnimal] as const,
  ([fecha, hora, idAnimal]) => {
    f.fecha_programada = fecha
    f.hora_programada = hora || '08:00'
    f.id_animal = idAnimal || props.animales[0]?.id_animal || 0
    f.id_recinto = f.id_recinto || props.recintos[0]?.id_recinto || 0
    error.value = ''
  },
  { immediate: true },
)

watch(
  () => [f.fecha_programada, f.hora_programada, f.duracion_horas, f.duracion_minutos, tipo.value] as const,
  () => {
    // El enriquecimiento no tiene duración en la base: se dibuja con 45 min de referencia
    const minutos = tipo.value === 'enriquecimiento' ? 45 : f.duracion_horas * 60 + f.duracion_minutos
    emit('borrador', { fecha: f.fecha_programada, hora: f.hora_programada, minutos })
  },
  { immediate: true },
)

// Mismas reglas que el formulario anterior; además la limpieza ahora lleva hora
function validar(): string {
  if (!f.fecha_programada) return 'Selecciona un día para la actividad.'
  if (!f.hora_programada) return 'Indica la hora de la actividad.'
  if (tipo.value !== 'enriquecimiento' && (f.duracion_horas < 0 || f.duracion_minutos < 0 || f.duracion_minutos > 59)) {
    return 'La duración debe tener horas no negativas y minutos entre 0 y 59.'
  }
  if (tipo.value !== 'enriquecimiento' && f.duracion_horas * 60 + f.duracion_minutos <= 0) {
    return 'La duración estimada debe ser mayor que cero.'
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
  return ''
}

async function guardar() {
  error.value = validar()
  if (error.value) return
  guardando.value = true
  try {
    const observaciones = f.observaciones.trim() || undefined
    let actividad: Actividad
    if (tipo.value === 'enriquecimiento') {
      actividad = await actividadesApi.programarEnriquecimiento({
        id_animal: f.id_animal,
        tipo_enriquecimiento: f.tipo_enriquecimiento,
        fecha_programada: f.fecha_programada,
        hora_programada: f.hora_programada,
        descripcion_estimulo: f.descripcion_estimulo.trim(),
        observaciones,
      })
    } else if (tipo.value === 'entrenamiento') {
      actividad = await actividadesApi.programarEntrenamiento({
        id_animal: f.id_animal,
        fecha_programada: f.fecha_programada,
        hora_programada: f.hora_programada,
        duracion_horas: f.duracion_horas,
        duracion_minutos: f.duracion_minutos,
        objetivo_entrenamiento: f.objetivo_entrenamiento.trim(),
        tipo_refuerzo: f.tipo_refuerzo.trim(),
        observaciones,
      })
    } else {
      actividad = await actividadesApi.programarLimpieza({
        id_recinto: f.id_recinto,
        fecha_programada: f.fecha_programada,
        hora_programada: f.hora_programada,
        duracion_horas: f.duracion_horas,
        duracion_minutos: f.duracion_minutos,
        observaciones,
      })
    }
    emit('creada', actividad)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo guardar la actividad.'
  } finally {
    guardando.value = false
  }
}

const nombreAnimal = (a: Animal) => (a.nombre ? `${a.nombre} · ${a.taxonomia.nombre_comun}` : a.taxonomia.nombre_comun)
</script>

<template>
  <form class="panel" :class="`t-${tipo}`" aria-label="Crear actividad" @submit.prevent="guardar">
    <header class="p-h">
      <span class="p-ico"><IconoTipo :tipo="tipo" /></span>
      <div class="p-tit">
        <h3>Crear actividad</h3>
        <p>{{ f.fecha_programada ? diaLargo(f.fecha_programada) : 'Elige el día' }}{{ f.hora_programada ? ` · ${f.hora_programada}` : '' }}</p>
      </div>
      <button class="cerrar" type="button" aria-label="Cerrar panel" @click="emit('close')">×</button>
    </header>

    <div class="p-b">
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

      <div class="dos">
        <div class="field">
          <label for="crear-fecha">Día</label>
          <input id="crear-fecha" v-model="f.fecha_programada" class="input" type="date" />
        </div>
        <div class="field">
          <label for="crear-hora">Hora</label>
          <input id="crear-hora" v-model="f.hora_programada" class="input" type="time" />
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

      <div v-if="tipo !== 'enriquecimiento'" class="field">
        <span class="lbl">Duración estimada</span>
        <div class="duracion">
          <input v-model.number="f.duracion_horas" class="input" type="number" min="0" max="32767" aria-label="Horas de duración" />
          <span>h</span>
          <input v-model.number="f.duracion_minutos" class="input" type="number" min="0" max="59" aria-label="Minutos de duración" />
          <span>min</span>
        </div>
      </div>

      <div class="field">
        <label for="crear-nota">Nota</label>
        <input id="crear-nota" v-model="f.observaciones" class="input" />
      </div>

      <p v-if="error" class="alert-error" role="alert">{{ error }}</p>
    </div>

    <footer class="p-f">
      <button class="btn btn-secondary" type="button" @click="emit('close')">Cancelar</button>
      <button class="btn btn-primary" type="submit" :disabled="guardando">{{ guardando ? 'Guardando…' : 'Crear actividad' }}</button>
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
</style>
