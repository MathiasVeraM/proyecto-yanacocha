<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { ApiError } from '@/api/http'
import { veterinariaApi } from '@/api/veterinaria'
import { hoyIso } from '@/config/animales'
import type {
  Diagnostico,
  DiagnosticoCreate,
  Tratamiento,
  TratamientoCreate,
} from '@/types/veterinaria'

type RegistroExistente =
  | { tipo: 'diagnostico'; datos: Diagnostico }
  | { tipo: 'tratamiento'; datos: Tratamiento }

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
      const datos: DiagnosticoCreate = {
        diagnostico: formDiagnostico.diagnostico.trim(),
        observaciones: formDiagnostico.observaciones.trim() || null,
        es_critico: formDiagnostico.es_critico,
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
    error.value = e instanceof ApiError ? e.message : 'No se pudo guardar el registro clínico'
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
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
