<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { ApiError } from '@/api/http'
import { veterinariaApi } from '@/api/veterinaria'
import { hoyIso } from '@/config/animales'
import type {
  Diagnostico,
  DiagnosticoCreate,
  SignosVitales,
  SignosVitalesCreate,
  Tratamiento,
  TratamientoCreate,
  UnidadFrecuenciaTratamiento,
} from '@/types/veterinaria'

type RegistroExistente =
  | { tipo: 'diagnostico'; datos: Diagnostico }
  | { tipo: 'tratamiento'; datos: Tratamiento }

type ValorNumerico = string | number
type MedicamentoForm = { nombre_medicamento: string; dosis_ml: ValorNumerico }
type CampoSigno = Exclude<keyof SignosVitales, 'id_signos_vitales' | 'id_diagnostico'>

const props = defineProps<{
  open: boolean
  idAnimal: number
  // Nombre que se muestra en el subtítulo ("Ejemplar: Ayni")
  nombreEjemplar?: string
  diagnosticos: Diagnostico[]
  registro?: RegistroExistente | null
  tipoInicial?: 'diagnostico' | 'tratamiento'
}>()

const emit = defineEmits<{ close: []; saved: [] }>()
const tipo = ref<'diagnostico' | 'tratamiento'>('diagnostico')
const pestanaTratamiento = ref<'datos' | 'medicamentos'>('datos')
const error = ref('')
const guardando = ref(false)
const tratamientoGuardadoSinActividades = ref(false)
const formDiagnostico = reactive({ diagnostico: '', observaciones: '', es_critico: false })
const formSignos = reactive({
  peso_kg: '' as ValorNumerico,
  temperatura_c: '' as ValorNumerico,
  frecuencia_cardiaca_lpm: '' as ValorNumerico,
  frecuencia_respiratoria_rpm: '' as ValorNumerico,
  tiempo_llenado_capilar_s: '' as ValorNumerico,
  hidratacion: '' as SignosVitalesCreate['hidratacion'] | '',
  condicion_corporal: '' as ValorNumerico,
  mucosas: '' as SignosVitalesCreate['mucosas'] | '',
  actitud: '' as SignosVitalesCreate['actitud'] | '',
})
const formTratamiento = reactive({
  id_diagnostico: 0,
  descripcion: '',
  frecuencia_valor: '1' as ValorNumerico,
  frecuencia_unidad: 'dias' as UnidadFrecuenciaTratamiento | '',
  hora_inicio: '08:00',
  fecha_inicio: hoyIso(),
  fecha_fin: '',
  estado: 'en_curso' as Tratamiento['estado'],
  medicamentos: [] as MedicamentoForm[],
})

const TIPOS = [
  { valor: 'diagnostico', label: 'Diagnóstico' },
  { valor: 'tratamiento', label: 'Tratamiento' },
] as const

const HIDRATACION = {
  normal: 'Normal',
  deshidratacion_leve: 'Deshidratación leve',
  deshidratacion_moderada: 'Deshidratación moderada',
  deshidratacion_severa: 'Deshidratación severa',
}
const CONDICION = { 1: 'Caquéctico', 2: 'Delgado', 3: 'Óptimo', 4: 'Sobrepeso', 5: 'Obeso' } as Record<number, string>
const MUCOSAS = {
  rosadas: 'Rosadas',
  palidas: 'Pálidas',
  cianoticas: 'Cianóticas',
  ictericas: 'Ictéricas',
  congestionadas: 'Congestionadas',
}
const ACTITUD = { alerta: 'Alerta', deprimido: 'Deprimido', estuporoso: 'Estuporoso', agitado: 'Agitado' }

const editando = computed(() => !!props.registro)
const tratamientoLegado = computed(() =>
  props.registro?.tipo === 'tratamiento' ? props.registro.datos : null,
)
const diagnosticosOrdenados = computed(() =>
  [...props.diagnosticos].sort(
    (a, b) => new Date(b.fecha_registro).getTime() - new Date(a.fecha_registro).getTime(),
  ),
)

