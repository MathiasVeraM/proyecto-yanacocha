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
const MAX_NOMBRE = 100
const MAX_ESPECIE = 150
const MAX_TAXONOMIA = 100
const MAX_EDAD_ANIOS = 200
const MAX_EDAD_MESES = 11
const MAX_NOMBRE_RECINTO = 100
const MAX_TIPO_RECINTO = 50

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
  edad_anios: '',
  edad_meses: '',
  estado_actual: 'en_centro' as EstadoAnimal,
  fecha_ingreso: '',
})

// Foto adjunta: se sube después de guardar la ficha, porque necesita el id del animal
const archivo = ref<File | null>(null)
const vistaPrevia = ref<string | null>(null)
const arrastrando = ref(false)

const error = ref('')
const guardando = ref(false)
const edadIntentada = ref(false)

const errorEdadAnios = computed(() => {
  const valor = form.edad_anios.trim()
  if (!valor) return ''
  const anios = Number(valor)
  if (!Number.isInteger(anios)) return 'Ingresa una cantidad entera de años'
  if (anios < 0 || anios > MAX_EDAD_ANIOS) return `Los años deben estar entre 0 y ${MAX_EDAD_ANIOS}`
  return ''
})

const errorEdadMeses = computed(() => {
  const valor = form.edad_meses.trim()
  if (!valor) return ''
  const meses = Number(valor)
  if (!Number.isInteger(meses)) return 'Ingresa una cantidad entera de meses'
  if (meses < 0 || meses > MAX_EDAD_MESES) return `Los meses deben estar entre 0 y ${MAX_EDAD_MESES}`
  return ''
})

const errorEdadRequerida = computed(() =>
  edadIntentada.value && !form.edad_anios.trim() && !form.edad_meses.trim()
    ? 'Ingresa la edad en años o meses'
    : '',
)

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
    edadIntentada.value = false
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
      edad_anios: a?.edad_anios === null || a?.edad_anios === undefined ? '' : String(a.edad_anios),
      edad_meses: a?.edad_meses === null || a?.edad_meses === undefined ? '' : String(a.edad_meses),
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

