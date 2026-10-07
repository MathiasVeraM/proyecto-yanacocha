import { ref } from 'vue'
import { defineStore } from 'pinia'
import { rolesApi } from '@/api/usuarios'
import type { Rol } from '@/types'

// Catálogo de roles compartido entre el layout, la tabla y el formulario
export const useRolesStore = defineStore('roles', () => {
  const roles = ref<Rol[]>([])

  async function cargar() {
    roles.value = await rolesApi.listar()
  }

  function nombreDe(idRol: number | undefined) {
    return roles.value.find((r) => r.id_rol === idRol)?.nombre_rol ?? '—'
  }

  return { roles, cargar, nombreDe }
})
