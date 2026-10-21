<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AnimalFoto from '@/components/AnimalFoto.vue'
import AnimalFormModal from '@/components/AnimalFormModal.vue'
import AppBadge from '@/components/AppBadge.vue'
import ModuloPlaceholder from '@/components/ModuloPlaceholder.vue'
import SalidaModal from '@/components/SalidaModal.vue'
import { animalesApi } from '@/api/animales'
import { ApiError } from '@/api/http'
import { ESTADOS_ANIMAL, ESTADOS_SALIDA, SEXOS, formatearFecha } from '@/config/animales'
import type { Animal } from '@/types/animales'

const props = defineProps<{ id: string }>()

const animal = ref<Animal | null>(null)
const cargando = ref(true)
const error = ref('')
const tab = ref<'resumen' | 'veterinaria' | 'actividades'>('resumen')
const editarAbierto = ref(false)
const salidaAbierta = ref(false)

const yaSalio = computed(() => !!animal.value && ESTADOS_SALIDA.includes(animal.value.estado_actual))
const estado = computed(() => (animal.value ? ESTADOS_ANIMAL[animal.value.estado_actual] : null))

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    animal.value = await animalesApi.obtener(Number(props.id))
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo cargar la ficha'
  } finally {
    cargando.value = false
  }
}

function onGuardado(actualizado: Animal) {
  animal.value = actualizado
  editarAbierto.value = false
  salidaAbierta.value = false
}

watch(() => props.id, cargar, { immediate: true })
</script>

<template>
  <RouterLink :to="{ name: 'fichas' }" class="volver">‹ Volver a fichas</RouterLink>

  <p v-if="cargando" class="vacio">Cargando ficha…</p>
  <p v-else-if="error" class="alert-error">{{ error }}</p>

  <div v-else-if="animal" class="layout">
    <!-- ---- Tarjeta lateral ---- -->
    <aside class="lateral">
      <AnimalFoto :url="animal.url_imagen" :nombre="animal.taxonomia.nombre_comun" class="foto" />

      <div class="encabezado">
        <h1>{{ animal.taxonomia.nombre_comun }}</h1>
        <AppBadge v-if="estado" :tone="estado.tono">{{ estado.label }}</AppBadge>
      </div>
      <p class="cientifico">{{ animal.taxonomia.especie }}</p>

      <dl class="datos">
        <div>
          <dt>Código</dt>
          <dd class="mono">{{ animal.codigo_animal }}</dd>
        </div>
        <div>
          <dt>Recinto</dt>
          <dd class="mono">{{ animal.recinto.nombre_recinto }}</dd>
        </div>
        <div>
          <dt>Sexo</dt>
          <dd>{{ animal.sexo ? SEXOS[animal.sexo] : '—' }}</dd>
        </div>
        <div>
          <dt>Edad</dt>
          <dd>{{ animal.edad_aproximada ?? '—' }}</dd>
        </div>
      </dl>

      <div class="acciones">
        <button class="btn btn-primary" @click="editarAbierto = true">Editar ficha</button>
        <button class="btn salida" :disabled="yaSalio" @click="salidaAbierta = true">
          {{ yaSalio ? 'Salida registrada' : 'Registrar salida' }}
        </button>
      </div>
    </aside>

    <!-- ---- Contenido ---- -->
    <section class="contenido">
      <nav class="tabs">
        <button :class="{ activo: tab === 'resumen' }" @click="tab = 'resumen'">Resumen</button>
        <button :class="{ activo: tab === 'veterinaria' }" @click="tab = 'veterinaria'">Veterinaria</button>
        <button :class="{ activo: tab === 'actividades' }" @click="tab = 'actividades'">Actividades</button>
      </nav>

      <template v-if="tab === 'resumen'">
        <article class="panel">
          <h2>Ficha técnica completa</h2>
          <dl class="ficha">
            <div>
              <dt>Código</dt>
              <dd class="mono">{{ animal.codigo_animal }} <span class="auto">· auto</span></dd>
            </div>
            <div>
              <dt>Nombre común</dt>
              <dd>{{ animal.taxonomia.nombre_comun }}</dd>
            </div>
            <div>
              <dt>Lugar de estancia</dt>
              <dd class="mono">{{ animal.recinto.nombre_recinto }}</dd>
            </div>
            <div>
              <dt>Nombre científico</dt>
              <dd><em>{{ animal.taxonomia.especie }}</em></dd>
            </div>
            <div>
              <dt>Sexo</dt>
              <dd>{{ animal.sexo ? SEXOS[animal.sexo] : '—' }}</dd>
            </div>
            <div>
              <dt>Género</dt>
              <dd><em>{{ animal.taxonomia.genero ?? '—' }}</em></dd>
            </div>
            <div>
              <dt>Edad</dt>
              <dd>{{ animal.edad_aproximada ?? '—' }}</dd>
            </div>
            <div>
              <dt>Familia</dt>
              <dd>{{ animal.taxonomia.familia ?? '—' }}</dd>
            </div>
            <div>
              <dt>Estado</dt>
              <dd>{{ estado?.label }}</dd>
            </div>
            <div>
              <dt>Fecha de ingreso</dt>
              <dd>{{ formatearFecha(animal.fecha_ingreso) }}</dd>
            </div>
          </dl>
        </article>

        <article class="panel">
          <h2>Línea de vida general</h2>
          <p class="sub">Eventos relevantes del ejemplar, en orden cronológico</p>
          <ol class="linea">
            <li>
              <time>{{ formatearFecha(animal.fecha_ingreso) }}</time>
              <AppBadge tone="green">Ingreso</AppBadge>
              <span>Ingreso al centro · {{ animal.recinto.nombre_recinto }}</span>
            </li>
            <li v-if="yaSalio">
              <time>—</time>
              <AppBadge :tone="estado?.tono">Salida</AppBadge>
              <span>{{ estado?.label }}</span>
            </li>
          </ol>
        </article>
      </template>

      <ModuloPlaceholder
        v-else-if="tab === 'veterinaria'"
        titulo="Veterinaria"
        descripcion="Los diagnósticos y tratamientos del ejemplar estarán disponibles próximamente."
      />
      <ModuloPlaceholder
        v-else
        titulo="Actividades"
        descripcion="Las actividades del ejemplar estarán disponibles próximamente."
      />
    </section>
  </div>

  <AnimalFormModal :open="editarAbierto" :animal="animal" @close="editarAbierto = false" @saved="onGuardado" />
  <SalidaModal :open="salidaAbierta" :animal="animal" @close="salidaAbierta = false" @saved="onGuardado" />
