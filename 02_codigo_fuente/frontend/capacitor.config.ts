import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'ec.yanacocha.fauna',
  appName: 'Yanacocha',
  webDir: 'dist',
  server: {
    // La app se sirve desde http://localhost (hay que agregarlo a CORS_ORIGINS del gateway) y
    // se permite hablar con un gateway sin HTTPS durante el desarrollo.
    androidScheme: 'http',
    cleartext: true,
  },
}

export default config