function validarTaxonomiaManual(): string | null {
  const nombreComun = manual.nombre_comun.trim()
  const nombreCientifico = manual.especie.trim()
  if (!nombreComun || !nombreCientifico) return 'Ingresa el nombre común y el nombre científico'
  if (nombreComun.length > MAX_NOMBRE) return `El nombre común no puede superar los ${MAX_NOMBRE} caracteres`
  if (nombreCientifico.length > MAX_ESPECIE) {
    return `El nombre científico no puede superar los ${MAX_ESPECIE} caracteres`
  }
  // El backend requiere que el nombre científico contenga al menos una letra latina.
  if (!/[A-Za-z]/.test(nombreCientifico.normalize('NFKD'))) {
    return 'El nombre científico debe contener letras'
  }

  const campos = [
    ['género', manual.genero],
    ['familia', manual.familia],
    ['orden', manual.orden],
    ['clase', manual.clase],
  ] as const
  for (const [etiqueta, valor] of campos) {
    if (valor.trim().length > MAX_TAXONOMIA) {
      return `${etiqueta[0]!.toUpperCase()}${etiqueta.slice(1)} no puede superar los ${MAX_TAXONOMIA} caracteres`
    }
  }
  return null
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

function validarEdad(): { edad_anios: number; edad_meses: number } | null {
  const aniosIngresados = form.edad_anios.trim()
  const mesesIngresados = form.edad_meses.trim()
  if (errorEdadAnios.value || errorEdadMeses.value || errorEdadRequerida.value) return null
  const edadAnios = aniosIngresados ? Number(aniosIngresados) : 0
  const edadMeses = mesesIngresados ? Number(mesesIngresados) : 0
  return { edad_anios: edadAnios, edad_meses: edadMeses }
}

async function guardar() {
  error.value = ''
  edadIntentada.value = true
  const edad = validarEdad()
  if (!edad) return

  if (!especie.value && !especieManual.value) {
    error.value = 'Elige la especie del animal'
    return
  }
  if (especieManual.value) {
    const errorTaxonomia = validarTaxonomiaManual()
    if (errorTaxonomia) {
      error.value = errorTaxonomia
      return
    }
  }
  if (recintoNuevo.value) {
    if (!nuevo.nombre_recinto.trim()) {
      error.value = 'Ingresa el nombre del recinto'
      return
    }
    if (nuevo.nombre_recinto.trim().length > MAX_NOMBRE_RECINTO) {
      error.value = `El nombre del recinto no puede superar los ${MAX_NOMBRE_RECINTO} caracteres`
      return
    }
    if (nuevo.tipo.trim().length > MAX_TIPO_RECINTO) {
      error.value = `El tipo de recinto no puede superar los ${MAX_TIPO_RECINTO} caracteres`
      return
    }
    if (
      nuevo.capacidad !== '' &&
      (!Number.isInteger(Number(nuevo.capacidad)) || Number(nuevo.capacidad) <= 0)
    ) {
      error.value = 'La capacidad debe ser un número entero mayor que cero'
      return
    }
  }
  guardando.value = true
  try {
    const comunes = {
      id_taxonomia: await obtenerIdTaxonomia(),
      id_recinto: await obtenerIdRecinto(),
      nombre: form.nombre || null,
      sexo: form.sexo || null,
      ...edad,
      fecha_ingreso: form.fecha_ingreso,
      ...(yaSalio.value ? {} : { estado_actual: form.estado_actual }),
    }
    const animal = props.animal
      ? await animalesApi.actualizar(props.animal.id_animal, comunes)
      : await animalesApi.crear(comunes)

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
    :title="esEdicion ? 'Editar ficha' : 'Registrar ingreso'"
    :subtitle="
      esEdicion
        ? `${animal?.codigo_animal} · ${animal?.taxonomia.nombre_comun}`
        : 'Ficha individual del ejemplar'
    "
    width="980px"
    @close="emit('close')"
  >
    <form id="animal-form" class="form" @submit.prevent="guardar">
      <!-- ---- Columna izquierda: fotografía ---- -->
      <aside class="columna-foto">
        <div v-if="vistaPrevia" class="vista-previa">
          <img :src="vistaPrevia" alt="Vista previa de la fotografía" />
          <div class="vista-previa-datos">
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
          <svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true">
            <path
              d="M4 8h3l2-3h6l2 3h3v11H4z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linejoin="round"
            />
            <circle cx="12" cy="13" r="3.5" fill="none" stroke="currentColor" stroke-width="1.6" />
          </svg>
          <span>{{ animal?.url_imagen ? 'Reemplazar fotografía' : 'Adjuntar fotografía' }}</span>
          <small>JPG, PNG o WEBP · máx. {{ TAMANO_MAXIMO_MB }} MB</small>
        </label>
        <p class="ayuda-foto">Arrastra el archivo aquí o haz clic para elegirlo.</p>

        <p v-if="!esEdicion" class="info">
          Se generan automáticamente el <strong>código</strong>, la <strong>fecha de ingreso</strong>
          (si no la cambias) y la <strong>taxonomía</strong> a partir del nombre común.
        </p>
        <p v-else class="info">
          Puedes corregir la especie de este ejemplar sin afectar a los demás animales; su código se conserva.
        </p>
      </aside>

      <!-- ---- Columna derecha: datos ---- -->
      <div class="columna-datos">
        <section class="bloque">
          <h3>Identificación</h3>

          <!-- Especie elegida: ocupa toda la fila para mostrar su taxonomía -->
          <div v-if="especie" class="especie-elegida">
            <div>
              <strong>{{ especie.nombre_comun }}</strong>
              <em>{{ especie.especie }}</em>
              <small>
                Clase: {{ nombreClase(especie.clase) }} · Orden: {{ especie.orden ?? '—' }} ·
                Familia: {{ especie.familia ?? '—' }} · Género: {{ especie.genero ?? '—' }}
              </small>
            </div>
            <button type="button" class="link" @click="cambiarEspecie">Cambiar</button>
          </div>

          <div class="row">
            <div v-if="especieManual && !especie" class="field">
              <label for="manual-comun">Nombre común</label>
              <input
                id="manual-comun"
                v-model.trim="manual.nombre_comun"
                class="input"
                minlength="1"
                :maxlength="MAX_NOMBRE"
                required
              />
            </div>
            <div v-else-if="!especie" class="field">
              <label for="especie-buscar">Nombre común</label>
              <EspecieAutocomplete
                input-id="especie-buscar"
                @seleccionar="(t) => (especie = t)"
                @manual="usarManual"
              />
            </div>
            <div class="field" :class="{ ancho: !!especie }">
              <label for="nombre-ejemplar">Nombre del ejemplar <span class="opcional">(opcional)</span></label>
              <input
                id="nombre-ejemplar"
                v-model.trim="form.nombre"
                class="input"
                placeholder="Ej. Yaku"
                :maxlength="MAX_NOMBRE"
              />
            </div>
          </div>

          <!-- Taxonomía escrita a mano cuando la especie no existe en ningún catálogo -->
          <template v-if="especieManual && !especie">
            <div class="row tres">
              <div class="field">
                <label for="manual-cientifico">Nombre científico</label>
                <input
                  id="manual-cientifico"
                  v-model.trim="manual.especie"
                  class="input"
                  placeholder="Ej. Tapirus terrestris"
                  minlength="1"
                  :maxlength="MAX_ESPECIE"
                  required
                />
              </div>
              <div class="field">
                <label for="manual-genero">Género</label>
                <input id="manual-genero" v-model.trim="manual.genero" class="input" :maxlength="MAX_TAXONOMIA" />
              </div>
              <div class="field">
                <label for="manual-familia">Familia</label>
                <input id="manual-familia" v-model.trim="manual.familia" class="input" :maxlength="MAX_TAXONOMIA" />
              </div>
              <div class="field">
                <label for="manual-clase">Clase <span class="opcional">(opcional)</span></label>
                <input
                  id="manual-clase"
                  v-model.trim="manual.clase"
                  class="input"
                  placeholder="Ej. Mammalia"
                  :maxlength="MAX_TAXONOMIA"
                  list="clases-disponibles"
                />
                <datalist id="clases-disponibles">
                  <option v-for="(label, valor) in CLASES" :key="valor" :value="valor">{{ label }}</option>
                </datalist>
              </div>
              <div class="field">
                <label for="manual-orden">Orden</label>
                <input
                  id="manual-orden"
                  v-model.trim="manual.orden"
                  class="input"
                  placeholder="Ej. Carnivora"
                  :maxlength="MAX_TAXONOMIA"
                />
              </div>
              <div class="field volver">
                <button type="button" class="link" @click="cambiarEspecie">← Volver a buscar</button>
              </div>
            </div>
          </template>
        </section>

        <section class="bloque">
          <h3>Ubicación y datos</h3>

          <!-- Recinto nuevo: sus tres campos ocupan una fila propia -->
          <div v-if="recintoNuevo" class="nuevo-recinto">
            <div class="row fila-identificacion" :class="{ 'sin-selector-recinto': recintoNuevo }">
              <div class="field">
                <label for="recinto-nombre">Nuevo recinto</label>
                <input
                  id="recinto-nombre"
                  v-model.trim="nuevo.nombre_recinto"
                  class="input"
                  placeholder="Ej. R-12"
                  minlength="1"
                  :maxlength="MAX_NOMBRE_RECINTO"
                  required
                />
              </div>
              <div class="field">
                <label for="recinto-tipo">Tipo</label>
                <input
                  id="recinto-tipo"
                  v-model.trim="nuevo.tipo"
                  class="input"
                  placeholder="Ej. aviario"
                  :maxlength="MAX_TIPO_RECINTO"
                />
              </div>
              <div class="field">
                <label for="recinto-capacidad">Capacidad</label>
                <input
                  id="recinto-capacidad"
                  v-model="nuevo.capacidad"
                  type="number"
                  min="1"
                  step="1"
                  class="input"
                />
              </div>
            </div>
            <button v-if="recintos.length" type="button" class="link" @click="recintoNuevo = false">
              ← Elegir un recinto existente
            </button>
          </div>

          <div v-if="!recintoNuevo" class="row recinto-asignado">
            <div class="field">
              <label for="recinto">Recinto asignado</label>
              <div class="con-accion">
                <select id="recinto" v-model.number="form.id_recinto" class="input" required>
                  <option v-for="r in recintos" :key="r.id_recinto" :value="r.id_recinto">
                    {{ r.nombre_recinto }}{{ r.tipo ? ` · ${r.tipo}` : '' }}
                  </option>
                </select>
                <button
                  type="button"
                  class="btn btn-secondary nuevo-btn"
                  title="Crear un recinto nuevo"
                  @click="recintoNuevo = true"
                >
                  + Nuevo
                </button>
              </div>
            </div>
          </div>

          <div class="row fila-edad">
            <div class="field">
              <label for="sexo">Sexo</label>
              <select id="sexo" v-model="form.sexo" class="input">
                <option value="">Sin registrar</option>
                <option v-for="(label, valor) in SEXOS" :key="valor" :value="valor">{{ label }}</option>
              </select>
            </div>
            <div class="field">
              <label for="edad-anios">Años</label>
              <input
                id="edad-anios"
                v-model="form.edad_anios"
                type="number"
                min="0"
                :max="MAX_EDAD_ANIOS"
                step="1"
                class="input"
                inputmode="numeric"
                aria-describedby="ayuda-edad error-edad-requerida"
                :aria-invalid="!!(errorEdadAnios || errorEdadRequerida)"
              />
              <small v-if="errorEdadAnios" class="error-edad" role="alert">
                {{ errorEdadAnios }}
              </small>
            </div>
            <div class="field">
              <label for="edad-meses">Meses</label>
              <input
                id="edad-meses"
                v-model="form.edad_meses"
                type="number"
                min="0"
                :max="MAX_EDAD_MESES"
                step="1"
                class="input"
                inputmode="numeric"
                aria-describedby="ayuda-edad error-edad-requerida"
                :aria-invalid="!!(errorEdadMeses || errorEdadRequerida)"
              />
              <small v-if="errorEdadMeses" class="error-edad" role="alert">
                {{ errorEdadMeses }}
              </small>
            </div>
          </div>
          <small v-if="errorEdadRequerida" id="error-edad-requerida" class="error-edad" role="alert">
            {{ errorEdadRequerida }}
          </small>
          <p id="ayuda-edad" class="ayuda-edad">
            Ingresa años o meses; si dejas una unidad vacía, se guardará como 0. Al menos una debe tener un valor.
            Años: 0–{{ MAX_EDAD_ANIOS }}; meses: 0–{{ MAX_EDAD_MESES }}.
          </p>
        </section>

        <section class="bloque">
          <h3>Ingreso</h3>
          <div class="row tres">
            <div class="field">
              <label for="fecha">Fecha de ingreso</label>
              <input id="fecha" v-model="form.fecha_ingreso" type="date" class="input" required />
            </div>
            <div v-if="!yaSalio" class="field">
              <label for="estado">Estado</label>
              <select id="estado" v-model="form.estado_actual" class="input">
                <option v-for="e in ESTADOS_EN_CENTRO" :key="e" :value="e">{{ ESTADOS_ANIMAL[e].label }}</option>
              </select>
            </div>
          </div>
        </section>

        <p v-if="error" class="alert-error">{{ error }}</p>
      </div>
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
/* Dos columnas que llegan hasta los bordes del modal: foto a la izquierda, datos a la derecha */
.form {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  margin: -20px -24px;
  border-top: 1px solid var(--color-border);
}

.columna-foto {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
  border-right: 1px solid var(--color-border);
}

.columna-datos {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  padding: 18px 24px 20px;
}

.info {
  margin-top: auto;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 11px;
  line-height: 1.5;
}

.bloque {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bloque h3 {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text);
}

.row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.row.tres {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.row.recinto-asignado {
  grid-template-columns: minmax(0, 1fr);
}

.row.fila-edad {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.fila-edad .field {
  min-width: 0;
}

.fila-edad label {
  font-size: 11px;
}

.fila-edad .input {
  min-width: 0;
  padding: 7px 8px;
  font-size: 12px;
}

.ayuda-edad {
  margin-top: -4px;
  color: var(--color-text-muted);
  font-size: 11px;
}

.error-edad {
  color: var(--color-danger);
  font-size: 11px;
}

/* Con la especie ya elegida, el nombre del ejemplar queda solo en su fila */
.field.ancho {
  grid-column: 1 / 2;
}

.field.volver {
  justify-content: flex-end;
  padding-bottom: 10px;
}

.input {
  padding: 9px 12px;
}

.con-accion {
  display: flex;
  gap: 6px;
}

.con-accion .input {
  min-width: 0;
}

.nuevo-btn {
  flex-shrink: 0;
  padding: 8px 10px;
  font-size: 12px;
}

.especie-elegida {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
}

.especie-elegida strong {
  margin-right: 6px;
}

.especie-elegida em {
  font-size: 13px;
  color: var(--color-text-muted);
}

.especie-elegida small {
  display: block;
  margin-top: 3px;
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
  justify-content: center;
  align-items: center;
  gap: 6px;
  min-height: 220px;
  padding: 20px 14px;
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

.zona-foto svg {
  margin-bottom: 4px;
  color: var(--color-text-subtle);
}

.zona-foto span {
  font-size: 15px;
  font-weight: 500;
}

.zona-foto small {
  font-size: 11px;
  color: var(--color-text-subtle);
}

.ayuda-foto {
  font-size: 12px;
  color: var(--color-text-muted);
}

.oculto {
  display: none;
}

.vista-previa {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
}

.vista-previa img {
  width: 100%;
  height: 170px;
  border-radius: var(--radius-sm);
  object-fit: cover;
}

.vista-previa-datos strong,
.vista-previa-datos small {
  display: block;
}

.vista-previa-datos strong {
  font-size: 13px;
  word-break: break-all;
}

.vista-previa-datos small {
  margin: 2px 0 4px;
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

/* En pantallas angostas todo se apila y el modal hace scroll */
@media (max-width: 760px) {
  .form {
    grid-template-columns: 1fr;
  }

  .columna-foto {
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }

  .zona-foto {
    min-height: 140px;
  }
}

@media (max-width: 600px) {
  .row:not(.fila-edad),
  .row.tres {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 520px) {
  .form {
    margin: -16px -18px;
  }
}
</style>
