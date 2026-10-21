<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import BaseModal from './BaseModal.vue'
import EspecieAutocomplete from './EspecieAutocomplete.vue'
import { animalesApi, recintosApi, taxonomiaApi } from '@/api/animales'
import { ApiError } from '@/api/http'
import { ESTADOS_ANIMAL, ESTADOS_EN_CENTRO, SEXOS, hoyIso } from '@/config/animales'
import type { Animal, EstadoAnimal, Recinto, Sexo, Taxonomia } from '@/types/animales'

const props = defineProps<{
  open: boolean
  // null = registrar ingreso, Animal = editar ficha
  animal: Animal | null
}>()

const emit = defineEmits<{ close: []; saved: [animal: Animal] }>()

const esEdicion = computed(() => props.animal !== null)

// Especie: elegida del autocompletado o escrita a mano si no existe en ningún lado
const especie = ref<Taxonomia | null>(null)
const especieManual = ref(false)
const manual = reactive({ nombre_comun: '', especie: '', genero: '', familia: '' })

// Recinto: uno existente o uno nuevo creado desde aquí mismo
const recintos = ref<Recinto[]>([])
const recintoNuevo = ref(false)
const nuevo = reactive({ nombre_recinto: '', tipo: '', capacidad: '' })

const form = reactive({
  id_recinto: 0,
  sexo: '' as Sexo | '',
  edad_aproximada: '',
  estado_actual: 'en_centro' as EstadoAnimal,
  fecha_ingreso: '',
  url_imagen: '',
})

const error = ref('')
const guardando = ref(false)

// Un animal que ya salió conserva su estado: la salida se registra con su propio flujo
const yaSalio = computed(
  () => !!props.animal && !ESTADOS_EN_CENTRO.includes(props.animal.estado_actual),
)

watch(
  () => props.open,
  async (abierto) => {
    if (!abierto) return
    error.value = ''
    const a = props.animal
    especie.value = a?.taxonomia ?? null
    especieManual.value = false
    Object.assign(manual, { nombre_comun: '', especie: '', genero: '', familia: '' })
    recintoNuevo.value = false
    Object.assign(nuevo, { nombre_recinto: '', tipo: '', capacidad: '' })
    Object.assign(form, {
      id_recinto: a?.id_recinto ?? 0,
      sexo: a?.sexo ?? '',
      edad_aproximada: a?.edad_aproximada ?? '',
      estado_actual: a?.estado_actual ?? 'en_centro',
      fecha_ingreso: a?.fecha_ingreso ?? hoyIso(),
      url_imagen: a?.url_imagen ?? '',
    })
    try {
      recintos.value = await recintosApi.listar()
      // Si todavía no hay recintos, se ofrece crear el primero
      if (recintos.value.length === 0) recintoNuevo.value = true
      else if (!form.id_recinto) form.id_recinto = recintos.value[0]!.id_recinto
    } catch (e) {
      error.value = e instanceof ApiError ? e.message : 'No se pudieron cargar los recintos'
    }
  },
)

function usarManual(texto: string) {
  especie.value = null
  especieManual.value = true
  manual.nombre_comun = texto
}

function cambiarEspecie() {
  especie.value = null
  especieManual.value = false
}

async function obtenerIdTaxonomia(): Promise<number> {
  if (especie.value) return especie.value.id_taxonomia
  const creada = await taxonomiaApi.crear({
    nombre_comun: manual.nombre_comun,
    especie: manual.especie,
    genero: manual.genero || null,
    familia: manual.familia || null,
  })
  // Si el animal no se llega a guardar, la especie ya queda en el catálogo para el siguiente intento
  especie.value = creada
  especieManual.value = false
  return creada.id_taxonomia
}

