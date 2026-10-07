import router from '@/router'
import { useAuthStore } from '@/stores/auth'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

// FastAPI devuelve `detail` como texto o como lista de errores de validación
function extraerMensaje(data: unknown, status: number): string {
  const detail = (data as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((e: { msg?: string }) => e.msg).join('. ')
  }
  if (status === 503) return 'El servicio no está disponible'
  return 'Ocurrió un error inesperado'
}

export async function request<T>(method: Method, path: string, body?: unknown): Promise<T> {
  const auth = useAuthStore()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth.token) headers.Authorization = `Bearer ${auth.token}`

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor')
  }

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    // Token vencido o inválido: cerramos sesión y volvemos al login
    if (response.status === 401 && auth.token) {
      auth.logout()
      router.push({ name: 'login' })
    }
    throw new ApiError(response.status, extraerMensaje(data, response.status))
  }

  return data as T
}
