<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import ActividadFormModal from '@/components/ActividadFormModal.vue'
import CalendarioPlanificacion from '@/components/CalendarioPlanificacion.vue'
import ChecklistPlanificacion from '@/components/ChecklistPlanificacion.vue'
import DietaFormPanel from '@/components/DietaFormPanel.vue'
import DietasPlanificacion from '@/components/DietasPlanificacion.vue'
import MonitoreoAlimentacion from '@/components/MonitoreoAlimentacion.vue'
import { actividadesApi, planificacionReferenciasApi } from '@/api/actividades'
import { ApiError } from '@/api/http'
import { hoyIso } from '@/config/animales'
import { useAuthStore } from '@/stores/auth'
import type {
  Actividad,
  Dieta,
  EventoCalendario,
  UsuarioActividad,
} from '@/types/actividades'
import type { Animal, Recinto } from '@/types/animales'

type Pestana = 'checklist' | 'calendario' | 'monitoreo' | 'dietas'

const auth = useAuthStore()
const pestana = ref<Pestana>('checklist')
const animales = ref<Animal[]>([])
const recintos = ref<Recinto[]>([])
const usuariosAuditoria = ref<UsuarioActividad[]>([])
const actividades = ref<Actividad[]>([])
const dietasPorAnimal = ref<Record<number, Dieta[]>>({})
const extrasPorDieta = ref<Record<number, { unidades: ('g' | 'kg' | 'unidad')[]; restriccion: boolean }>>({})
const cargandoReferencias = ref(false)
const cargandoActividades = ref(false)
const cargandoDietas = ref(false)
const actualizandoId = ref<number | null>(null)
const errorReferencias = ref('')
const errorActividades = ref('')
const errorDietas = ref('')
const formularioActividadAbierto = ref(false)
const formularioDietaAbierto = ref(false)
const hoy = hoyIso()

const pestañas: { id: Pestana; texto: string }[] = [
  { id: 'checklist', texto: 'Checklist' },
  { id: 'calendario', texto: 'Calendario' },
  { id: 'monitoreo', texto: 'Monitoreo de alimentación' },
  { id: 'dietas', texto: 'Registro de Dietas' },
]