// Último valor registrado de cada signo (el más reciente que no esté vacío), para usarlo de referencia
const ultimos = computed(() => {
  const resultado: Partial<Record<CampoSigno, string>> = {}
  const numero = (valor: number, decimales: number) =>
    new Intl.NumberFormat('es-EC', { maximumFractionDigits: decimales }).format(valor)
  for (const d of diagnosticosOrdenados.value) {
    const s = d.signos_vitales
    if (!s) continue
    if (s.peso_kg !== null) resultado.peso_kg ??= `${numero(s.peso_kg, 3)} kg`
    if (s.temperatura_c !== null) resultado.temperatura_c ??= `${numero(s.temperatura_c, 1)} °C`
    if (s.frecuencia_cardiaca_lpm !== null) resultado.frecuencia_cardiaca_lpm ??= `${s.frecuencia_cardiaca_lpm} lpm`
    if (s.frecuencia_respiratoria_rpm !== null) {
      resultado.frecuencia_respiratoria_rpm ??= `${s.frecuencia_respiratoria_rpm} rpm`
    }
    if (s.tiempo_llenado_capilar_s !== null) {
      resultado.tiempo_llenado_capilar_s ??= `${numero(s.tiempo_llenado_capilar_s, 1)} s`
    }
    if (s.hidratacion) resultado.hidratacion ??= HIDRATACION[s.hidratacion]
    if (s.condicion_corporal !== null) {
      resultado.condicion_corporal ??= `${s.condicion_corporal} · ${CONDICION[s.condicion_corporal] ?? ''}`
    }
    if (s.mucosas) resultado.mucosas ??= MUCOSAS[s.mucosas]
    if (s.actitud) resultado.actitud ??= ACTITUD[s.actitud]
  }
  return resultado
})

const hayUltimos = computed(() => Object.keys(ultimos.value).length > 0)

function referencia(campo: CampoSigno, vacio = '—') {
  const valor = ultimos.value[campo]
  return valor ? `Último: ${valor}` : vacio
}

// Los signos se guardan si se llenó al menos uno; si no, el diagnóstico va sin signos
const haySignos = computed(() =>
  Object.values(formSignos).some((valor) => valor !== '' && valor !== null),
)

function numeroOpcional(
  valor: ValorNumerico,
  campo: string,
  opciones: { minimo?: number; maximo?: number; decimales?: number; entero?: boolean } = {},
): number | null {
  if (valor === '') return null
  if (typeof valor === 'string' && /^\s*$/u.test(valor)) {
    throw new Error(`${campo}: ingresa un valor numérico válido.`)
  }

  const numero = typeof valor === 'number' ? valor : Number(valor)
  if (!Number.isFinite(numero)) {
    throw new Error(`${campo}: ingresa un valor numérico válido.`)
  }
  if (opciones.minimo !== undefined && numero < opciones.minimo) {
    throw new Error(`${campo}: el valor debe ser mayor o igual a ${opciones.minimo}.`)
  }
  if (opciones.maximo !== undefined && numero > opciones.maximo) {
    throw new Error(`${campo}: el valor no puede ser mayor que ${opciones.maximo}.`)
  }
  if (opciones.entero && !Number.isInteger(numero)) {
    throw new Error(`${campo}: ingresa un número entero.`)
  }
  if (
    opciones.decimales !== undefined &&
    Math.abs(numero * 10 ** opciones.decimales - Math.round(numero * 10 ** opciones.decimales)) > 1e-8
  ) {
    throw new Error(
      `${campo}: admite hasta ${opciones.decimales} decimal${opciones.decimales === 1 ? '' : 'es'}.`,
    )
  }
  return numero
}

