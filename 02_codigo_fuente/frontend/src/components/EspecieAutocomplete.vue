<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { taxonomiaApi } from '@/api/animales'
import { ApiError } from '@/api/http'
import type { SugerenciaTaxonomia, Taxonomia } from '@/types/animales'

defineProps<{ inputId?: string }>()

const emit = defineEmits<{
  seleccionar: [especie: Taxonomia]
  // El usuario no encontró la especie y quiere registrarla a mano con el texto escrito
  manual: [texto: string]
}>()

const MIN_LETRAS = 2
const ESPERA_MS = 350

const texto = ref('')
const sugerencias = ref<SugerenciaTaxonomia[]>([])
const abierto = ref(false)
const buscando = ref(false)
const importando = ref(false)
const error = ref('')

let temporizador: ReturnType<typeof setTimeout> | undefined
// Evita que una respuesta lenta reemplace a la de una búsqueda más reciente
let busquedaActual = 0

watch(texto, (valor) => {
  clearTimeout(temporizador)
  error.value = ''
  if (valor.trim().length < MIN_LETRAS) {
    sugerencias.value = []
    abierto.value = false
    return
  }
  temporizador = setTimeout(() => buscar(valor.trim()), ESPERA_MS)
})

onBeforeUnmount(() => clearTimeout(temporizador))

async function buscar(valor: string) {
  const id = ++busquedaActual
  buscando.value = true
  abierto.value = true
  try {
    const resultado = await taxonomiaApi.sugerencias(valor)
    if (id === busquedaActual) sugerencias.value = resultado
  } catch (e) {
    if (id === busquedaActual) error.value = e instanceof ApiError ? e.message : 'No se pudo buscar la especie'
  } finally {
    if (id === busquedaActual) buscando.value = false
  }
}

async function elegir(sugerencia: SugerenciaTaxonomia) {
  error.value = ''
  importando.value = true
  try {
    // Las de iNaturalist se guardan en el catálogo para tener su id_taxonomia, género y familia
    const especie =
      sugerencia.origen === 'catalogo'
        ? (await taxonomiaApi.listar(sugerencia.especie)).find(
            (t) => t.id_taxonomia === sugerencia.id_taxonomia,
          )
        : await taxonomiaApi.importar(sugerencia.id_inaturalist!)
    if (!especie) throw new Error()
    emit('seleccionar', especie)
    texto.value = ''
    abierto.value = false
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo usar esa especie'
  } finally {
    importando.value = false
  }
}

function cerrarConRetraso() {
  // Deja que el clic sobre una sugerencia se registre antes de cerrar la lista
  setTimeout(() => (abierto.value = false), 150)
}
</script>

<template>
  <div class="autocomplete">
    <input
      :id="inputId"
      v-model="texto"
      class="input"
      placeholder="Ej. Oso de anteojos"
      autocomplete="off"
      :disabled="importando"
      @focus="abierto = sugerencias.length > 0"
      @blur="cerrarConRetraso"
    />

    <div v-if="abierto" class="lista" role="listbox">
      <p v-if="buscando" class="estado">Buscando…</p>
      <template v-else>
        <button
          v-for="s in sugerencias"
          :key="`${s.origen}-${s.id_taxonomia ?? s.id_inaturalist}`"
          type="button"
          class="opcion"
          role="option"
          @mousedown.prevent="elegir(s)"
        >
          <span class="nombres">
            <strong>{{ s.nombre_comun ?? s.especie }}</strong>
            <em>{{ s.especie }}</em>
          </span>
          <span class="origen" :class="s.origen">
            {{ s.origen === 'catalogo' ? 'Catálogo' : 'iNaturalist' }}
          </span>
        </button>
        <p v-if="sugerencias.length === 0" class="estado">Sin coincidencias</p>
      </template>
      <button type="button" class="opcion manual" @mousedown.prevent="emit('manual', texto.trim())">
        + No la encuentro: registrar especie manualmente
      </button>
    </div>

    <p v-if="importando" class="ayuda">Obteniendo datos taxonómicos…</p>
    <p v-if="error" class="alert-error">{{ error }}</p>
  </div>
</template>

<style scoped>
.autocomplete {
  position: relative;
}

.lista {
  position: absolute;
  z-index: 10;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 280px;
  overflow-y: auto;
  padding: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.opcion {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  text-align: left;
}

.opcion:hover {
  background: var(--color-surface-alt);
}

.nombres {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.nombres strong {
  font-size: 13px;
  font-weight: 600;
}

.nombres em {
  font-size: 12px;
  color: var(--color-text-muted);
}

.origen {
  flex-shrink: 0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

.origen.catalogo {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.origen.inaturalist {
  background: #dde9f3;
  color: #2d6a9a;
}

.manual {
  margin-top: 4px;
  border-top: 1px solid var(--color-border);
  border-radius: 0;
  font-size: 12px;
  color: var(--color-primary);
}

.estado,
.ayuda {
  padding: 8px 10px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.ayuda {
  padding: 6px 0 0;
}

.alert-error {
  margin-top: 6px;
}
</style>