function fechaLocal(fecha: Date): string {
  return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}-${String(fecha.getDate()).padStart(2, '0')}`
}

function lunesDe(fecha: Date): Date {
  const lunes = new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate(), 12)
  lunes.setDate(lunes.getDate() - ((lunes.getDay() + 6) % 7))
  return lunes
}

const inicioSemana = ref(lunesDe(new Date()))
const diasSemana = computed(() =>
  Array.from({ length: 7 }, (_, indice) => {
    const fecha = new Date(inicioSemana.value)
    fecha.setDate(fecha.getDate() + indice)
    const fechaIso = fechaLocal(fecha)
    const diaCompleto = new Intl.DateTimeFormat('es-EC', {
      weekday: 'long',
      day: 'numeric',
    }).format(fecha)
    return {
      fecha: fechaIso,
      etiqueta: diaCompleto,
      numero: fecha.getDate(),
      corto: new Intl.DateTimeFormat('es-EC', { weekday: 'short' }).format(fecha),
      esHoy: fechaIso === hoyIso(),
    }
  }),
)

const dietasVigentes = computed(() => {
  const resultado: Record<number, Dieta> = {}
  for (const [idAnimal, historial] of Object.entries(dietasPorAnimal.value)) {
    const vigente = historial.find((dieta) => dieta.vigente)
    if (vigente) resultado[Number(idAnimal)] = vigente
  }
  return resultado
})

const dietasPorId = computed(() => {
  const resultado: Record<number, Dieta> = {}
  for (const historial of Object.values(dietasPorAnimal.value)) {
    for (const dieta of historial) resultado[dieta.id_dieta] = dieta
  }
  return resultado
})

function mensajeError(error: unknown, predeterminado: string) {
  return error instanceof ApiError ? error.message : predeterminado
}

async function cargarReferencias() {
  cargandoReferencias.value = true
  errorReferencias.value = ''
  const [resultadoAnimales, resultadoRecintos, resultadoUsuarios] = await Promise.allSettled([
    planificacionReferenciasApi.animales(),
    planificacionReferenciasApi.recintos(),
    planificacionReferenciasApi.usuariosAuditoria(),
  ])
  const errores: string[] = []

  if (resultadoAnimales.status === 'fulfilled') animales.value = resultadoAnimales.value
  else errores.push(`ejemplares: ${mensajeError(resultadoAnimales.reason, 'no se pudieron cargar')}`)

  if (resultadoRecintos.status === 'fulfilled') recintos.value = resultadoRecintos.value
  else errores.push(`recintos: ${mensajeError(resultadoRecintos.reason, 'no se pudieron cargar')}`)

  if (resultadoUsuarios.status === 'fulfilled') usuariosAuditoria.value = resultadoUsuarios.value
  else errores.push(`usuarios para auditoría: ${mensajeError(resultadoUsuarios.reason, 'no se pudieron cargar')}`)

  errorReferencias.value = errores.length
    ? `No se pudieron cargar algunos datos de referencia (${errores.join('; ')}).`
    : ''
  cargandoReferencias.value = false
}

async function cargarDietas() {
  if (!animales.value.length) {
    dietasPorAnimal.value = {}
    return
  }

  cargandoDietas.value = true
  errorDietas.value = ''
  const resultados = await Promise.allSettled(
    animales.value.map(async (animal) => ({
      idAnimal: animal.id_animal,
      dietas: await actividadesApi.dietasPorAnimal(animal.id_animal),
    })),
  )
  const siguientes: Record<number, Dieta[]> = {}
  const errores: string[] = []

  resultados.forEach((resultado, indice) => {
    if (resultado.status === 'fulfilled') {
      siguientes[resultado.value.idAnimal] = resultado.value.dietas
    } else {
      const animal = animales.value[indice]
      errores.push(
        `${animal?.nombre ?? animal?.taxonomia.nombre_comun ?? 'un ejemplar'}: ${mensajeError(resultado.reason, 'no se pudo cargar su historial')}`,
      )
    }
  })

  dietasPorAnimal.value = siguientes
  errorDietas.value = errores.length
    ? `No se pudieron cargar todos los historiales de dieta (${errores.join('; ')}).`
    : ''
  cargandoDietas.value = false
}

async function cargarActividades(fechaDesde: string, fechaHasta: string) {
  cargandoActividades.value = true
  errorActividades.value = ''
  try {
    const [lista, eventos] = await Promise.all([
      actividadesApi.listar({ fecha_desde: fechaDesde, fecha_hasta: fechaHasta }),
      actividadesApi.calendario(fechaDesde, fechaHasta),
    ])
    const idsEnCalendario = new Set(eventos.map((evento: EventoCalendario) => evento.id_actividad))
    actividades.value = lista.filter((actividad) => idsEnCalendario.has(actividad.id_actividad))
  } catch (error) {
    errorActividades.value = mensajeError(error, 'No se pudieron cargar las actividades.')
    actividades.value = []
  } finally {
    cargandoActividades.value = false
  }
}

async function cargarPestanaActiva() {
  if (pestana.value === 'calendario') {
    const dias = diasSemana.value
    if (dias.length) await cargarActividades(dias[0]!.fecha, dias[6]!.fecha)
  } else if (pestana.value === 'checklist' || pestana.value === 'monitoreo') {
    await cargarActividades(hoy, hoy)
  }
}

function cambiarSemana(delta: number) {
  const nueva = new Date(inicioSemana.value)
  nueva.setDate(nueva.getDate() + delta * 7)
  inicioSemana.value = nueva
  void cargarActividades(fechaLocal(nueva), fechaLocal(new Date(nueva.getFullYear(), nueva.getMonth(), nueva.getDate() + 6, 12)))
}

function irAHoy() {
  inicioSemana.value = lunesDe(new Date())
  void cargarPestanaActiva()
}

async function completarActividad(id: number, observaciones?: string) {
  const original = actividades.value.find((actividad) => actividad.id_actividad === id)
  if (!original || original.completada || actualizandoId.value !== null) return

  const usuarioId = auth.payload?.id_usuario ?? null
  actualizandoId.value = id
  errorActividades.value = ''
  actividades.value = actividades.value.map((actividad) =>
    actividad.id_actividad === id
      ? {
          ...actividad,
          completada: true,
          observaciones: observaciones ?? actividad.observaciones,
          id_usuario_completo: usuarioId,
          fecha_completada: new Date().toISOString(),
        }
      : actividad,
  )

  try {
    const actualizado = await actividadesApi.completar(id, observaciones)
    actividades.value = actividades.value.map((actividad) =>
      actividad.id_actividad === id ? { ...actividad, ...actualizado } : actividad,
    )
  } catch (error) {
    actividades.value = actividades.value.map((actividad) => (actividad.id_actividad === id ? original : actividad))
    errorActividades.value = mensajeError(error, 'No se pudo completar la actividad. Se restauró su estado anterior.')
  } finally {
    actualizandoId.value = null
  }
}

async function guardarActividad() {
  formularioActividadAbierto.value = false
  await cargarPestanaActiva()
}

async function guardarDieta(dieta: Dieta, extras: { unidades: ('g' | 'kg' | 'unidad')[]; restriccion: boolean }) {
  formularioDietaAbierto.value = false
  extrasPorDieta.value = { ...extrasPorDieta.value, [dieta.id_dieta]: extras }
  await cargarDietas()

  try {
    await actividadesApi.generarTomas(dieta.id_dieta)
  } catch (error) {
    errorDietas.value = `La dieta se registró, pero no se pudieron generar sus tomas: ${mensajeError(error, 'error desconocido')}`
  }

  if (pestana.value === 'checklist' || pestana.value === 'monitoreo') {
    await cargarActividades(hoy, hoy)
  } else if (pestana.value === 'calendario') {
    await cargarPestanaActiva()
  }
}

function cambiarPestana(nueva: Pestana) {
  pestana.value = nueva
  formularioActividadAbierto.value = false
  formularioDietaAbierto.value = false
  if (nueva === 'dietas') void cargarDietas()
  else void cargarPestanaActiva()
}

onMounted(async () => {
  await cargarReferencias()
  await cargarDietas()
  let errorRenovacion = ''
  try {
    await actividadesApi.renovarTomas()
  } catch (error) {
    errorRenovacion = `No se pudo renovar el horizonte de tomas: ${mensajeError(error, 'error desconocido')}`
  }
  await cargarPestanaActiva()
  if (errorRenovacion) {
    errorActividades.value = [errorActividades.value, errorRenovacion].filter(Boolean).join(' ')
  }
})
</script>

<template>
  <main class="planning-page">
    <p v-if="errorReferencias" class="alert-error" role="alert">{{ errorReferencias }}</p>
    <p v-if="cargandoReferencias" class="loading-reference" role="status">Cargando ejemplares, recintos y usuarios…</p>

    <nav class="planning-tabs" role="tablist" aria-label="Secciones de planificación">
      <button
        v-for="tab in pestañas"
        :key="tab.id"
        class="planning-tab"
        :class="{ active: pestana === tab.id }"
        type="button"
        role="tab"
        :aria-selected="pestana === tab.id"
        @click="cambiarPestana(tab.id)"
      >
        {{ tab.texto }}
      </button>
    </nav>

    <section v-show="pestana === 'checklist'" role="tabpanel">
      <ChecklistPlanificacion
        :actividades="actividades"
        :animales="animales"
        :recintos="recintos"
        :usuarios-auditoria="usuariosAuditoria"
        :cargando="cargandoActividades"
        :error="errorActividades"
        :actualizando-id="actualizandoId"
        @completar="completarActividad"
      />
    </section>

    <section v-show="pestana === 'calendario'" role="tabpanel">
      <ActividadFormModal
        :abierto="formularioActividadAbierto"
        :dias="diasSemana"
        :animales="animales"
        :recintos="recintos"
        @close="formularioActividadAbierto = false"
        @saved="guardarActividad"
      />
      <CalendarioPlanificacion
        :dias="diasSemana"
        :actividades="actividades"
        :animales="animales"
        :recintos="recintos"
        :dietas="dietasPorId"
        :cargando="cargandoActividades"
        :error="errorActividades"
        @cambiar-semana="cambiarSemana"
        @hoy="irAHoy"
        @crear="formularioActividadAbierto = true"
      />
    </section>

    <section v-show="pestana === 'monitoreo'" role="tabpanel">
      <MonitoreoAlimentacion
        :actividades="actividades"
        :animales="animales"
        :dietas="dietasPorId"
        :usuarios-auditoria="usuariosAuditoria"
        :cargando="cargandoActividades"
        :error="errorActividades"
        :actualizando-id="actualizandoId"
        @completar="completarActividad"
      />
    </section>

    <section v-show="pestana === 'dietas'" role="tabpanel">
      <DietaFormPanel
        :abierto="formularioDietaAbierto"
        :animales="animales"
        :dietas-vigentes="dietasVigentes"
        :extras-por-dieta="extrasPorDieta"
        @close="formularioDietaAbierto = false"
        @saved="guardarDieta"
      />
      <DietasPlanificacion
        :animales="animales"
        :dietas-vigentes="dietasVigentes"
        :historiales="dietasPorAnimal"
        :extras-por-dieta="extrasPorDieta"
        :cargando="cargandoDietas"
        :error="errorDietas"
        @registrar="formularioDietaAbierto = true"
      />
    </section>
  </main>
</template>

<style scoped>
.planning-page {
  min-width: 0;
}

.loading-reference {
  margin-bottom: 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.planning-tabs {
  display: inline-flex;
  max-width: 100%;
  gap: 4px;
  overflow-x: auto;
  padding: 4px;
  margin-bottom: 24px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  scrollbar-width: thin;
}

.planning-tab {
  flex: 0 0 auto;
  padding: 7px 14px;
  border: 0;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--color-text);
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}

.planning-tab:hover,
.planning-tab:focus-visible {
  color: var(--color-primary);
  outline-color: var(--color-primary);
}

.planning-tab.active {
  background: var(--color-primary);
  color: #fff;
}

.planning-page > section {
  min-width: 0;
}

@media (max-width: 600px) {
  .planning-tabs {
    display: flex;
    margin-bottom: 18px;
  }

  .planning-tab {
    padding: 7px 11px;
  }
}
</style>
