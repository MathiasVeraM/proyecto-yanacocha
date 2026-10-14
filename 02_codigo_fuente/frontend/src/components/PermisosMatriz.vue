<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ConfirmDeleteModal from './ConfirmDeleteModal.vue'
import ModuloFormModal from './ModuloFormModal.vue'
import RolFormModal from './RolFormModal.vue'
import { modulosApi } from '@/api/modulos'
import { rolesApi } from '@/api/roles'
import { ApiError } from '@/api/http'
import { usePermisosStore } from '@/stores/permisos'
import { useRolesStore } from '@/stores/roles'
import type { Modulo, Rol } from '@/types'

// El backend protege este rol: no se puede eliminar ni quitarle permisos
const ID_ROL_ADMIN = 1

const permisosStore = usePermisosStore()
const rolesStore = useRolesStore()

const cargando = ref(true)
const error = ref('')

// Modales de crear / editar
const rolFormAbierto = ref(false)
const rolEditando = ref<Rol | null>(null)
const moduloFormAbierto = ref(false)
const moduloEditando = ref<Modulo | null>(null)

// Modales de confirmación para eliminar
const rolAEliminar = ref<Rol | null>(null)
const moduloAEliminar = ref<Modulo | null>(null)
const eliminando = ref(false)
const errorEliminar = ref('')

function mensajeDe(e: unknown, porDefecto: string) {
  return e instanceof ApiError ? e.message : porDefecto
}

async function cargarMatriz() {
  error.value = ''
  try {
    await permisosStore.cargar()
  } catch (e) {
    error.value = mensajeDe(e, 'No se pudo cargar la matriz de permisos')
  } finally {
    cargando.value = false
  }
}

// Tras cambiar roles o módulos refrescamos la matriz y el catálogo de roles compartido
async function refrescar() {
  await Promise.all([cargarMatriz(), rolesStore.cargar().catch(() => undefined)])
}

async function alternarPermiso(idRol: number, idModulo: number) {
  error.value = ''
  try {
    await permisosStore.alternar(idRol, idModulo)
  } catch (e) {
    error.value = mensajeDe(e, 'No se pudo actualizar el permiso')
  }
}

function abrirCrearRol() {
  rolEditando.value = null
  rolFormAbierto.value = true
}

function abrirEditarRol(rol: Rol) {
  rolEditando.value = rol
  rolFormAbierto.value = true
}

function abrirCrearModulo() {
  moduloEditando.value = null
  moduloFormAbierto.value = true
}

function abrirEditarModulo(modulo: Modulo) {
  moduloEditando.value = modulo
  moduloFormAbierto.value = true
}

function onRolGuardado() {
  rolFormAbierto.value = false
  refrescar()
}

function onModuloGuardado() {
  moduloFormAbierto.value = false
  refrescar()
}

function pedirEliminarRol(rol: Rol) {
  errorEliminar.value = ''
  rolAEliminar.value = rol
}

function pedirEliminarModulo(modulo: Modulo) {
  errorEliminar.value = ''
  moduloAEliminar.value = modulo
}

async function confirmarEliminar(accion: () => Promise<unknown>, cerrar: () => void) {
  eliminando.value = true
  errorEliminar.value = ''
  try {
    await accion()
    cerrar()
    await refrescar()
  } catch (e) {
    errorEliminar.value = mensajeDe(e, 'No se pudo eliminar')
  } finally {
    eliminando.value = false
  }
}

const eliminarRol = () =>
  confirmarEliminar(
    () => rolesApi.eliminar(rolAEliminar.value!.id_rol),
    () => (rolAEliminar.value = null),
  )

const eliminarModulo = () =>
  confirmarEliminar(
    () => modulosApi.eliminar(moduloAEliminar.value!.id_modulo),
    () => (moduloAEliminar.value = null),
  )

onMounted(cargarMatriz)
</script>

