import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { Network } from '@capacitor/network'
import { actividadesApi } from '@/api/actividades'
import { ApiError } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import type { CategoriaObservacion, SeveridadObservacion } from '@/types/actividades'
import { claves, guardar, leer } from '../offline/almacen'
import { ahoraCentro, nuevoId } from '../offline/tiempo'
import type { CompletarPendiente, OperacionPendiente, OperacionRechazada } from '../offline/tipos'

// Mientras haya algo pendiente se reintenta con esta frecuencia (la meta es sincronizar en < 5 min)
const REINTENTO_MS = 30_000
const MAX_POR_LOTE = 200

export const useSincronizacionStore = defineStore('sincronizacion', () => {
  const auth = useAuthStore()

  const pendientes = ref<OperacionPendiente[]>([])
  const rechazadas = ref<OperacionRechazada[]>([])
  // Lo que informa el sistema operativo; el envío real puede fallar aunque diga "conectado"
  const hayRed = ref(true)
  const sincronizando = ref(false)
  const ultimoEnvio = ref<string | null>(null)
  const errorEnvio = ref('')

  let idUsuario: number | null = null
  let temporizador: ReturnType<typeof setInterval> | null = null
  // Se llama cuando el servidor confirmó cambios, para refrescar lo que se ve
  let alSincronizar: ((confirmadas: CompletarPendiente[]) => void) | null = null

  const totalPendientes = computed(() => pendientes.value.length)
  const completadasPendientes = computed(
    () => new Map(pendientes.value.filter((o) => o.tipo === 'completar').map((o) => [o.id_actividad, o])),
  )
  const observacionesPorActividad = computed(() => {
    const cuenta = new Map<number, number>()
    for (const o of pendientes.value) {
      if (o.tipo === 'observacion') cuenta.set(o.id_actividad, (cuenta.get(o.id_actividad) ?? 0) + 1)
    }
    return cuenta
  })

  async function guardarCola() {
    if (idUsuario !== null) {
      await guardar(claves.cola(idUsuario), pendientes.value)
      await guardar(claves.rechazadas(idUsuario), rechazadas.value)
    }
  }

  // Arranca con la sesión: carga lo que quedó guardado, vigila la red y reintenta
  async function iniciar(alConfirmar: (confirmadas: CompletarPendiente[]) => void) {
    const id = auth.payload?.id_usuario
    if (!id) return
    idUsuario = id
    alSincronizar = alConfirmar
    pendientes.value = await leer<OperacionPendiente[]>(claves.cola(id), [])
    rechazadas.value = await leer<OperacionRechazada[]>(claves.rechazadas(id), [])

    try {
      hayRed.value = (await Network.getStatus()).connected
      await Network.addListener('networkStatusChange', (estado) => {
        hayRed.value = estado.connected
        // Volvió la señal: se envía enseguida
        if (estado.connected) void sincronizar()
      })
    } catch {
      hayRed.value = true
    }

    temporizador ??= setInterval(() => {
      if (pendientes.value.length && auth.isAuthenticated) void sincronizar()
    }, REINTENTO_MS)
    void sincronizar()
  }

  async function detener() {
    if (temporizador) clearInterval(temporizador)
    temporizador = null
    idUsuario = null
    alSincronizar = null
    pendientes.value = []
    rechazadas.value = []
    try {
      await Network.removeAllListeners()
    } catch {
      // nada que limpiar
    }
  }

  async function marcarHecha(idActividad: number, observaciones?: string) {
    if (completadasPendientes.value.has(idActividad)) return
    pendientes.value.push({
      tipo: 'completar',
      id_local: nuevoId(),
      id_actividad: idActividad,
      fecha_completada: ahoraCentro().iso,
      observaciones: observaciones?.trim() || undefined,
    })
    await guardarCola()
    void sincronizar()
  }

  async function observar(
    idActividad: number,
    datos: { categoria: CategoriaObservacion; severidad: SeveridadObservacion; detalle: string },
  ) {
    pendientes.value.push({
      tipo: 'observacion',
      id_cliente: nuevoId(),
      id_actividad: idActividad,
      ...datos,
      fecha_registro: ahoraCentro().iso,
    })
    await guardarCola()
    void sincronizar()
  }

  async function descartarRechazada(id: string) {
    rechazadas.value = rechazadas.value.filter((r) => r.id !== id)
    await guardarCola()
  }

  // Envía todo lo pendiente. Es seguro repetirlo: el servidor no duplica nada.
  async function sincronizar() {
    if (sincronizando.value || !pendientes.value.length || !hayRed.value || !auth.isAuthenticated) return
    sincronizando.value = true
    errorEnvio.value = ''
    try {
      while (pendientes.value.length) {
        const lote = pendientes.value.slice(0, MAX_POR_LOTE)
        const completadas = lote.filter((o) => o.tipo === 'completar')
        const observaciones = lote.filter((o) => o.tipo === 'observacion')

        const respuesta = await actividadesApi.sincronizar({
          completadas: completadas.map((o) => ({
            id_actividad: o.id_actividad,
            fecha_completada: o.fecha_completada,
            observaciones: o.observaciones,
          })),
          observaciones: observaciones.map((o) => ({
            id_cliente: o.id_cliente,
            id_actividad: o.id_actividad,
            categoria: o.categoria,
            severidad: o.severidad,
            detalle: o.detalle,
            fecha_registro: o.fecha_registro,
          })),
        })

        // creada y duplicada: ya está en el servidor. rechazada: no se puede guardar nunca;
        // se quita de la cola (si no, bloquearía los envíos) y se avisa a la persona.
        const resueltas = new Set<OperacionPendiente>()
        const resolver = (ops: OperacionPendiente[], resultados: typeof respuesta.completadas) => {
          resultados.forEach((resultado, i) => {
            const op = ops[i]
            if (!op) return
            resueltas.add(op)
            if (resultado.resultado === 'rechazada') {
              rechazadas.value.unshift({
                id: nuevoId(),
                tipo: op.tipo,
                id_actividad: op.id_actividad,
                motivo: resultado.detalle ?? 'El servidor no pudo guardar el registro',
                fecha: ahoraCentro().iso,
              })
            }
          })
        }
        resolver(completadas, respuesta.completadas)
        resolver(observaciones, respuesta.observaciones)

        pendientes.value = pendientes.value.filter((o) => !resueltas.has(o))
        await guardarCola()
        ultimoEnvio.value = ahoraCentro().iso
        alSincronizar?.(
          [...resueltas].filter((o): o is CompletarPendiente => o.tipo === 'completar'),
        )
        if (!resueltas.size) break
      }
    } catch (e) {
      // Sin conexión o servidor caído: todo queda guardado en el teléfono para el próximo intento
      errorEnvio.value =
        e instanceof ApiError && e.status !== 0 && e.status < 500
          ? e.message
          : 'Sin conexión con el servidor. Se enviará automáticamente.'
    } finally {
      sincronizando.value = false
    }
  }

  return {
    pendientes,
    rechazadas,
    hayRed,
    sincronizando,
    ultimoEnvio,
    errorEnvio,
    totalPendientes,
    completadasPendientes,
    observacionesPorActividad,
    iniciar,
    detener,
    marcarHecha,
    observar,
    descartarRechazada,
    sincronizar,
  }
})
