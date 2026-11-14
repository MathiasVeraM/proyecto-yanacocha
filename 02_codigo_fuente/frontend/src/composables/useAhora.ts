import { onBeforeUnmount, ref } from 'vue'
import { fechaIso } from '@/config/actividades'

function horaActual() {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// Fecha y hora local que se actualizan cada minuto (atrasos, línea de "ahora")
export function useAhora() {
  const hoy = ref(fechaIso(new Date()))
  const hora = ref(horaActual())
  const intervalo = setInterval(() => {
    hoy.value = fechaIso(new Date())
    hora.value = horaActual()
  }, 60_000)
  onBeforeUnmount(() => clearInterval(intervalo))
  return { hoy, hora }
}
