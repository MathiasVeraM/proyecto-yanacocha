import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { actividadesApi, planificacionReferenciasApi } from '@/api/actividades'
import { describirActividades, lunesDe, sumarDias } from '@/config/actividades'
import { useAuthStore } from '@/stores/auth'
import type { Actividad, Dieta, ReferenciasPlanificacion } from '@/types/actividades'
import { claves, guardar, leer } from '../offline/almacen'
import { ahoraCentro } from '../offline/tiempo'
import { useSincronizacionStore } from './sincronizacion'

// Lo que se conserva en el teléfono para el calendario: días atrás desde hoy
const DIAS_GUARDADOS = 60

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

  // Por id: cada semana que se consulta se mezcla con lo que ya había
  const porId = ref<Record<number, Actividad>>({})
  const referencias = ref<ReferenciasPlanificacion>(VACIAS)
  const dietas = ref<Dieta[]>([])
  const cargando = ref(false)
  // Fecha de la última copia traída del servidor (se muestra si lo que se ve es lo guardado)
  const actualizado = ref<string | null>(null)
  const hoy = ref(ahoraCentro().fecha)
  // Semanas (lunes) ya traídas del servidor en esta sesión
  const semanasCargadas = new Set<string>()

  // Lo marcado en el teléfono se ve como hecho aunque todavía no se haya enviado
  const actividades = computed<Actividad[]>(() =>
    Object.values(porId.value)
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

  const delDia = (fecha: string) => actividades.value.filter((a) => a.fecha_programada === fecha)

  const describir = computed(() =>
    describirActividades({
      animales: referencias.value.animales,
      recintos: referencias.value.recintos,
      usuarios: referencias.value.usuarios,
      dietasPorId: Object.fromEntries(dietas.value.map((d) => [d.id_dieta, d])),
    }),
  )

  function mezclar(lista: Actividad[], desde: string, hasta: string) {
    // Dentro del rango consultado, lo que ya no viene del servidor se eliminó allí
    const siguiente: Record<number, Actividad> = {}
    for (const a of Object.values(porId.value)) {
      if (a.fecha_programada < desde || a.fecha_programada > hasta) siguiente[a.id_actividad] = a
    }
    for (const a of lista) siguiente[a.id_actividad] = a
    porId.value = siguiente
  }

  async function persistir() {
    const id = auth.payload?.id_usuario
    if (!id) return
    const limite = sumarDias(hoy.value, -DIAS_GUARDADOS)
    await guardar(claves.datos(id), {
      actividades: Object.values(porId.value).filter((a) => a.fecha_programada >= limite),
      referencias: referencias.value,
      dietas: dietas.value,
      guardado: actualizado.value ?? ahoraCentro().iso,
    } satisfies DatosGuardados)
  }

  // Primero lo guardado en el teléfono (instantáneo y funciona sin conexión); luego se intenta
  // traer lo último del servidor y se guarda para la próxima vez.
  async function cargar() {
    const id = auth.payload?.id_usuario
    if (!id) return
    hoy.value = ahoraCentro().fecha
    cargando.value = true

    if (!Object.keys(porId.value).length) {
      const guardados = await leer<DatosGuardados | null>(claves.datos(id), null)
      if (guardados) {
        porId.value = Object.fromEntries(guardados.actividades.map((a) => [a.id_actividad, a]))
        referencias.value = guardados.referencias
        dietas.value = guardados.dietas
        actualizado.value = guardados.guardado
      }
    }

    try {
      const desde = lunesDe(hoy.value)
      const hasta = sumarDias(desde, 6)
      const [lista, refs, listaDietas] = await Promise.all([
        actividadesApi.listar({ fecha_desde: desde, fecha_hasta: hasta }),
        planificacionReferenciasApi.todas(),
        actividadesApi.listarDietas(),
      ])
      mezclar(lista, desde, hasta)
      semanasCargadas.add(desde)
      referencias.value = refs
      dietas.value = listaDietas
      actualizado.value = ahoraCentro().iso
      await persistir()
    } catch {
      // Sin conexión: se sigue con lo guardado
    } finally {
      cargando.value = false
    }
  }

  // Calendario: trae la semana de esa fecha si todavía no se tenía (sin conexión se ve lo guardado)
  async function cargarSemana(fecha: string, forzar = false) {
    const desde = lunesDe(fecha)
    if (semanasCargadas.has(desde) && !forzar) return
    cargando.value = true
    try {
      mezclar(await actividadesApi.listar({ fecha_desde: desde, fecha_hasta: sumarDias(desde, 6) }), desde, sumarDias(desde, 6))
      semanasCargadas.add(desde)
      actualizado.value = ahoraCentro().iso
      await persistir()
    } catch {
      // Sin conexión: se muestra lo que haya guardado de esa semana
    } finally {
      cargando.value = false
    }
  }

  // El servidor confirmó lo marcado en el teléfono: se deja como hecho sin esperar otra descarga
  function confirmarCompletadas(operaciones: { id_actividad: number; fecha_completada: string }[]) {
    for (const op of operaciones) {
      const actividad = porId.value[op.id_actividad]
      if (actividad && !actividad.completada) {
        actividad.completada = true
        actividad.fecha_completada = op.fecha_completada
      }
    }
  }

  function limpiar() {
    porId.value = {}
    referencias.value = VACIAS
    dietas.value = []
    actualizado.value = null
    semanasCargadas.clear()
  }

  return {
    actividades,
    delDia,
    describir,
    referencias,
    cargando,
    actualizado,
    hoy,
    cargar,
    cargarSemana,
    confirmarCompletadas,
    limpiar,
  }
})
