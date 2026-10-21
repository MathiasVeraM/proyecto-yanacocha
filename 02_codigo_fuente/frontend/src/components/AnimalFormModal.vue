<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import BaseModal from './BaseModal.vue'
import EspecieAutocomplete from './EspecieAutocomplete.vue'
import { animalesApi, recintosApi, taxonomiaApi } from '@/api/animales'
import { ApiError } from '@/api/http'
import { CLASES, ESTADOS_ANIMAL, ESTADOS_EN_CENTRO, SEXOS, hoyIso, nombreClase } from '@/config/animales'
import type { Animal, EstadoAnimal, Recinto, Sexo, Taxonomia } from '@/types/animales'

const props = defineProps<{
  open: boolean
  // null = registrar ingreso, Animal = editar ficha
  animal: Animal | null
}>()

// aviso: la ficha se guardó pero la foto no se pudo subir
const emit = defineEmits<{ close: []; saved: [animal: Animal, aviso?: string] }>()

// Mismos límites que valida el servicio
const TIPOS_FOTO = ['image/jpeg', 'image/png', 'image/webp']
const TAMANO_MAXIMO_MB = 5

const esEdicion = computed(() => props.animal !== null)

// Especie: elegida del autocompletado o escrita a mano si no existe en ningún lado
const especie = ref<Taxonomia | null>(null)
const especieManual = ref(false)
const manual = reactive({ nombre_comun: '', especie: '', genero: '', familia: '', orden: '', clase: '' })

// Recinto: uno existente o uno nuevo creado desde aquí mismo
const recintos = ref<Recinto[]>([])
const recintoNuevo = ref(false)
const nuevo = reactive({ nombre_recinto: '', tipo: '', capacidad: '' })

const form = reactive({
  nombre: '',
  id_recinto: 0,
  sexo: '' as Sexo | '',
  edad_aproximada: '',
  estado_actual: 'en_centro' as EstadoAnimal,
  fecha_ingreso: '',
})

// Foto adjunta: se sube después de guardar la ficha, porque necesita el id del animal
const archivo = ref<File | null>(null)
const vistaPrevia = ref<string | null>(null)
const arrastrando = ref(false)

const error = ref('')
const guardando = ref(false)

function quitarFoto() {
  if (vistaPrevia.value) URL.revokeObjectURL(vistaPrevia.value)
  archivo.value = null
  vistaPrevia.value = null
}

function adjuntar(elegido: File | undefined) {
  if (!elegido) return
  error.value = ''
  if (!TIPOS_FOTO.includes(elegido.type)) {
    error.value = 'La fotografía debe ser una imagen JPG, PNG o WEBP'
    return
  }
  if (elegido.size > TAMANO_MAXIMO_MB * 1024 * 1024) {
    error.value = `La fotografía no puede superar los ${TAMANO_MAXIMO_MB} MB`
    return
  }
  quitarFoto()
  archivo.value = elegido
  vistaPrevia.value = URL.createObjectURL(elegido)
}

function onSeleccion(evento: Event) {
  const input = evento.target as HTMLInputElement
  adjuntar(input.files?.[0])
  // Permite volver a elegir el mismo archivo después de quitarlo
  input.value = ''
}

onBeforeUnmount(quitarFoto)

