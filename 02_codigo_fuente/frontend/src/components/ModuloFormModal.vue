<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import BaseModal from './BaseModal.vue'
import { modulosApi } from '@/api/modulos'
import { ApiError } from '@/api/http'
import type { Modulo } from '@/types'

const props = defineProps<{
  open: boolean
  // null = crear módulo, Modulo = editar módulo
  modulo: Modulo | null
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const form = reactive({ nombre_modulo: '', codigo_servicio: '' })
const error = ref('')
const guardando = ref(false)

const esEdicion = computed(() => props.modulo !== null)

// Cada vez que se abre el modal, cargamos los datos del módulo o lo dejamos vacío
watch(
  () => props.open,
  (abierto) => {
    if (!abierto) return
    error.value = ''
    Object.assign(form, {
      nombre_modulo: props.modulo?.nombre_modulo ?? '',
      codigo_servicio: props.modulo?.codigo_servicio ?? '',
    })
  },
)

async function guardar() {
  error.value = ''
  guardando.value = true
  try {
    if (props.modulo) await modulosApi.actualizar(props.modulo.id_modulo, { ...form })
    else await modulosApi.crear({ ...form })
    emit('saved')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo guardar el módulo'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    :title="esEdicion ? 'Editar módulo' : 'Agregar módulo'"
    :subtitle="esEdicion ? 'Actualiza los datos del módulo' : 'Registra un nuevo módulo del sistema'"
    @close="emit('close')"
  >
    <form id="modulo-form" class="form" @submit.prevent="guardar">
      <div class="field">
        <label for="nombre_modulo">Nombre</label>
        <input
          id="nombre_modulo"
          v-model.trim="form.nombre_modulo"
          class="input"
          maxlength="100"
          required
        />
      </div>

      <div class="field">
        <label for="codigo_servicio">Código de servicio</label>
        <input
          id="codigo_servicio"
          v-model.trim="form.codigo_servicio"
          class="input"
          maxlength="50"
          placeholder="servicio-gestion-animal"
          required
        />
      </div>

      <p v-if="error" class="alert-error">{{ error }}</p>
    </form>

    <template #footer>
      <button type="button" class="btn btn-secondary" @click="emit('close')">Cancelar</button>
      <button type="submit" form="modulo-form" class="btn btn-primary" :disabled="guardando">
        {{ guardando ? 'Guardando…' : esEdicion ? 'Guardar cambios' : 'Crear módulo' }}
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.input {
  padding: 9px 12px;
}
</style>
