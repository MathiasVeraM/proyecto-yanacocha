<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import BaseModal from './BaseModal.vue'
import { usuariosApi } from '@/api/usuarios'
import { ApiError } from '@/api/http'
import { useRolesStore } from '@/stores/roles'
import type { Usuario, UsuarioUpdate } from '@/types'

const props = defineProps<{
  open: boolean
  // null = crear cuenta, Usuario = editar cuenta
  usuario: Usuario | null
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const rolesStore = useRolesStore()

const form = reactive({
  nombre: '',
  apellido: '',
  correo: '',
  password: '',
  id_rol: 0,
  activo: true,
})
const error = ref('')
const guardando = ref(false)

const esEdicion = computed(() => props.usuario !== null)

// Cada vez que se abre el modal, cargamos los datos del usuario o lo dejamos vacío
watch(
  () => props.open,
  (abierto) => {
    if (!abierto) return
    error.value = ''
    const u = props.usuario
    Object.assign(form, {
      nombre: u?.nombre ?? '',
      apellido: u?.apellido ?? '',
      correo: u?.correo ?? '',
      password: '',
      id_rol: u?.id_rol ?? rolesStore.roles[0]?.id_rol ?? 0,
      activo: u?.activo ?? true,
    })
  },
)

async function guardar() {
  error.value = ''
  guardando.value = true
  try {
    if (props.usuario) {
      const datos: UsuarioUpdate = {
        nombre: form.nombre,
        apellido: form.apellido,
        correo: form.correo,
        id_rol: form.id_rol,
        activo: form.activo,
      }
      if (form.password) datos.password = form.password
      await usuariosApi.actualizar(props.usuario.id_usuario, datos)
    } else {
      await usuariosApi.crear({
        nombre: form.nombre,
        apellido: form.apellido,
        correo: form.correo,
        password: form.password,
        id_rol: form.id_rol,
      })
    }
    emit('saved')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo guardar la cuenta'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    :title="esEdicion ? 'Editar cuenta' : 'Crear cuenta'"
    :subtitle="esEdicion ? 'Actualiza los datos de la cuenta' : 'Registra una nueva cuenta de acceso'"
    @close="emit('close')"
  >
    <form id="usuario-form" class="form" @submit.prevent="guardar">
      <div class="row">
        <div class="field">
          <label for="nombre">Nombre</label>
          <input id="nombre" v-model.trim="form.nombre" class="input" required />
        </div>
        <div class="field">
          <label for="apellido">Apellido</label>
          <input id="apellido" v-model.trim="form.apellido" class="input" required />
        </div>
      </div>

      <div class="field">
        <label for="correo">Correo</label>
        <input id="correo" v-model.trim="form.correo" type="email" class="input" required />
      </div>

      <div class="field">
        <label for="password">
          Contraseña
          <span v-if="esEdicion" class="hint">(déjala vacía para no cambiarla)</span>
        </label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          class="input"
          autocomplete="new-password"
          minlength="8"
          :required="!esEdicion"
        />
      </div>

      <div class="field">
        <label for="rol">Rol</label>
        <select id="rol" v-model.number="form.id_rol" class="input" required>
          <option v-for="rol in rolesStore.roles" :key="rol.id_rol" :value="rol.id_rol">
            {{ rol.nombre_rol }}
          </option>
        </select>
      </div>

      <label v-if="esEdicion" class="check">
        <input v-model="form.activo" type="checkbox" />
        Cuenta activa
      </label>

      <p v-if="error" class="alert-error">{{ error }}</p>
    </form>

    <template #footer>
      <button type="button" class="btn btn-secondary" @click="emit('close')">Cancelar</button>
      <button type="submit" form="usuario-form" class="btn btn-primary" :disabled="guardando">
        {{ guardando ? 'Guardando…' : esEdicion ? 'Guardar cambios' : 'Crear cuenta' }}
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

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.input {
  padding: 9px 12px;
}

.hint {
  color: var(--color-text-subtle);
}

.check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.check input {
  accent-color: var(--color-primary);
}
</style>
