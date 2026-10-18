<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import BaseModal from './BaseModal.vue'
import { rolesApi } from '@/api/roles'
import { ApiError } from '@/api/http'
import type { Rol } from '@/types'

const props = defineProps<{
  open: boolean
  // null = crear rol, Rol = editar rol
  rol: Rol | null
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const form = reactive({ nombre_rol: '', descripcion: '' })
const error = ref('')
const guardando = ref(false)

const esEdicion = computed(() => props.rol !== null)

// Cada vez que se abre el modal, cargamos los datos del rol o lo dejamos vacío
watch(
  () => props.open,
  (abierto) => {
    if (!abierto) return
    error.value = ''
    Object.assign(form, {
      nombre_rol: props.rol?.nombre_rol ?? '',
      descripcion: props.rol?.descripcion ?? '',
    })
  },
)

async function guardar() {
  error.value = ''
  guardando.value = true
  const datos = { nombre_rol: form.nombre_rol, descripcion: form.descripcion || null }
  try {
    if (props.rol) await rolesApi.actualizar(props.rol.id_rol, datos)
    else await rolesApi.crear(datos)
    emit('saved')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo guardar el rol'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    :title="esEdicion ? 'Editar rol' : 'Agregar nuevo rol'"
    :subtitle="esEdicion ? 'Actualiza los datos del rol' : 'Define un nuevo rol de acceso'"
    @close="emit('close')"
  >
    <form id="rol-form" class="form" @submit.prevent="guardar">
      <div class="field">
        <label for="nombre_rol">Nombre</label>
        <input
          id="nombre_rol"
          v-model.trim="form.nombre_rol"
          class="input"
          maxlength="50"
          required
        />
      </div>

      <div class="field">
        <label for="descripcion_rol">Descripción</label>
        <textarea id="descripcion_rol" v-model.trim="form.descripcion" class="input" rows="3" />
      </div>

      <p v-if="error" class="alert-error">{{ error }}</p>
    </form>

    <template #footer>
      <button type="button" class="btn btn-secondary" @click="emit('close')">Cancelar</button>
      <button type="submit" form="rol-form" class="btn btn-primary" :disabled="guardando">
        {{ guardando ? 'Guardando…' : esEdicion ? 'Guardar cambios' : 'Crear rol' }}
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

textarea.input {
  resize: vertical;
  font: inherit;
}
</style>
