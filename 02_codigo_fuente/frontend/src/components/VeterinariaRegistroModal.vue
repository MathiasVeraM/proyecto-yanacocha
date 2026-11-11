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
} from '@/types/veterinaria'

type RegistroExistente =
  | { tipo: 'diagnostico'; datos: Diagnostico }
  | { tipo: 'tratamiento'; datos: Tratamiento }

type ValorNumerico = string | number
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
const error = ref('')
const guardando = ref(false)
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
  medicamento_o_proceso: '',
  dosis: '',
  frecuencia: '',
  fecha_inicio: hoyIso(),
  fecha_fin: '',
  estado: 'en_curso' as Tratamiento['estado'],
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
      medicamento_o_proceso:
        props.registro?.tipo === 'tratamiento' ? props.registro.datos.medicamento_o_proceso : '',
      dosis: props.registro?.tipo === 'tratamiento' ? (props.registro.datos.dosis ?? '') : '',
      frecuencia: props.registro?.tipo === 'tratamiento' ? (props.registro.datos.frecuencia ?? '') : '',
      fecha_inicio: props.registro?.tipo === 'tratamiento' ? props.registro.datos.fecha_inicio : hoyIso(),
      fecha_fin: props.registro?.tipo === 'tratamiento' ? (props.registro.datos.fecha_fin ?? '') : '',
      estado: props.registro?.tipo === 'tratamiento' ? props.registro.datos.estado : 'en_curso',
    })
  },
)

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
      if (!formTratamiento.id_diagnostico && props.registro?.tipo !== 'tratamiento') {
        error.value = 'Selecciona el diagnóstico asociado'
        return
      }
      const datos: TratamientoCreate = {
        medicamento_o_proceso: formTratamiento.medicamento_o_proceso.trim(),
        dosis: formTratamiento.dosis.trim() || null,
        frecuencia: formTratamiento.frecuencia.trim() || null,
        fecha_inicio: formTratamiento.fecha_inicio,
        fecha_fin: formTratamiento.fecha_fin || null,
        estado: formTratamiento.estado,
      }
      if (props.registro?.tipo === 'tratamiento') {
        await veterinariaApi.actualizarTratamiento(props.registro.datos.id_tratamiento, datos)
      } else {
        await veterinariaApi.crearTratamiento(formTratamiento.id_diagnostico, datos)
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
        <div v-if="!editando" class="field doble">
          <label for="diagnostico-asociado">Diagnóstico asociado</label>
          <select id="diagnostico-asociado" v-model.number="formTratamiento.id_diagnostico" class="input" required>
            <option :value="0" disabled>Selecciona un diagnóstico</option>
            <option v-for="d in diagnosticosOrdenados" :key="d.id_diagnostico" :value="d.id_diagnostico">
              {{ d.diagnostico }}
            </option>
          </select>
        </div>
        <div class="field doble">
          <label for="tratamiento">Tratamiento / procedimiento</label>
          <input
            id="tratamiento"
            v-model="formTratamiento.medicamento_o_proceso"
            class="input"
            required
            maxlength="200"
            placeholder="Medicamento o procedimiento"
          />
        </div>
        <div class="field">
          <label for="dosis">Dosis</label>
          <input id="dosis" v-model="formTratamiento.dosis" class="input" maxlength="100" placeholder="Ej. 5 ml" />
        </div>
        <div class="field">
          <label for="frecuencia">Frecuencia</label>
          <input
            id="frecuencia"
            v-model="formTratamiento.frecuencia"
            class="input"
            maxlength="100"
            placeholder="Ej. Cada 12 horas"
          />
        </div>
        <div class="field">
          <label for="fecha-inicio">Fecha de inicio</label>
          <input id="fecha-inicio" v-model="formTratamiento.fecha_inicio" class="input" type="date" required />
        </div>
        <div class="field">
          <label for="fecha-fin">Fecha de fin</label>
          <input id="fecha-fin" v-model="formTratamiento.fecha_fin" class="input" type="date" />
        </div>
        <div class="field">
          <label for="estado-tratamiento">Estado</label>
          <select id="estado-tratamiento" v-model="formTratamiento.estado" class="input">
            <option value="en_curso">En curso</option>
            <option value="finalizado">Finalizado</option>
            <option value="suspendido">Suspendido</option>
          </select>
        </div>
      </div>

      <p v-if="error" class="alert-error">{{ error }}</p>
      <footer class="acciones">
        <button type="button" class="btn btn-secondary" :disabled="guardando" @click="emit('close')">
          Cancelar
        </button>
        <button type="submit" class="btn btn-primary" :disabled="guardando">
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
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.tratamiento-grid .doble {
  grid-column: span 2;
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
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .signos-grid,
  .tratamiento-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .tratamiento-grid .doble {
    grid-column: 1 / -1;
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
