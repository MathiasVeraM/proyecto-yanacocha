import { API_URL, ApiError, request } from './http'
import { useAuthStore } from '@/stores/auth'
import type {
  Animal,
  AnimalCreate,
  AnimalUpdate,
  FiltrosAnimales,
  Recinto,
  RecintoCreate,
  SugerenciaTaxonomia,
  Taxonomia,
  TaxonomiaCreate,
} from '@/types/animales'

const URL = '/api/animales'

// Arma el query string solo con los filtros que tienen valor
function query(params: Record<string, string | number | undefined>) {
  const valores = Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
  return valores.length ? `?${new URLSearchParams(valores.map(([k, v]) => [k, String(v)]))}` : ''
}

// La foto no viaja como JSON: se sube como archivo y se descarga como imagen, con el token igual que el resto
async function fetchConToken(method: 'GET' | 'PUT', path: string, body?: FormData) {
  const auth = useAuthStore()
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
      body,
    })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor')
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const detalle = (data as { detail?: unknown } | null)?.detail
    throw new ApiError(response.status, typeof detalle === 'string' ? detalle : 'No se pudo procesar la fotografía')
  }
  return response
}

export const animalesApi = {
  listar: (filtros: FiltrosAnimales = {}) => request<Animal[]>('GET', `${URL}${query({ ...filtros })}`),

  obtener: (id: number) => request<Animal>('GET', `${URL}/${id}`),

  crear: (datos: AnimalCreate) => request<Animal>('POST', URL, datos),

  actualizar: (id: number, datos: AnimalUpdate) => request<Animal>('PUT', `${URL}/${id}`, datos),

  // Sube o reemplaza la foto; devuelve el animal con su url_imagen nueva
  subirImagen: async (id: number, archivo: File) => {
    const datos = new FormData()
    datos.append('archivo', archivo)
    return (await (await fetchConToken('PUT', `${URL}/${id}/imagen`, datos)).json()) as Animal
  },

  // Recibe la url_imagen del animal (ruta de la API) y devuelve la imagen para mostrarla
  descargarImagen: async (urlImagen: string) => (await fetchConToken('GET', urlImagen)).blob(),
}

export const taxonomiaApi = {
  listar: (buscar?: string) => request<Taxonomia[]>('GET', `${URL}/taxonomia${query({ buscar })}`),

  // Autocompletado: catálogo propio + iNaturalist
  sugerencias: (buscar: string) =>
    request<SugerenciaTaxonomia[]>('GET', `${URL}/taxonomia/sugerencias${query({ buscar })}`),

  importar: (idInaturalist: number) =>
    request<Taxonomia>('POST', `${URL}/taxonomia/importar`, { id_inaturalist: idInaturalist }),

  crear: (datos: TaxonomiaCreate) => request<Taxonomia>('POST', `${URL}/taxonomia`, datos),
}

export const recintosApi = {
  listar: () => request<Recinto[]>('GET', `${URL}/recintos`),

  crear: (datos: RecintoCreate) => request<Recinto>('POST', `${URL}/recintos`, datos),
}
