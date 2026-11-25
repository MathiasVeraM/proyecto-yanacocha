import { Preferences } from '@capacitor/preferences'

// Almacenamiento local persistente del móvil. En el navegador (pruebas con `pnpm dev:movil`)
// Capacitor usa localStorage por debajo, así que el mismo código funciona en ambos.
// Los datos se guardan por usuario para que dos personas en el mismo teléfono no se mezclen.

export async function leer<T>(clave: string, porDefecto: T): Promise<T> {
  try {
    const { value } = await Preferences.get({ key: clave })
    return value ? (JSON.parse(value) as T) : porDefecto
  } catch {
    return porDefecto
  }
}

export async function guardar(clave: string, valor: unknown) {
  try {
    await Preferences.set({ key: clave, value: JSON.stringify(valor) })
  } catch {
    // Sin espacio o almacenamiento bloqueado: la app sigue funcionando con lo que tiene en memoria
  }
}

export const claves = {
  cola: (idUsuario: number) => `yc:${idUsuario}:cola`,
  rechazadas: (idUsuario: number) => `yc:${idUsuario}:rechazadas`,
  datos: (idUsuario: number) => `yc:${idUsuario}:datos`,
}
