/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  // 'true' al compilar la app móvil (modo movil)
  readonly VITE_APP_MOVIL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