watch(
  () => [props.open, props.registro] as const,
  ([abierto]) => {
    if (!abierto) return
    error.value = ''
    tratamientoGuardadoSinActividades.value = false
    pestanaTratamiento.value = 'datos'
    tipo.value = props.registro?.tipo ?? props.tipoInicial ?? 'diagnostico'
    const signosExistentes =
      props.registro?.tipo === 'diagnostico' ? props.registro.datos.signos_vitales : null
    Object.assign(formDiagnostico, {
      diagnostico: props.registro?.tipo === 'diagnostico' ? props.registro.datos.diagnostico : '',
      observaciones:
        props.registro?.tipo === 'diagnostico' ? (props.registro.datos.observaciones ?? '') : '',
      es_critico: props.registro?.tipo === 'diagnostico' ? props.registro.datos.es_critico : false,
    })
    Object.assign(formSignos, {
      peso_kg: signosExistentes?.peso_kg ?? '',
      temperatura_c: signosExistentes?.temperatura_c ?? '',
      frecuencia_cardiaca_lpm: signosExistentes?.frecuencia_cardiaca_lpm ?? '',
      frecuencia_respiratoria_rpm: signosExistentes?.frecuencia_respiratoria_rpm ?? '',
      tiempo_llenado_capilar_s: signosExistentes?.tiempo_llenado_capilar_s ?? '',
      hidratacion: signosExistentes?.hidratacion ?? '',
      condicion_corporal: signosExistentes?.condicion_corporal ?? '',
      mucosas: signosExistentes?.mucosas ?? '',
      actitud: signosExistentes?.actitud ?? '',
    })
    Object.assign(formTratamiento, {
      id_diagnostico:
        props.registro?.tipo === 'tratamiento'
          ? props.registro.datos.id_diagnostico
          : (diagnosticosOrdenados.value[0]?.id_diagnostico ?? 0),
      descripcion:
        props.registro?.tipo === 'tratamiento' ? props.registro.datos.descripcion : '',
      frecuencia_valor:
        props.registro?.tipo === 'tratamiento'
          ? String(props.registro.datos.frecuencia_valor ?? '')
          : '1',
      frecuencia_unidad:
        props.registro?.tipo === 'tratamiento'
          ? (props.registro.datos.frecuencia_unidad ?? '')
          : 'dias',
      hora_inicio:
        props.registro?.tipo === 'tratamiento'
          ? (props.registro.datos.hora_inicio?.slice(0, 5) ?? '')
          : '08:00',
      fecha_inicio: props.registro?.tipo === 'tratamiento' ? props.registro.datos.fecha_inicio : hoyIso(),
      fecha_fin: props.registro?.tipo === 'tratamiento' ? (props.registro.datos.fecha_fin ?? '') : '',
      estado: props.registro?.tipo === 'tratamiento' ? props.registro.datos.estado : 'en_curso',
      medicamentos:
        props.registro?.tipo === 'tratamiento'
          ? props.registro.datos.medicamentos.map((medicamento) => ({
              nombre_medicamento: medicamento.nombre_medicamento,
              dosis_ml: String(medicamento.dosis_ml),
            }))
          : [],
    })
  },
)

function agregarMedicamento() {
  formTratamiento.medicamentos.push({ nombre_medicamento: '', dosis_ml: '' })
}

function quitarMedicamento(indice: number) {
  formTratamiento.medicamentos.splice(indice, 1)
}

