<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AnimalCard from '@/components/AnimalCard.vue'
import AnimalFormModal from '@/components/AnimalFormModal.vue'
import { consultas } from '@/api/consultas'
import { ApiError } from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { CLASES, ESTADOS_ANIMAL, ESTADOS_EN_CENTRO, nombreClase } from '@/config/animales'
import type { Animal, EstadoAnimal, Recinto, Taxonomia } from '@/types/animales'

const router = useRouter()

const animales = ref<Animal[]>([])
const especies = ref<Taxonomia[]>([])
const recintos = ref<Recinto[]>([])
const cargando = ref(true)
const error = ref('')
const errorMetricas = ref('')
const formAbierto = ref(false)
// Registrar ingresos es solo de Veterinaria y Manejo de Animales
const auth = useAuthStore()
// Todos los ejemplares sin filtros, solo para las métricas de arriba
const todos = ref<Animal[] | null>(null)
const animalesConTratamientoEnCurso = ref<number | null>(null)
const opcionesCargadas = ref(false)

const filtros = reactive({
  buscar: '',
  estado: '' as EstadoAnimal | '',
  id_taxonomia: 0,
  id_recinto: 0,
  clase: '',
})

const ESTADOS = Object.entries(ESTADOS_ANIMAL) as [EstadoAnimal, { label: string }][]

// Un botón por cada clase que tenga especies en el catálogo (Mamíferos, Aves, Reptiles…)
const clases = computed(() => {
  const presentes = new Set(especies.value.map((t) => t.clase).filter((c): c is string => !!c))
  const orden = Object.keys(CLASES)
  const posicion = (c: string) => (orden.includes(c) ? orden.indexOf(c) : orden.length)
  return [...presentes].sort((a, b) => posicion(a) - posicion(b) || a.localeCompare(b))
})

// Evita que una respuesta lenta reemplace a la de filtros más recientes
let consultaActual = 0

async function cargarAnimales() {
  const id = ++consultaActual
  cargando.value = true
  error.value = ''
  try {
    // Si ya se vio esta lista, se muestra al instante y se confirma con la API por detrás
    const resultado = await consultas.animales(
      {
        buscar: filtros.buscar.trim() || undefined,
        estado: filtros.estado || undefined,
        id_taxonomia: filtros.id_taxonomia || undefined,
        id_recinto: filtros.id_recinto || undefined,
        clase: filtros.clase || undefined,
      },
      { alActualizar: (lista) => id === consultaActual && (animales.value = lista) },
    )
    if (id === consultaActual) animales.value = resultado
  } catch (e) {
    if (id === consultaActual) {
      error.value = e instanceof ApiError ? e.message : 'No se pudieron cargar los ejemplares'
    }
  } finally {
    if (id === consultaActual) cargando.value = false
  }
}

async function cargarOpcionesDeFiltro() {
  try {
    ;[especies.value, recintos.value] = await Promise.all([consultas.especies(), consultas.recintos()])
    opcionesCargadas.value = true
  } catch {
    // Sin estas listas solo se pierden los filtros por especie y recinto
  }
}

async function cargarMetricas() {
  errorMetricas.value = ''
  // La lista sin filtros es la misma consulta que la del catálogo al abrir: se pide una sola vez
  const [lista, conteoTratamientos] = await Promise.allSettled([
    consultas.animales({}, { alActualizar: (nueva) => (todos.value = nueva) }),
    consultas.animalesConTratamientoEnCurso({
      alActualizar: (n) => (animalesConTratamientoEnCurso.value = n),
    }),
  ])
  if (lista.status === 'fulfilled') todos.value = lista.value
  else errorMetricas.value = 'No se pudo cargar el total de ejemplares.'
  if (conteoTratamientos.status === 'fulfilled') {
    animalesConTratamientoEnCurso.value = conteoTratamientos.value
  } else {
    errorMetricas.value = [
      errorMetricas.value,
      'No se pudo cargar el conteo de tratamientos en curso.',
    ]
      .filter(Boolean)
      .join(' ')
  }
}

const metricas = computed(() => {
  const formato = (n: number | null) => (n === null ? '—' : new Intl.NumberFormat('es-EC').format(n))
  const lista = todos.value
  return [
    {
      etiqueta: 'ejemplares en el centro',
      valor: formato(lista ? lista.filter((a) => ESTADOS_EN_CENTRO.includes(a.estado_actual)).length : null),
    },
    { etiqueta: 'recintos', valor: formato(opcionesCargadas.value ? recintos.value.length : null) },
    {
      etiqueta: 'animales con tratamientos en curso',
      valor: formato(animalesConTratamientoEnCurso.value),
    },
  ]
})

// El texto espera a que el usuario deje de escribir; los demás filtros se aplican al instante
let temporizador: ReturnType<typeof setTimeout> | undefined
watch(
  () => filtros.buscar,
  () => {
    clearTimeout(temporizador)
    temporizador = setTimeout(cargarAnimales, 300)
  },
)
watch(() => [filtros.estado, filtros.id_taxonomia, filtros.id_recinto, filtros.clase], cargarAnimales)
onBeforeUnmount(() => clearTimeout(temporizador))

