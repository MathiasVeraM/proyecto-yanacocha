<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppBadge, { type BadgeTone } from '@/components/AppBadge.vue'
import BaseModal from '@/components/BaseModal.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import UsuarioFormModal from '@/components/UsuarioFormModal.vue'
import { usuariosApi } from '@/api/usuarios'
import { ApiError } from '@/api/http'
import { useRolesStore } from '@/stores/roles'
import type { Usuario } from '@/types'

const rolesStore = useRolesStore()

const tab = ref<'permisos' | 'usuarios'>('usuarios')
const usuarios = ref<Usuario[]>([])
const cargando = ref(true)
const error = ref('')

// Modal de crear / editar
const formAbierto = ref(false)
const usuarioEditando = ref<Usuario | null>(null)

// Modal de confirmación para desactivar
const usuarioADesactivar = ref<Usuario | null>(null)
const desactivando = ref(false)

const tonosPorRol: Record<string, BadgeTone> = {
  administrador: 'green',
  veterinario: 'blue',
  'manejo de animales': 'amber',
  voluntario: 'indigo',
}

function tonoRol(idRol: number): BadgeTone {
  return tonosPorRol[rolesStore.nombreDe(idRol).toLowerCase()] ?? 'gray'
}

function mensajeDe(e: unknown, porDefecto: string) {
  return e instanceof ApiError ? e.message : porDefecto
}

async function cargarUsuarios() {
  cargando.value = true
  error.value = ''
  try {
    usuarios.value = await usuariosApi.listar()
  } catch (e) {
    error.value = mensajeDe(e, 'No se pudieron cargar los usuarios')
  } finally {
    cargando.value = false
  }
}

function abrirCrear() {
  usuarioEditando.value = null
  formAbierto.value = true
}

function abrirEditar(usuario: Usuario) {
  usuarioEditando.value = usuario
  formAbierto.value = true
}

function onGuardado() {
  formAbierto.value = false
  cargarUsuarios()
}

async function confirmarDesactivar() {
  if (!usuarioADesactivar.value) return
  desactivando.value = true
  try {
    await usuariosApi.desactivar(usuarioADesactivar.value.id_usuario)
    usuarioADesactivar.value = null
    await cargarUsuarios()
  } catch (e) {
    error.value = mensajeDe(e, 'No se pudo desactivar la cuenta')
    usuarioADesactivar.value = null
  } finally {
    desactivando.value = false
  }
}

onMounted(cargarUsuarios)
</script>

<template>
  <div class="tabs">
    <button :class="{ active: tab === 'permisos' }" @click="tab = 'permisos'">
      Permisos por roles
    </button>
    <button :class="{ active: tab === 'usuarios' }" @click="tab = 'usuarios'">Usuarios</button>
  </div>

  <section v-if="tab === 'permisos'" class="placeholder">
    La gestión de permisos por roles estará disponible próximamente.
  </section>

  <section v-else>
    <header class="section-header">
      <div>
        <h1>Gestión de cuentas</h1>
        <p>{{ usuarios.length }} usuarios · {{ rolesStore.roles.length }} roles configurados</p>
      </div>
      <button class="btn btn-primary" @click="abrirCrear">+ Crear cuenta</button>
    </header>

    <p v-if="error" class="alert-error">{{ error }}</p>

    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Rol</th>
            <th>Estado</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-if="cargando">
            <td colspan="4" class="empty">Cargando usuarios…</td>
          </tr>
          <tr v-else-if="usuarios.length === 0">
            <td colspan="4" class="empty">No hay usuarios registrados</td>
          </tr>
          <tr v-for="u in usuarios" v-else :key="u.id_usuario">
            <td>
              <div class="user-cell">
                <UserAvatar :nombre="u.nombre" :apellido="u.apellido" />
                <div>
                  <strong>{{ u.nombre }} {{ u.apellido }}</strong>
                  <small>{{ u.correo }}</small>
                </div>
              </div>
            </td>
            <td>
              <AppBadge :tone="tonoRol(u.id_rol)">{{ rolesStore.nombreDe(u.id_rol) }}</AppBadge>
            </td>
            <td>
              <AppBadge :tone="u.activo ? 'green' : 'gray'">
                {{ u.activo ? 'Activo' : 'Suspendido' }}
              </AppBadge>
            </td>
            <td class="actions">
              <button class="action edit" @click="abrirEditar(u)">Editar</button>
              <button
                class="action deactivate"
                :disabled="!u.activo"
                @click="usuarioADesactivar = u"
              >
                Desactivar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <UsuarioFormModal
    :open="formAbierto"
    :usuario="usuarioEditando"
    @close="formAbierto = false"
    @saved="onGuardado"
  />

  <BaseModal
    :open="usuarioADesactivar !== null"
    title="Desactivar cuenta"
    width="420px"
    @close="usuarioADesactivar = null"
  >
    <p class="confirm-text">
      ¿Seguro que deseas desactivar la cuenta de
      <strong>{{ usuarioADesactivar?.nombre }} {{ usuarioADesactivar?.apellido }}</strong>?
      Podrás reactivarla desde “Editar”.
    </p>
    <template #footer>
      <button class="btn btn-secondary" @click="usuarioADesactivar = null">Cancelar</button>
      <button class="btn btn-danger" :disabled="desactivando" @click="confirmarDesactivar">
        {{ desactivando ? 'Desactivando…' : 'Desactivar' }}
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.tabs {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  margin-bottom: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.tabs button {
  padding: 7px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  font-size: 12px;
  font-weight: 500;
}

.tabs button.active {
  background: var(--color-primary);
  color: #fff;
}

.placeholder {
  padding: 48px;
  text-align: center;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h1 {
  font-size: 16px;
  font-weight: 700;
}

.section-header p {
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.alert-error {
  margin-bottom: 12px;
}

.table-card {
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  padding: 12px 16px;
  background: var(--color-surface-alt);
  border-bottom: 1px solid var(--color-border);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-align: left;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

tbody tr:last-child td {
  border-bottom: none;
}

.empty {
  padding: 32px;
  text-align: center;
  color: var(--color-text-muted);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-cell strong {
  display: block;
  font-weight: 600;
}

.user-cell small {
  font-size: 11px;
  color: var(--color-text-muted);
}

.actions {
  text-align: right;
  white-space: nowrap;
}

.action {
  margin-left: 6px;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.action.edit {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border-strong);
  color: var(--color-text-muted);
}

.action.edit:hover {
  background: var(--color-border);
}

.action.deactivate {
  background: var(--color-danger-soft);
  border: 1px solid #efc6c1;
  color: var(--color-danger);
}

.action.deactivate:hover:not(:disabled) {
  background: #f2cfcb;
}

.confirm-text {
  line-height: 1.5;
}
</style>
