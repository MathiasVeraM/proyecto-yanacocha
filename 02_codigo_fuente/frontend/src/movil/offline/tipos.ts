import type { CategoriaObservacion, SeveridadObservacion } from '@/types/actividades'

// Lo que se registró en el teléfono y todavía no llegó al servidor
export interface CompletarPendiente {
  tipo: 'completar'
  id_local: string
  id_actividad: number
  // Hora real del dispositivo al marcar
  fecha_completada: string
  observaciones?: string
}

export interface ObservacionPendiente {
  tipo: 'observacion'
  // Identificador único: si el envío se repite, el servidor no la duplica
  id_cliente: string
  id_actividad: number
  categoria: CategoriaObservacion
  severidad: SeveridadObservacion
  detalle: string
  fecha_registro: string
}

export type OperacionPendiente = CompletarPendiente | ObservacionPendiente

// Registros que el servidor no pudo guardar nunca (ej. la actividad se eliminó)
export interface OperacionRechazada {
  id: string
  tipo: OperacionPendiente['tipo']
  id_actividad: number
  motivo: string
  fecha: string
}