<template>
  <section>
    <header class="section-header">
      <p class="intro">
        Selecciona a qué módulos tiene acceso cada rol. Haz clic en las casillas para dar o quitar
        acceso.
      </p>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="abrirCrearModulo">+ Agregar módulo</button>
        <button class="btn btn-primary" @click="abrirCrearRol">+ Agregar nuevo rol</button>
      </div>
    </header>

    <p v-if="error" class="alert-error">{{ error }}</p>

    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th class="col-modulo">Módulo</th>
            <th v-for="rol in permisosStore.matriz.roles" :key="rol.id_rol" class="col-rol">
              <span class="rol-nombre">{{ rol.nombre_rol }}</span>
              <span class="botones">
                <button class="action edit" @click="abrirEditarRol(rol)">Editar</button>
                <button
                  class="action delete"
                  :disabled="rol.id_rol === ID_ROL_ADMIN"
                  :title="rol.id_rol === ID_ROL_ADMIN ? 'El rol de Administrador está protegido' : ''"
                  @click="pedirEliminarRol(rol)"
                >
                  Eliminar
                </button>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr class="fila-usuarios">
            <td>Usuarios asignados</td>
            <td v-for="rol in permisosStore.matriz.roles" :key="rol.id_rol" class="centro">
              {{ rol.total_usuarios }}
            </td>
          </tr>

          <tr v-if="cargando">
            <td :colspan="permisosStore.matriz.roles.length + 1" class="empty">
              Cargando permisos…
            </td>
          </tr>
          <tr v-else-if="permisosStore.matriz.modulos.length === 0">
            <td :colspan="permisosStore.matriz.roles.length + 1" class="empty">
              No hay módulos registrados
            </td>
          </tr>
          <tr v-for="modulo in permisosStore.matriz.modulos" v-else :key="modulo.id_modulo">
            <td>
              <strong>{{ modulo.nombre_modulo }}</strong>
              <span class="botones">
                <button class="action edit" @click="abrirEditarModulo(modulo)">Editar</button>
                <button class="action delete" @click="pedirEliminarModulo(modulo)">Eliminar</button>
              </span>
            </td>
            <td v-for="rol in permisosStore.matriz.roles" :key="rol.id_rol" class="centro">
              <input
                type="checkbox"
                class="check"
                :checked="permisosStore.tiene(rol.id_rol, modulo.id_modulo)"
                :disabled="rol.id_rol === ID_ROL_ADMIN"
                :aria-label="`${rol.nombre_rol} · ${modulo.nombre_modulo}`"
                @change="alternarPermiso(rol.id_rol, modulo.id_modulo)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <RolFormModal
    :open="rolFormAbierto"
    :rol="rolEditando"
    @close="rolFormAbierto = false"
    @saved="onRolGuardado"
  />

  <ModuloFormModal
    :open="moduloFormAbierto"
    :modulo="moduloEditando"
    @close="moduloFormAbierto = false"
    @saved="onModuloGuardado"
  />

  <ConfirmDeleteModal
    :open="rolAEliminar !== null"
    title="Eliminar rol"
    :loading="eliminando"
    :error="errorEliminar"
    @close="rolAEliminar = null"
    @confirm="eliminarRol"
  >
    ¿Seguro que deseas eliminar el rol <strong>{{ rolAEliminar?.nombre_rol }}</strong
    >? Se quitarán también sus permisos. Un rol con usuarios asignados no se puede eliminar.
  </ConfirmDeleteModal>

  <ConfirmDeleteModal
    :open="moduloAEliminar !== null"
    title="Eliminar módulo"
    :loading="eliminando"
    :error="errorEliminar"
    @close="moduloAEliminar = null"
    @confirm="eliminarModulo"
  >
    ¿Seguro que deseas eliminar el módulo <strong>{{ moduloAEliminar?.nombre_modulo }}</strong
    >? Se quitarán los permisos que tenga asignados en todos los roles.
  </ConfirmDeleteModal>
</template>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.intro {
  max-width: 480px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.alert-error {
  margin-bottom: 12px;
}

.table-card {
  overflow-x: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  padding: 14px 16px;
  background: var(--color-surface-alt);
  border-bottom: 1px solid var(--color-border);
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.col-modulo {
  min-width: 220px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-align: left;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.col-rol {
  min-width: 140px;
}

.rol-nombre {
  display: block;
  margin-bottom: 6px;
}

td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

tbody tr:last-child td {
  border-bottom: none;
}

.fila-usuarios td {
  background: var(--color-surface-alt);
  font-size: 12px;
  font-weight: 600;
}

.fila-usuarios td.centro {
  color: var(--color-primary);
}

.centro {
  text-align: center;
}

.empty {
  padding: 32px;
  text-align: center;
  color: var(--color-text-muted);
}

.botones {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 6px;
}

td:first-child .botones {
  justify-content: flex-start;
}

.action {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.action.edit {
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  color: var(--color-text-muted);
}

.action.edit:hover {
  background: var(--color-border);
}

.action.delete {
  background: var(--color-danger-soft);
  border: 1px solid #efc6c1;
  color: var(--color-danger);
}

.action.delete:hover:not(:disabled) {
  background: #f2cfcb;
}

.check {
  width: 18px;
  height: 18px;
  accent-color: var(--color-primary);
}
</style>
