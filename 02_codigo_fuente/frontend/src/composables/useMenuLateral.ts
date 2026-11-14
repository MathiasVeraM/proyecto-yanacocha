import { ref, watch } from 'vue'

const CLAVE = 'yanacocha.menuContraido'

function leerPreferencia() {
  try {
    return localStorage.getItem(CLAVE) === '1'
  } catch {
    return false
  }
}

// Un solo estado para toda la app: el botón está en la barra superior y el menú lo lee
const contraido = ref(leerPreferencia())

watch(contraido, (valor) => {
  try {
    localStorage.setItem(CLAVE, valor ? '1' : '0')
  } catch {
    // Sin almacenamiento (modo privado): la preferencia solo dura la sesión
  }
})

export function useMenuLateral() {
  return {
    contraido,
    alternar: () => {
      contraido.value = !contraido.value
    },
  }
}
