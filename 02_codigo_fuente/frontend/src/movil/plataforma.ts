// true al compilar la app móvil (`vite --mode movil`, ver .env.movil)
export const esMovil = import.meta.env.VITE_APP_MOVIL === 'true'
