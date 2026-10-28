<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { ApiError } from '@/api/http'
import { veterinariaApi } from '@/api/veterinaria'
import { hoyIso } from '@/config/animales'
import type {
  Diagnostico,
  DiagnosticoCreate,
  SignosVitalesCreate,
  Tratamiento,
  TratamientoCreate,
} from '@/types/veterinaria'

type RegistroExistente =
  | { tipo: 'diagnostico'; datos: Diagnostico }
  | { tipo: 'tratamiento'; datos: Tratamiento }

type ValorNumerico = string | number

const props = defineProps<{
  open: boolean
  idAnimal: number
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

const editando = computed(() => !!props.registro)
const diagnosticosOrdenados = computed(() =>
  [...props.diagnosticos].sort(
    (a, b) => new Date(b.fecha_registro).getTime() - new Date(a.fecha_registro).getTime(),
  ),
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
    Object.assign(formDiagnostico, {
      diagnostico: props.registro?.tipo === 'diagnostico' ? props.registro.datos.diagnostico : '',
      observaciones:
        props.registro?.tipo === 'diagnostico' ? (props.registro.datos.observaciones ?? '') : '',
      es_critico: props.registro?.tipo === 'diagnostico' ? props.registro.datos.es_critico : false,
    })
    Object.assign(formSignos, {
      peso_kg: '',
      temperatura_c: '',
      frecuencia_cardiaca_lpm: '',
      frecuencia_respiratoria_rpm: '',
      tiempo_llenado_capilar_s: '',
      hidratacion: '',
      condicion_corporal: '',
      mucosas: '',
      actitud: '',
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
      const signosVitales: SignosVitalesCreate = {
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
      const incluirSignos = Object.values(signosVitales).some((valor) => valor !== null)
      const datos: DiagnosticoCreate = {
        diagnostico: formDiagnostico.diagnostico.trim(),
        observaciones: formDiagnostico.observaciones.trim() || null,
        es_critico: formDiagnostico.es_critico,
        ...(incluirSignos ? { signos_vitales: signosVitales } : {}),
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
    subtitle="Historial veterinario del ejemplar"
    width="560px"
    @close="emit('close')"
  >
    <form class="registro-form" @submit.prevent="guardar">
      <fieldset :disabled="editando">
        <legend>Tipo de registro</legend>
        <div class="tipo-opciones">
          <button
            type="button"
            :class="{ activo: tipo === 'diagnostico' }"
            @click="tipo = 'diagnostico'"
          >
            Diagnóstico
          </button>
          <button
            type="button"
            :class="{ activo: tipo === 'tratamiento' }"
            :disabled="diagnosticos.length === 0 && !editando"
            @click="tipo = 'tratamiento'"
          >
            Tratamiento
          </button>
        </div>
      </fieldset>

      <template v-if="tipo === 'diagnostico'">
        <div class="field">
          <label for="diagnostico">Motivo / título</label>
          <input
            id="diagnostico"
            v-model="formDiagnostico.diagnostico"
            class="input"
            required
            maxlength="5000"
            placeholder="Ej. Control de rutina, infección respiratoria…"
          />
        </div>
        <div class="field">
          <label for="observaciones">Descripción clínica</label>
          <textarea
            id="observaciones"
            v-model="formDiagnostico.observaciones"
            class="input"
            rows="4"
            placeholder="Hallazgos, síntomas o plan de seguimiento…"
          />
        </div>
        <label class="check">
          <input v-model="formDiagnostico.es_critico" type="checkbox" />
          Marcar como diagnóstico crítico
        </label>

        <fieldset v-if="!editando" class="signos-fieldset">
          <legend>Signos vitales <span>Opcional · actualiza la ficha clínica</span></legend>
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
                placeholder="—"
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
                placeholder="—"
              />
            </div>
            <div class="field">
              <label for="frecuencia-cardiaca">Frecuencia cardíaca (lpm)</label>
              <input
                id="frecuencia-cardiaca"
                v-model="formSignos.frecuencia_cardiaca_lpm"
                class="input"
                type="number"
                min="1"
                step="1"
                placeholder="—"
              />
            </div>
            <div class="field">
              <label for="frecuencia-respiratoria">Frecuencia respiratoria (rpm)</label>
              <input
                id="frecuencia-respiratoria"
                v-model="formSignos.frecuencia_respiratoria_rpm"
                class="input"
                type="number"
                min="1"
                step="1"
                placeholder="—"
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
                placeholder="—"
              />
            </div>
            <div class="field">
              <label for="hidratacion">Hidratación</label>
              <select id="hidratacion" v-model="formSignos.hidratacion" class="input">
                <option value="">Sin registrar</option>
                <option value="normal">Normal</option>
                <option value="deshidratacion_leve">Deshidratación leve</option>
                <option value="deshidratacion_moderada">Deshidratación moderada</option>
                <option value="deshidratacion_severa">Deshidratación severa</option>
              </select>
            </div>
            <div class="field">
              <label for="condicion-corporal">Condición corporal (1–5)</label>
              <select id="condicion-corporal" v-model="formSignos.condicion_corporal" class="input">
                <option value="">Sin registrar</option>
                <option value="1">1 · Caquéctico</option>
                <option value="2">2 · Delgado</option>
                <option value="3">3 · Óptimo</option>
                <option value="4">4 · Sobrepeso</option>
                <option value="5">5 · Obeso</option>
              </select>
            </div>
            <div class="field">
              <label for="mucosas">Mucosas</label>
              <select id="mucosas" v-model="formSignos.mucosas" class="input">
                <option value="">Sin registrar</option>
                <option value="rosadas">Rosadas</option>
                <option value="palidas">Pálidas</option>
                <option value="cianoticas">Cianóticas</option>
                <option value="ictericas">Ictéricas</option>
                <option value="congestionadas">Congestionadas</option>
              </select>
            </div>
            <div class="field">
              <label for="actitud">Actitud</label>
              <select id="actitud" v-model="formSignos.actitud" class="input">
                <option value="">Sin registrar</option>
                <option value="alerta">Alerta</option>
                <option value="deprimido">Deprimido</option>
                <option value="estuporoso">Estuporoso</option>
                <option value="agitado">Agitado</option>
              </select>
            </div>
          </div>
          <p class="ayuda-signos">Registra solo las mediciones disponibles; no hay rangos normales fijos.</p>
        </fieldset>
      </template>

      <template v-else>
        <div v-if="!editando" class="field">
          <label for="diagnostico-asociado">Diagnóstico asociado</label>
          <select id="diagnostico-asociado" v-model.number="formTratamiento.id_diagnostico" class="input" required>
            <option :value="0" disabled>Selecciona un diagnóstico</option>
            <option v-for="d in diagnosticosOrdenados" :key="d.id_diagnostico" :value="d.id_diagnostico">
              {{ d.diagnostico }}
            </option>
          </select>
        </div>
        <div class="field">
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
        <div class="form-grid">
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
        </div>
        <div class="field">
          <label for="estado-tratamiento">Estado</label>
          <select id="estado-tratamiento" v-model="formTratamiento.estado" class="input">
            <option value="en_curso">En curso</option>
            <option value="finalizado">Finalizado</option>
            <option value="suspendido">Suspendido</option>
          </select>
        </div>
      </template>

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
  display: grid;
  gap: 16px;
}

fieldset {
  padding: 0;
  border: 0;
}

legend,
.field label {
  margin-bottom: 7px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.tipo-opciones {
  display: flex;
  gap: 8px;
}

.tipo-opciones button {
  padding: 8px 13px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 12px;
}

.tipo-opciones button.activo {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: white;
}

.field textarea {
  resize: vertical;
  min-height: 92px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.signos-fieldset {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
}

.signos-fieldset legend {
  padding: 0 5px;
}

.signos-fieldset legend span {
  margin-left: 4px;
  font-size: 10px;
  font-weight: 400;
  letter-spacing: 0;
  text-transform: none;
}

.signos-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 11px;
}

.signos-grid .input {
  padding: 9px 10px;
  background: var(--color-surface);
  font-size: 12px;
}

.ayuda-signos {
  color: var(--color-text-muted);
  font-size: 11px;
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
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

@media (max-width: 520px) {
  .form-grid,
  .signos-grid {
    grid-template-columns: 1fr;
  }
}
</style>
