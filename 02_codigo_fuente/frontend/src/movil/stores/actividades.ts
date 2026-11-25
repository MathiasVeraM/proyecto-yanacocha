import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { actividadesApi, planificacionReferenciasApi } from '@/api/actividades'
import { describirActividades, sumarDias } from '@/config/actividades'
import { useAuthStore } from '@/stores/auth'
import type { Actividad, Dieta, ReferenciasPlanificacion } from '@/types/actividades'
import { claves, guardar, leer } from '../offline/almacen'
import { ahoraCentro } from '../offline/tiempo'
import { useSincronizacionStore } from './sincronizacion'

// Hasta cuántos días atrás se muestran actividades pendientes (las "atrasadas")
const DIAS_ATRAS = 7

interface DatosGuardados {
  actividades: Actividad[]
  referencias: ReferenciasPlanificacion
  dietas: Dieta[]
  guardado: string
}

const VACIAS: ReferenciasPlanificacion = { animales: [], recintos: [], usuarios: [] }

export const useActividadesMovilStore = defineStore('actividadesMovil', () => {
  const auth = useAuthStore()
  const sync = useSincronizacionStore()

  const base = ref<Actividad[]>([])
  const referencias = ref<ReferenciasPlanificacion>(VACIAS)
  const dietas = ref<Dieta[]>([])
  const cargando = ref(false)
  // Fecha de la última copia traída del servidor (se muestra si lo que se ve es lo guardado)
  const actualizado = ref<string | null>(null)
  const hoy = ref(ahoraCentro().fecha)

  // Lo marcado en el teléfono se ve como hecho aunque todavía no se haya enviado
  const actividades = computed<Actividad[]>(() =>
    base.value
      .map((a) => {
        const local = sync.completadasPendientes.get(a.id_actividad)
        return local && !a.completada
          ? { ...a, completada: true, fecha_completada: local.fecha_completada }
          : a
      })
      .sort((a, b) =>
        `${a.fecha_programada} ${a.hora_programada ?? ''}`.localeCompare(
          `${b.fecha_programada} ${b.hora_programada ?? ''}`,
        ),
      ),
  )

  const describir = computed(() =>
    describirActividades({
      animales: referencias.value.animales,
      recintos: referencias.value.recintos,
      usuarios: referencias.value.usuarios,
      dietasPorId: Object.fromEntries(dietas.value.map((d) => [d.id_dieta, d])),
    }),
  )

  // Primero lo guardado en el teléfono (instantáneo y funciona sin conexión); luego se intenta
  // traer lo último del servidor y se guarda para la próxima vez.
  async function cargar() {
    const id = auth.payload?.id_usuario
    if (!id) return
    hoy.value = ahoraCentro().fecha
    cargando.value = true

    if (!base.value.length) {
      const guardados = await leer<DatosGuardados | null>(claves.datos(id), null)
      if (guardados) {
        base.value = guardados.actividades
        referencias.value = guardados.referencias
        dietas.value = guardados.dietas
        actualizado.value = guardados.guardado
      }
    }

    try {
      const [lista, refs, listaDietas] = await Promise.all([
        actividadesApi.listar({
          fecha_desde: sumarDias(hoy.value, -DIAS_ATRAS),
          fecha_hasta: hoy.value,
        }),
        planificacionReferenciasApi.todas(),
        actividadesApi.listarDietas(),
      ])
      base.value = lista
      referencias.value = refs
      dietas.value = listaDietas
      actualizado.value = ahoraCentro().iso
      await guardar(claves.datos(id), {
        actividades: lista,
        referencias: refs,
        dietas: listaDietas,
        guardado: actualizado.value,
      } satisfies DatosGuardados)
    } catch {
      // Sin conexión: se sigue con lo guardado
    } finally {
      cargando.value = false
    }
  }

  // El servidor confirmó lo marcado en el teléfono: se deja como hecho sin esperar otra descarga
  function confirmarCompletadas(operaciones: { id_actividad: number; fecha_completada: string }[]) {
    for (const op of operaciones) {
      const actividad = base.value.find((a) => a.id_actividad === op.id_actividad)
      if (actividad && !actividad.completada) {
        actividad.completada = true
        actividad.fecha_completada = op.fecha_completada
      }
    }
  }

  function limpiar() {
    base.value = []
    referencias.value = VACIAS
    dietas.value = []
    actualizado.value = null
  }

  return { actividades, describir, referencias, cargando, actualizado, hoy, cargar, confirmarCompletadas, limpiar }
})
