import { crearRouterMovil } from '@/movil/router'
import { esMovil } from '@/movil/plataforma'
import { crearRouterWeb } from './web'

// La app móvil (Capacitor) y la web comparten API, stores y configuración, pero cada una
// tiene sus propias pantallas y rutas: se elige al compilar (`--mode movil`).
export default esMovil ? crearRouterMovil() : crearRouterWeb()
