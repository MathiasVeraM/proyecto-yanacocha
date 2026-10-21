import type { BadgeTone } from '@/components/AppBadge.vue'
import type { EstadoAnimal, Sexo } from '@/types/animales'

export const ESTADOS_ANIMAL: Record<EstadoAnimal, { label: string; tono: BadgeTone }> = {
  en_centro: { label: 'En el centro', tono: 'green' },
  en_tratamiento: { label: 'En tratamiento', tono: 'amber' },
  liberado: { label: 'Liberado', tono: 'blue' },
  trasladado: { label: 'Trasladado', tono: 'indigo' },
  fallecido: { label: 'Fallecido', tono: 'gray' },
}

// Estados que significan que el animal ya salió del centro
export const ESTADOS_SALIDA: EstadoAnimal[] = ['liberado', 'trasladado', 'fallecido']

// Al registrar un ingreso o editar la ficha solo se elige entre estos; la salida tiene su propio flujo
export const ESTADOS_EN_CENTRO: EstadoAnimal[] = ['en_centro', 'en_tratamiento']

export const SEXOS: Record<Sexo, string> = {
  macho: 'Macho',
  hembra: 'Hembra',
  indeterminado: 'Indeterminado',
}

// "2026-10-21" -> "21 oct 2026" (sin pasar por Date para no correr la fecha por la zona horaria)
export function formatearFecha(fecha: string) {
  const [anio, mes, dia] = fecha.split('-').map(Number)
  const meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  return `${dia} ${meses[mes! - 1]} ${anio}`
}

// Fecha de hoy en hora local, en formato "aaaa-mm-dd" para un <input type="date">
export function hoyIso() {
  const hoy = new Date()
  const mes = String(hoy.getMonth() + 1).padStart(2, '0')
  const dia = String(hoy.getDate()).padStart(2, '0')
  return `${hoy.getFullYear()}-${mes}-${dia}`
}

// "Oso de anteojos" -> "OS"
export function iniciales(texto: string) {
  return texto.trim().slice(0, 2).toUpperCase()
}
