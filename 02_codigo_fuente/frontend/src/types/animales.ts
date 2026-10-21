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
  id_inaturalist: number | null
}

export interface TaxonomiaCreate {
  nombre_comun: string
  especie: string
  genero?: string | null
  familia?: string | null
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

// El código no se envía: lo genera el servicio a partir del nombre científico
export interface AnimalCreate {
  id_taxonomia: number
  id_recinto: number
  edad_aproximada?: string | null
  sexo?: Sexo | null
  estado_actual?: EstadoAnimal
  fecha_ingreso?: string
  url_imagen?: string | null
}

// El código y la especie no se pueden editar
export type AnimalUpdate = Partial<Omit<AnimalCreate, 'id_taxonomia'>>

export interface FiltrosAnimales {
  buscar?: string
  id_taxonomia?: number
  estado?: EstadoAnimal
  id_recinto?: number
}
