<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AnimalCard from '@/components/AnimalCard.vue'
import AnimalFormModal from '@/components/AnimalFormModal.vue'
import { animalesApi, recintosApi, taxonomiaApi } from '@/api/animales'
import { ApiError } from '@/api/http'
import { ESTADOS_ANIMAL } from '@/config/animales'
import type { Animal, EstadoAnimal, Recinto, Taxonomia } from '@/types/animales'

const router = useRouter()

const animales = ref<Animal[]>([])
const especies = ref<Taxonomia[]>([])
const recintos = ref<Recinto[]>([])
const cargando = ref(true)
const error = ref('')
const formAbierto = ref(false)

const filtros = reactive({
  buscar: '',
  estado: '' as EstadoAnimal | '',
  id_taxonomia: 0,
  id_recinto: 0,
})

const ESTADOS = Object.entries(ESTADOS_ANIMAL) as [EstadoAnimal, { label: string }][]

// Evita que una respuesta lenta reemplace a la de filtros más recientes
let consultaActual = 0

async function cargarAnimales() {
  const id = ++consultaActual
  cargando.value = true
  error.value = ''
  try {
    const resultado = await animalesApi.listar({
      buscar: filtros.buscar.trim() || undefined,
      estado: filtros.estado || undefined,
      id_taxonomia: filtros.id_taxonomia || undefined,
      id_recinto: filtros.id_recinto || undefined,
    })
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
    ;[especies.value, recintos.value] = await Promise.all([taxonomiaApi.listar(), recintosApi.listar()])
  } catch {
    // Sin estas listas solo se pierden los filtros por especie y recinto
  }
}

// El texto espera a que el usuario deje de escribir; los demás filtros se aplican al instante
let temporizador: ReturnType<typeof setTimeout> | undefined
watch(
  () => filtros.buscar,
  () => {
    clearTimeout(temporizador)
    temporizador = setTimeout(cargarAnimales, 300)
  },
)
watch(() => [filtros.estado, filtros.id_taxonomia, filtros.id_recinto], cargarAnimales)
onBeforeUnmount(() => clearTimeout(temporizador))

function onRegistrado(animal: Animal, aviso?: string) {
  formAbierto.value = false
  // Si la foto no se pudo subir, la ficha lo muestra al abrirse
  router.push({ name: 'ficha-animal', params: { id: animal.id_animal }, query: aviso ? { aviso } : {} })
}

onMounted(() => {
  cargarAnimales()
  cargarOpcionesDeFiltro()
})
</script>

<template>
  <div class="toolbar">
    <label class="search">
      <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
        <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2" />
        <path d="m20 20-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
      <input v-model="filtros.buscar" type="search" placeholder="Buscar por código o nombre común…" />
    </label>

    <select v-model.number="filtros.id_taxonomia" class="input select" aria-label="Filtrar por especie">
      <option :value="0">Todas las especies</option>
      <option v-for="t in especies" :key="t.id_taxonomia" :value="t.id_taxonomia">{{ t.nombre_comun }}</option>
    </select>

    <select v-model.number="filtros.id_recinto" class="input select" aria-label="Filtrar por recinto">
      <option :value="0">Todos los recintos</option>
      <option v-for="r in recintos" :key="r.id_recinto" :value="r.id_recinto">{{ r.nombre_recinto }}</option>
    </select>

    <button class="btn btn-primary registrar" @click="formAbierto = true">+ Registrar ingreso</button>
  </div>

  <div class="chips" role="group" aria-label="Filtrar por estado">
    <button :class="{ activo: !filtros.estado }" @click="filtros.estado = ''">Todos</button>
    <button
      v-for="[valor, { label }] in ESTADOS"
      :key="valor"
      :class="{ activo: filtros.estado === valor }"
      @click="filtros.estado = valor"
    >
      {{ label }}
    </button>
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
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 220px;
  padding: 10px 14px;
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
  min-width: 170px;
  padding: 10px 12px;
  background: var(--color-surface);
}

.registrar {
  margin-left: auto;
  padding: 11px 18px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0 20px;
}

.chips button {
  padding: 8px 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-size: 13px;
  font-weight: 500;
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
</style>