</template>

<style scoped>
.volver {
  display: inline-block;
  margin-bottom: 18px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.volver:hover {
  color: var(--color-text);
}

.layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 24px;
  align-items: start;
}

.lateral,
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.lateral {
  padding: 20px;
}

.foto {
  height: 200px;
  border-radius: var(--radius-md);
}

.encabezado {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
}

h1 {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 600;
}

.cientifico {
  margin-top: 2px;
  font-style: italic;
  color: var(--color-text-muted);
}

dl {
  margin: 0;
}

.datos {
  margin-top: 16px;
}

dl > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

dt {
  color: var(--color-text-muted);
}

dd {
  margin: 0;
  font-weight: 500;
  text-align: right;
}

.mono {
  font-family: ui-monospace, 'Cascadia Code', monospace;
}

.auto {
  font-size: 11px;
  color: var(--color-text-subtle);
}

.acciones {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 18px;
}

.acciones .btn {
  padding: 11px;
}

.salida {
  border: 1px solid var(--color-border-strong);
  background: var(--color-surface);
  color: var(--color-danger);
}

.salida:hover:not(:disabled) {
  background: var(--color-danger-soft);
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--color-border);
}

.tabs button {
  padding: 10px 18px;
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  font-weight: 500;
  color: var(--color-text-muted);
}

.tabs button.activo {
  border-bottom-color: var(--color-primary);
  color: var(--color-primary);
}

.panel {
  padding: 22px 26px;
}

.panel + .panel {
  margin-top: 18px;
}

.panel h2 {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.sub {
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-subtle);
}

.ficha {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 32px;
  margin-top: 10px;
}

.linea {
  margin-top: 14px;
  padding-left: 14px;
  border-left: 2px solid var(--color-border-strong);
  list-style: none;
}

.linea li {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 6px 0;
  font-size: 13px;
}

.linea time {
  min-width: 90px;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 12px;
  color: var(--color-text-muted);
}

.vacio {
  padding: 48px;
  text-align: center;
  color: var(--color-text-muted);
}

@media (max-width: 960px) {
  .layout,
  .ficha {
    grid-template-columns: 1fr;
  }
}
</style>