function onRegistrado(animal: Animal, aviso?: string) {
  formAbierto.value = false
  // Si la foto no se pudo subir, la ficha lo muestra al abrirse
  router.push({ name: 'ficha-animal', params: { id: animal.id_animal }, query: aviso ? { aviso } : {} })
}

onMounted(() => {
  cargarAnimales()
  cargarOpcionesDeFiltro()
  cargarMetricas()
})
</script>

<template>
  <!-- Métricas generales del centro (sin aplicar filtros) -->
  <div class="metricas">
    <article v-for="m in metricas" :key="m.etiqueta" class="metrica">
      <strong>{{ m.valor }}</strong>
      <span>{{ m.etiqueta }}</span>
    </article>
  </div>
  <p v-if="errorMetricas" class="alert-error" role="alert">{{ errorMetricas }}</p>

  <!-- Una sola fila: filtros a la izquierda; buscador y registrar ingreso a la derecha -->
  <div class="toolbar">
    <div class="filtros">
      <div class="chips" role="group" aria-label="Filtrar por clase">
        <button :class="{ activo: !filtros.clase }" @click="filtros.clase = ''">Todas</button>
        <button
          v-for="clase in clases"
          :key="clase"
          :class="{ activo: filtros.clase === clase }"
          @click="filtros.clase = clase"
        >
          {{ nombreClase(clase) }}
        </button>
      </div>

      <select v-model.number="filtros.id_taxonomia" class="input select" aria-label="Filtrar por especie">
        <option :value="0">Todas las especies</option>
        <option v-for="t in especies" :key="t.id_taxonomia" :value="t.id_taxonomia">{{ t.nombre_comun }}</option>
      </select>

      <select v-model.number="filtros.id_recinto" class="input select" aria-label="Filtrar por recinto">
        <option :value="0">Todos los recintos</option>
        <option v-for="r in recintos" :key="r.id_recinto" :value="r.id_recinto">{{ r.nombre_recinto }}</option>
      </select>

      <select v-model="filtros.estado" class="input select" aria-label="Filtrar por estado">
        <option value="">Todos los estados</option>
        <option v-for="[valor, { label }] in ESTADOS" :key="valor" :value="valor">{{ label }}</option>
      </select>
    </div>

    <div class="acciones">
      <label class="search">
        <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
          <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2" />
          <path d="m20 20-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
        <input
          v-model="filtros.buscar"
          type="search"
          placeholder="Buscar por nombre, código o especie…"
          aria-label="Buscar ejemplares"
        />
      </label>
      <button v-if="auth.permisos.gestionarFichas" class="btn btn-primary registrar" @click="formAbierto = true">
        + Registrar ingreso
      </button>
    </div>
  </div>

  <p v-if="error" class="alert-error">{{ error }}</p>

  <p v-if="cargando && animales.length === 0" class="vacio">Cargando ejemplares…</p>
  <p v-else-if="!cargando && animales.length === 0 && !error" class="vacio">
    No hay ejemplares que coincidan con los filtros.
  </p>

  <div class="grid" :class="{ atenuado: cargando }">
    <AnimalCard v-for="a in animales" :key="a.id_animal" :animal="a" />
  </div>

  <AnimalFormModal :open="formAbierto" :animal="null" @close="formAbierto = false" @saved="onRegistrado" />
</template>

<style scoped>
.metricas {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.metrica {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.metrica strong {
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
}

.metrica span {
  font-size: 13px;
  color: var(--color-text-muted);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px 16px;
  margin-bottom: 20px;
}

.filtros,
.acciones {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.acciones {
  flex: 1 1 360px;
  justify-content: flex-end;
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 220px;
  min-width: 200px;
  max-width: 320px;
  height: 40px;
  padding: 0 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  color: var(--color-text-subtle);
}

.search input {
  flex: 1;
  min-width: 0;
  border: none;
  background: none;
  outline: none;
}

.select {
  width: auto;
  min-width: 0;
  height: 40px;
  padding: 0 10px;
  background: var(--color-surface);
}

.registrar {
  flex-shrink: 0;
  height: 40px;
  padding: 0 18px;
  white-space: nowrap;
}

.chips {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 2px;
  padding: 3px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.chips button {
  height: 32px;
  padding: 0 12px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.chips button:hover:not(.activo) {
  background: var(--color-surface-alt);
  color: var(--color-text);
}

.chips button.activo {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  transition: opacity 0.15s;
}

.grid.atenuado {
  opacity: 0.6;
}

.vacio {
  padding: 48px;
  text-align: center;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
}

.alert-error {
  margin-bottom: 16px;
}

@media (max-width: 640px) {
  .metricas {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .acciones,
  .search {
    flex: 1 1 100%;
    max-width: none;
  }
}
</style>
