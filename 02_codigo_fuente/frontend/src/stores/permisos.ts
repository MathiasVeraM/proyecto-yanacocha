import { ref } from 'vue'
import { defineStore } from 'pinia'
import { permisosApi } from '@/api/permisos'
import type { MatrizPermisos } from '@/types'

// Matriz roles × módulos que se muestra en "Permisos por roles"
export const usePermisosStore = defineStore('permisos', () => {
  const matriz = ref<MatrizPermisos>({ roles: [], modulos: [], permisos: [] })

  async function cargar() {
    matriz.value = await permisosApi.matriz()
  }

  function tiene(idRol: number, idModulo: number) {
    return matriz.value.permisos.some((p) => p.id_rol === idRol && p.id_modulo === idModulo)
  }

  // Actualiza la casilla al instante y revierte el cambio si la API lo rechaza
  async function alternar(idRol: number, idModulo: number) {
    const permisosAnteriores = matriz.value.permisos
    if (tiene(idRol, idModulo)) {
      matriz.value.permisos = permisosAnteriores.filter(
        (p) => !(p.id_rol === idRol && p.id_modulo === idModulo),
      )
    } else {
      matriz.value.permisos = [...permisosAnteriores, { id_rol: idRol, id_modulo: idModulo }]
    }

    try {
      if (tiene(idRol, idModulo)) await permisosApi.asignar(idRol, idModulo)
      else await permisosApi.quitar(idRol, idModulo)
    } catch (e) {
      matriz.value.permisos = permisosAnteriores
      throw e
    }
  }

  return { matriz, cargar, tiene, alternar }
})
