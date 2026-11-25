// El servidor y el móvil trabajan en la misma zona (la del centro), sin importar cómo tenga
// configurada la zona el teléfono. La hora sale del reloj del dispositivo, sin entrada manual.
const ZONA = 'America/Guayaquil'

const formato = new Intl.DateTimeFormat('en-CA', {
  timeZone: ZONA,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hourCycle: 'h23',
})

export function ahoraCentro() {
  const p = Object.fromEntries(formato.formatToParts(new Date()).map((x) => [x.type, x.value]))
  const fecha = `${p.year}-${p.month}-${p.day}`
  const hora = `${p.hour}:${p.minute}`
  // "2026-11-25T08:15:30", el formato que espera el backend (sin zona)
  return { fecha, hora, iso: `${fecha}T${hora}:${p.second}` }
}

export function nuevoId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  // Respaldo para WebViews antiguos
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}