async function obtenerIdRecinto(): Promise<number> {
  if (!recintoNuevo.value) return form.id_recinto
  const creado = await recintosApi.crear({
    nombre_recinto: nuevo.nombre_recinto,
    tipo: nuevo.tipo || null,
    capacidad: nuevo.capacidad ? Number(nuevo.capacidad) : null,
  })
  recintos.value.push(creado)
  recintoNuevo.value = false
  form.id_recinto = creado.id_recinto
  return creado.id_recinto
}

async function guardar() {
  error.value = ''
  if (!esEdicion.value && !especie.value && !especieManual.value) {
    error.value = 'Elige la especie del animal'
    return
  }
  guardando.value = true
  try {
    const comunes = {
      id_recinto: await obtenerIdRecinto(),
      sexo: form.sexo || null,
      edad_aproximada: form.edad_aproximada || null,
      fecha_ingreso: form.fecha_ingreso,
      url_imagen: form.url_imagen || null,
      ...(yaSalio.value ? {} : { estado_actual: form.estado_actual }),
    }
    const animal = props.animal
      ? await animalesApi.actualizar(props.animal.id_animal, comunes)
      : await animalesApi.crear({ id_taxonomia: await obtenerIdTaxonomia(), ...comunes })
    emit('saved', animal)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo guardar la ficha'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    :title="esEdicion ? 'Editar ficha' : 'Registrar ingreso de ejemplar'"
    :subtitle="esEdicion ? `${animal?.codigo_animal} · ${animal?.taxonomia.nombre_comun}` : 'Ficha individual del ejemplar'"
    width="640px"
    @close="emit('close')"
  >
    <form id="animal-form" class="form" @submit.prevent="guardar">
      <p v-if="!esEdicion" class="info">
        Se generan automáticamente: el <strong>código</strong>, la <strong>fecha de ingreso</strong>
        (si no la cambias) y la <strong>información taxonómica</strong> (nombre científico, género y
        familia) a partir del nombre común.
      </p>

      <!-- ---- Especie ---- -->
      <section class="bloque">
        <h3>Especie</h3>

        <div v-if="especie" class="especie-elegida">
          <div>
            <strong>{{ especie.nombre_comun }}</strong>
            <em>{{ especie.especie }}</em>
            <small>
              Género: {{ especie.genero ?? '—' }} · Familia: {{ especie.familia ?? '—' }}
            </small>
          </div>
          <button v-if="!esEdicion" type="button" class="link" @click="cambiarEspecie">Cambiar</button>
        </div>

        <template v-else-if="especieManual">
          <div class="row">
            <div class="field">
              <label for="manual-comun">Nombre común</label>
              <input id="manual-comun" v-model.trim="manual.nombre_comun" class="input" maxlength="100" required />
            </div>
            <div class="field">
              <label for="manual-cientifico">Nombre científico</label>
              <input
                id="manual-cientifico"
                v-model.trim="manual.especie"
                class="input"
                placeholder="Ej. Tapirus terrestris"
                maxlength="150"
                required
              />
            </div>
          </div>
          <div class="row">
            <div class="field">
              <label for="manual-genero">Género</label>
              <input id="manual-genero" v-model.trim="manual.genero" class="input" maxlength="100" />
            </div>
            <div class="field">
              <label for="manual-familia">Familia</label>
              <input id="manual-familia" v-model.trim="manual.familia" class="input" maxlength="100" />
            </div>
          </div>
          <button type="button" class="link" @click="cambiarEspecie">← Volver a buscar</button>
        </template>

        <div v-else class="field">
          <label for="especie-buscar">Nombre común</label>
          <EspecieAutocomplete
            input-id="especie-buscar"
            @seleccionar="(t) => (especie = t)"
            @manual="usarManual"
          />
        </div>
      </section>

      <!-- ---- Ubicación y datos del ejemplar ---- -->
      <section class="bloque">
        <h3>Datos del ejemplar</h3>

        <div v-if="!recintoNuevo" class="field">
          <label for="recinto">Recinto asignado</label>
          <div class="con-accion">
            <select id="recinto" v-model.number="form.id_recinto" class="input" required>
              <option v-for="r in recintos" :key="r.id_recinto" :value="r.id_recinto">
                {{ r.nombre_recinto }}{{ r.tipo ? ` · ${r.tipo}` : '' }}
              </option>
            </select>
            <button type="button" class="btn btn-secondary" @click="recintoNuevo = true">+ Nuevo</button>
          </div>
        </div>
        <div v-else class="nuevo-recinto">
          <div class="row tres">
            <div class="field">
              <label for="recinto-nombre">Nuevo recinto</label>
              <input
                id="recinto-nombre"
                v-model.trim="nuevo.nombre_recinto"
                class="input"
                placeholder="Ej. R-12"
                maxlength="100"
                required
              />
            </div>
            <div class="field">
              <label for="recinto-tipo">Tipo</label>
              <input id="recinto-tipo" v-model.trim="nuevo.tipo" class="input" placeholder="Ej. aviario" maxlength="50" />
            </div>
            <div class="field">
              <label for="recinto-capacidad">Capacidad</label>
              <input id="recinto-capacidad" v-model="nuevo.capacidad" type="number" min="1" class="input" />
            </div>
          </div>
          <button v-if="recintos.length" type="button" class="link" @click="recintoNuevo = false">
            ← Elegir un recinto existente
          </button>
        </div>

        <div class="row tres">
          <div class="field">
            <label for="sexo">Sexo</label>
            <select id="sexo" v-model="form.sexo" class="input">
              <option value="">Sin registrar</option>
              <option v-for="(label, valor) in SEXOS" :key="valor" :value="valor">{{ label }}</option>
            </select>
          </div>
          <div class="field">
            <label for="edad">Edad aproximada</label>
            <input id="edad" v-model.trim="form.edad_aproximada" class="input" placeholder="Ej. Adulto (~10 años)" maxlength="50" />
          </div>
          <div class="field">
            <label for="fecha">Fecha de ingreso</label>
            <input id="fecha" v-model="form.fecha_ingreso" type="date" class="input" required />
          </div>
        </div>

        <div class="row">
          <div v-if="!yaSalio" class="field">
            <label for="estado">Estado</label>
            <select id="estado" v-model="form.estado_actual" class="input">
              <option v-for="e in ESTADOS_EN_CENTRO" :key="e" :value="e">{{ ESTADOS_ANIMAL[e].label }}</option>
            </select>
          </div>
          <div class="field">
            <label for="imagen">URL de la fotografía</label>
            <input id="imagen" v-model.trim="form.url_imagen" type="url" class="input" placeholder="https://…" maxlength="500" />
          </div>
        </div>
      </section>

      <p v-if="error" class="alert-error">{{ error }}</p>
    </form>

    <template #footer>
      <button type="button" class="btn btn-secondary" @click="emit('close')">Cancelar</button>
      <button type="submit" form="animal-form" class="btn btn-primary" :disabled="guardando">
        {{ guardando ? 'Guardando…' : esEdicion ? 'Guardar cambios' : 'Registrar ingreso' }}
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.info {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 12px;
  line-height: 1.5;
}

.bloque {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bloque h3 {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.row.tres {
  grid-template-columns: 1fr 1fr 1fr;
}

.input {
  padding: 9px 12px;
}

.con-accion {
  display: flex;
  gap: 8px;
}

.con-accion .btn {
  flex-shrink: 0;
}

.especie-elegida {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
}

.especie-elegida strong,
.especie-elegida em,
.especie-elegida small {
  display: block;
}

.especie-elegida em {
  margin-top: 2px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.especie-elegida small {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.nuevo-recinto {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.link {
  align-self: flex-start;
  padding: 0;
  border: none;
  background: none;
  font-size: 12px;
  color: var(--color-primary);
}

@media (max-width: 600px) {
  .row,
  .row.tres {
    grid-template-columns: 1fr;
  }
}
</style>
