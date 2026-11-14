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
const mostrarPassword = ref(false)

const esEdicion = computed(() => props.usuario !== null)

// Cada vez que se abre el modal, cargamos los datos del usuario o lo dejamos vacío
watch(
  () => props.open,
  (abierto) => {
    if (!abierto) return
    error.value = ''
    // La contraseña vuelve a ocultarse cada vez que se abre el formulario
    mostrarPassword.value = false
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
        <!-- Mismo botón de ojo que en el inicio de sesión, para revisar lo que se escribió -->
        <div class="password-control">
          <input
            id="password"
            v-model="form.password"
            :type="mostrarPassword ? 'text' : 'password'"
            class="input"
            autocomplete="new-password"
            minlength="8"
            :required="!esEdicion"
          />
          <button
            class="password-toggle"
            type="button"
            :aria-label="mostrarPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
            :aria-pressed="mostrarPassword"
            @click="mostrarPassword = !mostrarPassword"
          >
            <svg v-if="mostrarPassword" viewBox="0 0 24 24" width="19" height="19" fill="none" aria-hidden="true">
              <path
                d="M2.5 12s3.2-6 9.5-6 9.5 6 9.5 6-3.2 6-9.5 6-9.5-6-9.5-6Z"
                stroke="currentColor"
                stroke-width="1.7"
              />
              <circle cx="12" cy="12" r="2.7" stroke="currentColor" stroke-width="1.7" />
            </svg>
            <svg v-else viewBox="0 0 24 24" width="19" height="19" fill="none" aria-hidden="true">
              <path
                d="M3 3l18 18M10.6 6.2A9.8 9.8 0 0 1 12 6c6.3 0 9.5 6 9.5 6a15 15 0 0 1-3.1 3.7M6.2 6.7C3.8 8.3 2.5 12 2.5 12s3.2 6 9.5 6c1 0 1.9-.2 2.7-.5"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
            </svg>
          </button>
        </div>
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

.password-control {
  position: relative;
}

.password-control .input {
  width: 100%;
  padding-right: 46px;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 5px;
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  transform: translateY(-50%);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
}

.password-toggle:hover {
  background: var(--color-surface-alt);
  color: var(--color-text);
}

.password-toggle:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
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