function onSoltar(evento: DragEvent) {
  arrastrando.value = false
  adjuntar(evento.dataTransfer?.files[0])
}

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
    Object.assign(manual, { nombre_comun: '', especie: '', genero: '', familia: '', orden: '', clase: '' })
    recintoNuevo.value = false
    Object.assign(nuevo, { nombre_recinto: '', tipo: '', capacidad: '' })
    Object.assign(form, {
      nombre: a?.nombre ?? '',
      id_recinto: a?.id_recinto ?? 0,
      sexo: a?.sexo ?? '',
      edad_aproximada: a?.edad_aproximada ?? '',
      estado_actual: a?.estado_actual ?? 'en_centro',
      fecha_ingreso: a?.fecha_ingreso ?? hoyIso(),
    })
    quitarFoto()
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
    orden: manual.orden || null,
    clase: manual.clase || null,
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
      nombre: form.nombre || null,
      sexo: form.sexo || null,
      edad_aproximada: form.edad_aproximada || null,
      fecha_ingreso: form.fecha_ingreso,
      ...(yaSalio.value ? {} : { estado_actual: form.estado_actual }),
    }
    const animal = props.animal
      ? await animalesApi.actualizar(props.animal.id_animal, comunes)
      : await animalesApi.crear({ id_taxonomia: await obtenerIdTaxonomia(), ...comunes })

    if (!archivo.value) {
      emit('saved', animal)
      return
    }
    try {
      emit('saved', await animalesApi.subirImagen(animal.id_animal, archivo.value))
    } catch (e) {
      // La ficha ya quedó guardada: se avisa para volver a intentar la foto desde "Editar ficha"
      const motivo = e instanceof ApiError ? e.message : 'error de conexión'
      emit('saved', animal, `La ficha se guardó, pero la fotografía no se pudo subir (${motivo}).`)
    }
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
              Clase: {{ nombreClase(especie.clase) }} · Orden: {{ especie.orden ?? '—' }} ·
              Familia: {{ especie.familia ?? '—' }} · Género: {{ especie.genero ?? '—' }}
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
          <div class="row">
            <div class="field">
              <label for="manual-clase">Clase</label>
              <select id="manual-clase" v-model="manual.clase" class="input">
                <option value="">Sin registrar</option>
                <option v-for="(label, valor) in CLASES" :key="valor" :value="valor">{{ label }} ({{ valor }})</option>
              </select>
            </div>
            <div class="field">
              <label for="manual-orden">Orden</label>
              <input id="manual-orden" v-model.trim="manual.orden" class="input" placeholder="Ej. Carnivora" maxlength="100" />
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

        <div class="field">
          <label for="nombre-ejemplar">Nombre del ejemplar <span class="opcional">(opcional)</span></label>
          <input id="nombre-ejemplar" v-model.trim="form.nombre" class="input" placeholder="Ej. Yaku" maxlength="100" />
        </div>

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

        <div v-if="!yaSalio" class="row">
          <div class="field">
            <label for="estado">Estado</label>
            <select id="estado" v-model="form.estado_actual" class="input">
              <option v-for="e in ESTADOS_EN_CENTRO" :key="e" :value="e">{{ ESTADOS_ANIMAL[e].label }}</option>
            </select>
          </div>
        </div>
      </section>

      <!-- ---- Fotografía ---- -->
      <section class="bloque">
        <h3>Fotografía</h3>
        <div v-if="vistaPrevia" class="vista-previa">
          <img :src="vistaPrevia" alt="Vista previa de la fotografía" />
          <div>
            <strong>{{ archivo?.name }}</strong>
            <small>{{ ((archivo?.size ?? 0) / 1024 / 1024).toFixed(2) }} MB</small>
            <button type="button" class="link quitar" @click="quitarFoto">Quitar</button>
          </div>
        </div>
        <label
          v-else
          class="zona-foto"
          :class="{ arrastrando }"
          @dragover.prevent="arrastrando = true"
          @dragleave="arrastrando = false"
          @drop.prevent="onSoltar"
        >
          <input type="file" :accept="TIPOS_FOTO.join(',')" class="oculto" @change="onSeleccion" />
          <span>
            + {{ animal?.url_imagen ? 'Reemplazar la fotografía del ejemplar' : 'Adjuntar fotografía del ejemplar' }}
          </span>
          <small>JPG, PNG o WEBP · máximo {{ TAMANO_MAXIMO_MB }} MB · haz clic o arrastra el archivo aquí</small>
        </label>
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

.opcional {
  color: var(--color-text-subtle);
}

.zona-foto {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 26px 16px;
  border: 1.5px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s, background-color 0.15s;
}

.zona-foto:hover,
.zona-foto.arrastrando {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.zona-foto span {
  font-weight: 500;
}

.zona-foto small {
  font-size: 11px;
  color: var(--color-text-subtle);
}

.oculto {
  display: none;
}

.vista-previa {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
}

.vista-previa img {
  width: 96px;
  height: 72px;
  border-radius: var(--radius-sm);
  object-fit: cover;
}

.vista-previa strong,
.vista-previa small {
  display: block;
}

.vista-previa strong {
  font-size: 13px;
  word-break: break-all;
}

.vista-previa small {
  margin: 2px 0 6px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.quitar {
  color: var(--color-danger);
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