async function guardar() {
  error.value = ''
  guardando.value = true
  try {
    if (tipo.value === 'diagnostico') {
      if (!formDiagnostico.diagnostico.trim()) {
        error.value = 'Ingresa el motivo o título del diagnóstico.'
        return
      }

      let signosVitales: SignosVitalesCreate | null | undefined
      if (haySignos.value) {
        signosVitales = {
          peso_kg: numeroOpcional(formSignos.peso_kg, 'Peso', { minimo: 0.001, decimales: 3 }),
          temperatura_c: numeroOpcional(formSignos.temperatura_c, 'Temperatura', {
            minimo: 0,
            maximo: 60,
            decimales: 1,
          }),
          frecuencia_cardiaca_lpm: numeroOpcional(
            formSignos.frecuencia_cardiaca_lpm,
            'Frecuencia cardíaca',
            { minimo: 1, entero: true },
          ),
          frecuencia_respiratoria_rpm: numeroOpcional(
            formSignos.frecuencia_respiratoria_rpm,
            'Frecuencia respiratoria',
            { minimo: 1, entero: true },
          ),
          tiempo_llenado_capilar_s: numeroOpcional(
            formSignos.tiempo_llenado_capilar_s,
            'Llenado capilar',
            { minimo: 0.1, decimales: 1 },
          ),
          hidratacion: formSignos.hidratacion || null,
          condicion_corporal: numeroOpcional(formSignos.condicion_corporal, 'Condición corporal', {
            minimo: 1,
            maximo: 5,
            entero: true,
          }),
          mucosas: formSignos.mucosas || null,
          actitud: formSignos.actitud || null,
        }
      } else if (props.registro?.tipo === 'diagnostico' && props.registro.datos.signos_vitales) {
        // Se vaciaron todos los signos de un registro que sí los tenía: se eliminan
        signosVitales = null
      }

      const datos: DiagnosticoCreate = {
        diagnostico: formDiagnostico.diagnostico.trim(),
        observaciones: formDiagnostico.observaciones.trim() || null,
        es_critico: formDiagnostico.es_critico,
        ...(signosVitales !== undefined ? { signos_vitales: signosVitales } : {}),
      }
      if (props.registro?.tipo === 'diagnostico') {
        await veterinariaApi.actualizarDiagnostico(props.registro.datos.id_diagnostico, datos)
      } else {
        await veterinariaApi.crearDiagnostico(props.idAnimal, datos)
      }
    } else {
      if (!formTratamiento.id_diagnostico) {
        pestanaTratamiento.value = 'datos'
        error.value = 'Selecciona el diagnóstico asociado'
        return
      }
      if (tratamientoGuardadoSinActividades.value) return
      const descripcion = formTratamiento.descripcion.trim()
      if (!descripcion) {
        pestanaTratamiento.value = 'datos'
        error.value = 'Ingresa la descripción del tratamiento.'
        return
      }
      if (!formTratamiento.fecha_inicio) {
        pestanaTratamiento.value = 'datos'
        error.value = 'Ingresa la fecha de inicio del tratamiento.'
        return
      }
      if (formTratamiento.fecha_fin && formTratamiento.fecha_fin < formTratamiento.fecha_inicio) {
        pestanaTratamiento.value = 'datos'
        error.value = 'La fecha de fin no puede ser anterior a la fecha de inicio.'
        return
      }
      pestanaTratamiento.value = 'datos'
      const frecuenciaValor = numeroOpcional(formTratamiento.frecuencia_valor, 'Frecuencia', {
        minimo: 1,
        maximo: 2147483647,
        entero: true,
      })
      if (frecuenciaValor === null) {
        pestanaTratamiento.value = 'datos'
        error.value = 'Ingresa una frecuencia válida.'
        return
      }
      if (!formTratamiento.frecuencia_unidad || !formTratamiento.hora_inicio) {
        pestanaTratamiento.value = 'datos'
        error.value = 'Selecciona la unidad y la hora de inicio de la frecuencia.'
        return
      }
      const medicamentos = formTratamiento.medicamentos.map((medicamento, indice) => {
        const nombre = medicamento.nombre_medicamento.trim()
        if (!nombre) {
          pestanaTratamiento.value = 'medicamentos'
          throw new Error(`Medicamento ${indice + 1}: ingresa el nombre.`)
        }
        const dosis = numeroOpcional(medicamento.dosis_ml, `Dosis del medicamento ${indice + 1}`, {
          minimo: 0.01,
          decimales: 2,
        })
        if (dosis === null) {
          pestanaTratamiento.value = 'medicamentos'
          throw new Error(`Medicamento ${indice + 1}: ingresa la dosis en ml.`)
        }
        return { nombre_medicamento: nombre, dosis_ml: dosis }
      })
      const datos: TratamientoCreate = {
        descripcion,
        frecuencia_valor: frecuenciaValor,
        frecuencia_unidad: formTratamiento.frecuencia_unidad,
        hora_inicio: formTratamiento.hora_inicio,
        medicamentos,
        fecha_inicio: formTratamiento.fecha_inicio,
        fecha_fin: formTratamiento.fecha_fin || null,
        estado: formTratamiento.estado,
      }
      let idTratamiento: number
      if (props.registro?.tipo === 'tratamiento') {
        const tratamiento = await veterinariaApi.actualizarTratamiento(
          props.registro.datos.id_tratamiento,
          datos,
        )
        idTratamiento = tratamiento.id_tratamiento
      } else {
        const tratamiento = await veterinariaApi.crearTratamiento(
          formTratamiento.id_diagnostico,
          datos,
        )
        idTratamiento = tratamiento.id_tratamiento
      }
      try {
        await veterinariaApi.generarActividadesTratamiento(idTratamiento)
      } catch (e) {
        tratamientoGuardadoSinActividades.value = true
        error.value =
          `El tratamiento se guardó, pero no se pudieron generar sus actividades: ` +
          (e instanceof ApiError
            ? e.message
            : e instanceof Error
              ? e.message
              : 'error desconocido')
        emit('saved')
        return
      }
    }
    emit('saved')
    emit('close')
  } catch (e) {
    error.value =
      e instanceof ApiError
        ? e.message
        : e instanceof Error
          ? e.message
          : 'No se pudo guardar el registro clínico'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    :title="editando ? 'Editar registro clínico' : 'Nuevo registro clínico'"
    :subtitle="nombreEjemplar ? `Ejemplar: ${nombreEjemplar}` : 'Historial veterinario del ejemplar'"
    width="1000px"
    @close="emit('close')"
  >
    <form class="registro-form" @submit.prevent="guardar">
      <!-- Tipo: solo se elige al crear; al editar se mantiene el del registro -->
      <div class="field">
        <span class="etiqueta" id="tipo-registro">Tipo</span>
        <div class="pastillas" role="radiogroup" aria-labelledby="tipo-registro">
          <button
            v-for="t in TIPOS"
            :key="t.valor"
            type="button"
            class="pastilla"
            :class="{ activa: tipo === t.valor }"
            role="radio"
            :aria-checked="tipo === t.valor"
            :disabled="editando ? tipo !== t.valor : t.valor === 'tratamiento' && diagnosticos.length === 0"
            :title="
              !editando && t.valor === 'tratamiento' && diagnosticos.length === 0
                ? 'Registra primero un diagnóstico'
                : undefined
            "
            @click="tipo = t.valor"
          >
            {{ t.label }}
          </button>
        </div>
      </div>

      <div v-if="tipo === 'diagnostico'" class="diagnostico-layout">
        <div class="diagnostico-campos">
          <div class="field">
            <label for="diagnostico">Título</label>
            <input
              id="diagnostico"
              v-model="formDiagnostico.diagnostico"
              class="input"
              required
              maxlength="5000"
              placeholder="Ej. Control de rutina, infección respiratoria…"
            />
          </div>
          <div class="field descripcion">
            <label for="observaciones">Descripción / observaciones</label>
            <textarea
              id="observaciones"
              v-model="formDiagnostico.observaciones"
              class="input"
              rows="6"
              placeholder="Hallazgos, síntomas o plan de seguimiento…"
            />
          </div>
          <label class="check">
            <input v-model="formDiagnostico.es_critico" type="checkbox" />
            Marcar como crítico
          </label>
        </div>

        <details class="signos" open>
          <summary>Signos vitales</summary>
          <div class="signos-grid">
            <div class="field">
              <label for="peso">Peso (kg)</label>
              <input
                id="peso"
                v-model="formSignos.peso_kg"
                class="input"
                type="number"
                min="0.001"
                step="0.001"
                :placeholder="referencia('peso_kg')"
              />
            </div>
            <div class="field">
              <label for="temperatura">Temperatura (°C)</label>
              <input
                id="temperatura"
                v-model="formSignos.temperatura_c"
                class="input"
                type="number"
                min="0"
                max="60"
                step="0.1"
                :placeholder="referencia('temperatura_c')"
              />
            </div>
            <div class="field">
              <label for="frecuencia-cardiaca">Frec. cardíaca (lpm)</label>
              <input
                id="frecuencia-cardiaca"
                v-model="formSignos.frecuencia_cardiaca_lpm"
                class="input"
                type="number"
                min="1"
                step="1"
                :placeholder="referencia('frecuencia_cardiaca_lpm')"
              />
            </div>
            <div class="field">
              <label for="frecuencia-respiratoria">Frec. respiratoria (rpm)</label>
              <input
                id="frecuencia-respiratoria"
                v-model="formSignos.frecuencia_respiratoria_rpm"
                class="input"
                type="number"
                min="1"
                max="2147483647"
                step="1"
                :placeholder="referencia('frecuencia_respiratoria_rpm')"
              />
            </div>
            <div class="field">
              <label for="tllc">Llenado capilar (s)</label>
              <input
                id="tllc"
                v-model="formSignos.tiempo_llenado_capilar_s"
                class="input"
                type="number"
                min="0.1"
                step="0.1"
                :placeholder="referencia('tiempo_llenado_capilar_s')"
              />
            </div>
            <div class="field">
              <label for="hidratacion">Hidratación</label>
              <select
                id="hidratacion"
                v-model="formSignos.hidratacion"
                class="input"
                :class="{ vacio: !formSignos.hidratacion }"
              >
                <option value="">{{ referencia('hidratacion', 'Sin registrar') }}</option>
                <option v-for="(label, valor) in HIDRATACION" :key="valor" :value="valor">{{ label }}</option>
              </select>
            </div>
            <div class="field">
              <label for="condicion-corporal">Condición corporal (1–5)</label>
              <select
                id="condicion-corporal"
                v-model="formSignos.condicion_corporal"
                class="input"
                :class="{ vacio: formSignos.condicion_corporal === '' }"
              >
                <option value="">{{ referencia('condicion_corporal', 'Sin registrar') }}</option>
                <option v-for="(label, valor) in CONDICION" :key="valor" :value="valor">
                  {{ valor }} · {{ label }}
                </option>
              </select>
            </div>
            <div class="field">
              <label for="mucosas">Mucosas</label>
              <select
                id="mucosas"
                v-model="formSignos.mucosas"
                class="input"
                :class="{ vacio: !formSignos.mucosas }"
              >
                <option value="">{{ referencia('mucosas', 'Sin registrar') }}</option>
                <option v-for="(label, valor) in MUCOSAS" :key="valor" :value="valor">{{ label }}</option>
              </select>
            </div>
            <div class="field">
              <label for="actitud">Actitud</label>
              <select
                id="actitud"
                v-model="formSignos.actitud"
                class="input"
                :class="{ vacio: !formSignos.actitud }"
              >
                <option value="">{{ referencia('actitud', 'Sin registrar') }}</option>
                <option v-for="(label, valor) in ACTITUD" :key="valor" :value="valor">{{ label }}</option>
              </select>
            </div>
          </div>
          <p class="ayuda-signos">
            {{ hayUltimos ? 'Se muestra el último valor como referencia. ' : '' }}Completa solo las mediciones
            disponibles; los rangos dependen de la especie.
          </p>
        </details>
      </div>

      <div v-else class="tratamiento-grid">
        <nav class="pestanas-tratamiento" role="tablist" aria-label="Secciones del tratamiento">
          <button
            type="button"
            role="tab"
            id="tab-datos-tratamiento"
            aria-controls="panel-datos-tratamiento"
            :aria-selected="pestanaTratamiento === 'datos'"
            :class="{ activa: pestanaTratamiento === 'datos' }"
            @click="pestanaTratamiento = 'datos'"
          >
            Tratamiento
          </button>
          <button
            type="button"
            role="tab"
            id="tab-medicamentos-tratamiento"
            aria-controls="panel-medicamentos-tratamiento"
            :aria-selected="pestanaTratamiento === 'medicamentos'"
            :class="{ activa: pestanaTratamiento === 'medicamentos' }"
            @click="pestanaTratamiento = 'medicamentos'"
          >
            Medicamentos ({{ formTratamiento.medicamentos.length }})
          </button>
        </nav>
        <section
          v-if="pestanaTratamiento === 'datos'"
          id="panel-datos-tratamiento"
          class="tratamiento-tabpanel"
          role="tabpanel"
          aria-labelledby="tab-datos-tratamiento"
        >
          <div class="tratamiento-contexto">
            <div class="field">
              <label for="diagnostico-asociado">Diagnóstico asociado</label>
              <select
                id="diagnostico-asociado"
                v-model.number="formTratamiento.id_diagnostico"
                class="input"
                :required="!editando"
                :disabled="editando"
              >
                <option :value="0" disabled>Selecciona un diagnóstico</option>
                <option v-for="d in diagnosticosOrdenados" :key="d.id_diagnostico" :value="d.id_diagnostico">
                  {{ d.diagnostico }}
                </option>
              </select>
            </div>
            <div class="field">
              <label for="fecha-inicio">Fecha de inicio</label>
              <input id="fecha-inicio" v-model="formTratamiento.fecha_inicio" class="input" type="date" required />
            </div>
            <div class="field">
              <label for="fecha-fin">Fecha de fin</label>
              <input
                id="fecha-fin"
                v-model="formTratamiento.fecha_fin"
                class="input"
                type="date"
                :min="formTratamiento.fecha_inicio"
              />
            </div>
          </div>
          <div class="field descripcion-tratamiento">
            <label for="descripcion-tratamiento">Descripción del tratamiento</label>
            <textarea
              id="descripcion-tratamiento"
              v-model="formTratamiento.descripcion"
              class="input"
              rows="3"
              required
              placeholder="Indicación y procedimiento a realizar"
            />
          </div>
          <div class="tratamiento-programacion">
            <div class="field">
              <label for="estado-tratamiento">Estado</label>
              <select id="estado-tratamiento" v-model="formTratamiento.estado" class="input">
                <option value="en_curso">En curso</option>
                <option value="finalizado">Finalizado</option>
                <option value="suspendido">Suspendido</option>
              </select>
            </div>
            <div class="field">
              <label for="hora-inicio">Hora de inicio</label>
              <input
                id="hora-inicio"
                v-model="formTratamiento.hora_inicio"
                class="input"
                type="time"
                required
              />
            </div>
            <div class="field">
              <label for="frecuencia-valor">Frecuencia</label>
              <input
                id="frecuencia-valor"
                v-model="formTratamiento.frecuencia_valor"
                class="input"
                type="number"
                min="1"
                step="1"
                required
              />
            </div>
            <div class="field">
              <label for="frecuencia-unidad">Unidad de frecuencia</label>
              <select id="frecuencia-unidad" v-model="formTratamiento.frecuencia_unidad" class="input">
                <option value="" disabled>Selecciona unidad</option>
                <option value="horas">Horas</option>
                <option value="dias">Días</option>
              </select>
            </div>
          </div>
          <p
            v-if="
              tratamientoLegado &&
              (!tratamientoLegado.frecuencia_valor ||
                !tratamientoLegado.frecuencia_unidad ||
                !tratamientoLegado.hora_inicio)
            "
            class="dato-legado"
          >
            Este tratamiento previo no tiene frecuencia y hora estructuradas. Datos anteriores:
            frecuencia {{ tratamientoLegado.frecuencia || 'sin registrar' }},
            dosis {{ tratamientoLegado.dosis || 'sin registrar' }}. Ingresa la programación y los medicamentos
            estructurados para generar actividades.
          </p>
        </section>
        <section
          v-else
          id="panel-medicamentos-tratamiento"
          class="medicamentos-seccion tratamiento-tabpanel"
          role="tabpanel"
          aria-labelledby="tab-medicamentos-tratamiento"
        >
          <header class="medicamentos-cabecera">
            <div>
              <h3>Medicamentos</h3>
              <p>Opcional. Puedes agregar ninguno, uno o varios medicamentos.</p>
            </div>
            <button type="button" class="btn btn-secondary" @click="agregarMedicamento">
              + Agregar medicamento
            </button>
          </header>
          <div v-if="formTratamiento.medicamentos.length" class="medicamentos-lista">
            <div
              v-for="(medicamento, indice) in formTratamiento.medicamentos"
              :key="indice"
              class="medicamento-row"
            >
              <div class="field">
                <label :for="`medicamento-nombre-${indice}`">Nombre del medicamento</label>
                <input
                  :id="`medicamento-nombre-${indice}`"
                  v-model="medicamento.nombre_medicamento"
                  class="input"
                  maxlength="150"
                  required
                />
              </div>
              <div class="field">
                <label :for="`medicamento-dosis-${indice}`">Dosis</label>
                <div class="dosis-input">
                  <input
                    :id="`medicamento-dosis-${indice}`"
                    v-model="medicamento.dosis_ml"
                    class="input"
                    type="number"
                    min="0.01"
                    max="999999.99"
                    step="0.01"
                    required
                  />
                  <span>ml</span>
                </div>
              </div>
              <button
                type="button"
                class="btn btn-secondary quitar-medicamento"
                :aria-label="`Quitar medicamento ${indice + 1}`"
                @click="quitarMedicamento(indice)"
              >
                Quitar
              </button>
            </div>
          </div>
          <p v-else class="medicamentos-vacio">No se agregaron medicamentos.</p>
        </section>
      </div>

      <p v-if="error" class="alert-error">{{ error }}</p>
      <footer class="acciones">
        <button type="button" class="btn btn-secondary" :disabled="guardando" @click="emit('close')">
          {{ tratamientoGuardadoSinActividades ? 'Cerrar' : 'Cancelar' }}
        </button>
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="guardando || tratamientoGuardadoSinActividades"
        >
          {{ guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Guardar registro' }}
        </button>
      </footer>
    </form>
  </BaseModal>
</template>

<style scoped>
.registro-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.etiqueta {
  font-size: 12px;
  color: var(--color-text-muted);
}

/* Tipo de registro como pastillas */
.pastillas {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pastilla {
  padding: 8px 18px;
  border: 1px solid var(--color-border-strong);
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 14px;
  transition: background-color 0.15s, border-color 0.15s;
}

.pastilla:hover:not(:disabled):not(.activa) {
  background: var(--color-surface-alt);
}

.pastilla.activa {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
  font-weight: 500;
}

.pastilla.activa:disabled {
  opacity: 1;
  cursor: default;
}

/* Diagnóstico a la izquierda, signos vitales a la derecha */
.diagnostico-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr);
  gap: 24px;
}

.diagnostico-campos {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.descripcion {
  flex: 1;
}

.descripcion textarea {
  flex: 1;
  min-height: 120px;
  resize: vertical;
}

.signos {
  min-width: 0;
}

.signos summary {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.signos-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.signos-grid .input {
  padding: 9px 11px;
  font-size: 13px;
}

.signos-grid .input::placeholder,
.signos-grid select.vacio {
  color: var(--color-text-muted);
}

.signos-grid select option {
  color: var(--color-text);
}

.ayuda-signos {
  margin-top: 10px;
  color: var(--color-text-muted);
  font-size: 11px;
}

.tratamiento-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tratamiento-tabpanel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.tratamiento-contexto {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.tratamiento-programacion {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.descripcion-tratamiento textarea {
  resize: vertical;
}

.tratamiento-contenido {
  min-width: 0;
}

.pestanas-tratamiento {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid var(--color-border);
}

.pestanas-tratamiento button {
  padding: 10px 14px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--color-text-muted);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.pestanas-tratamiento button:hover,
.pestanas-tratamiento button.activa {
  color: var(--color-primary);
}

.pestanas-tratamiento button.activa {
  border-bottom-color: var(--color-primary);
  font-weight: 600;
}

.tratamiento-tabpanel .dato-legado {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 12px;
}

.medicamentos-seccion {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.medicamentos-cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.medicamentos-cabecera h3 {
  margin: 0;
  font-size: 15px;
}

.medicamentos-cabecera p,
.medicamentos-vacio {
  margin: 4px 0 0;
  color: var(--color-text-muted);
  font-size: 12px;
}

.medicamentos-lista {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.medicamento-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(120px, 0.35fr) auto;
  align-items: end;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.dosis-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dosis-input .input {
  min-width: 0;
}

.dosis-input span {
  color: var(--color-text-muted);
  font-size: 13px;
}

.quitar-medicamento {
  min-height: 40px;
}

.check {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.check input {
  accent-color: var(--color-primary);
}

.acciones {
  position: sticky;
  bottom: -20px;
  z-index: 1;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin: 4px -24px -20px;
  padding: 14px 24px 20px;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}

/* En pantallas angostas se apila y el modal hace scroll */
@media (max-width: 820px) {
  .diagnostico-layout {
    grid-template-columns: 1fr;
  }

  .tratamiento-grid {
    grid-template-columns: 1fr;
  }

  .tratamiento-contexto,
  .tratamiento-programacion {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .medicamento-row {
    grid-template-columns: minmax(0, 1fr) minmax(110px, 0.45fr) auto;
  }
}

@media (max-width: 520px) {
  .signos-grid,
  .tratamiento-contexto,
  .tratamiento-programacion {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .tratamiento-contexto {
    grid-template-columns: 1fr;
  }

  .medicamento-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .medicamentos-cabecera {
    align-items: flex-start;
    flex-direction: column;
  }

  .acciones {
    margin-right: -18px;
    margin-bottom: -16px;
    margin-left: -18px;
    padding-right: 18px;
    padding-left: 18px;
    bottom: -16px;
  }
}
</style>
