// Tipos que reflejan los esquemas del servicio de gestión animal

export type EstadoAnimal = 'en_centro' | 'en_tratamiento' | 'liberado' | 'trasladado' | 'fallecido'
export type Sexo = 'macho' | 'hembra' | 'indeterminado'
export type EstadoRecinto = 'disponible' | 'en_limpieza' | 'en_mantenimiento'

export interface Taxonomia {
  id_taxonomia: number
  nombre_comun: string
  especie: string
  genero: string | null
  familia: string | null
  orden: string | null
  // Nombre científico de la clase: Mammalia, Aves, Reptilia…
  clase: string | null
  id_inaturalist: number | null
}

export interface TaxonomiaCreate {
  nombre_comun: string
  especie: string
  genero?: string | null
  familia?: string | null
  orden?: string | null
  clase?: string | null
}

// "catalogo": ya está guardada; "inaturalist": hay que importarla antes de usarla
export interface SugerenciaTaxonomia {
  origen: 'catalogo' | 'inaturalist'
  id_taxonomia: number | null
  id_inaturalist: number | null
  nombre_comun: string | null
  especie: string
}

export interface Recinto {
  id_recinto: number
  nombre_recinto: string
  tipo: string | null
  capacidad: number | null
  estado: EstadoRecinto
}

export interface RecintoCreate {
  nombre_recinto: string
  tipo?: string | null
  capacidad?: number | null
}

export interface Animal {
  id_animal: number
  codigo_animal: string
  // Nombre propio del ejemplar (ej. "Yaku"); el nombre común es de la especie
  nombre: string | null
  id_taxonomia: number
  id_recinto: number
  edad_aproximada: string | null
  sexo: Sexo | null
  estado_actual: EstadoAnimal
  fecha_ingreso: string
  url_imagen: string | null
  taxonomia: Taxonomia
  recinto: Recinto
}

// El código no se envía: lo genera el servicio a partir del nombre científico.
// La foto se sube aparte con animalesApi.subirImagen y el servicio llena url_imagen
export interface AnimalCreate {
  id_taxonomia: number
  id_recinto: number
  nombre?: string | null
  edad_aproximada?: string | null
  sexo?: Sexo | null
  estado_actual?: EstadoAnimal
  fecha_ingreso?: string
}

// El código no se edita; la taxonomía puede corregirse en la ficha
export type AnimalUpdate = Partial<AnimalCreate>

export interface FiltrosAnimales {
  buscar?: string
  id_taxonomia?: number
  estado?: EstadoAnimal
  id_recinto?: number
  clase?: string
}
