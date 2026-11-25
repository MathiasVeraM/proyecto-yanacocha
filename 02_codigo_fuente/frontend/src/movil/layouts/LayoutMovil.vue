<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { App } from '@capacitor/app'
import logoIcono from '@/assets/images/logo-yanacocha-icono.png'
import { useActividadesMovilStore } from '../stores/actividades'
import { useSincronizacionStore } from '../stores/sincronizacion'

const actividades = useActividadesMovilStore()
const sync = useSincronizacionStore()

let escucha: { remove: () => Promise<void> } | null = null

onMounted(async () => {
  // Al confirmar el servidor lo enviado, se deja como hecho y se trae lo último
  await sync.iniciar((confirmadas) => {
    actividades.confirmarCompletadas(confirmadas)
    void actividades.cargar()
  })
  void actividades.cargar()

  // Al volver a la app (segundo plano → primer plano) se reintenta y se refresca
  try {
    escucha = await App.addListener('appStateChange', ({ isActive }) => {
      if (!isActive) return
      void sync.sincronizar()
      void actividades.cargar()
    })
  } catch {
    // En el navegador no aplica
  }
})

onBeforeUnmount(() => void escucha?.remove())
</script>

<template>
  <div class="app">
    <header class="barra">
      <img :src="logoIcono" alt="" class="logo" />
      <span class="nombre">Yanacocha</span>
      <span class="estado" :class="{ sin: !sync.hayRed }">
        {{ sync.sincronizando ? 'Enviando…' : sync.hayRed ? 'En línea' : 'Sin conexión' }}
      </span>
    </header>

    <main class="contenido">
      <RouterView />
    </main>

    <nav class="pestanas" aria-label="Secciones">
      <RouterLink :to="{ name: 'actividades' }" class="pestana">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 6.5l1.5 1.5L9 5.5M5 12.5L6.5 14 9 11.5M5 18.5L6.5 20 9 17.5M12 7h7M12 13h7M12 19h7" />
        </svg>
        Hoy
      </RouterLink>
      <RouterLink :to="{ name: 'calendario' }" class="pestana">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4.5 6.5h15v13h-15ZM4.5 10.5h15M8.5 4v4M15.5 4v4" />
        </svg>
        Calendario
      </RouterLink>
      <RouterLink :to="{ name: 'envio' }" class="pestana">
        <span class="icono-envio">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 16V5M7.5 9.5L12 5l4.5 4.5M5 19h14" />
          </svg>
          <b v-if="sync.totalPendientes" class="contador">{{ sync.totalPendientes }}</b>
        </span>
        Envío
      </RouterLink>
    </nav>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100dvh;
}

.barra {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: calc(10px + env(safe-area-inset-top)) 16px 10px;
  background: var(--color-dark);
  color: #fff;
}

.logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.nombre {
  flex: 1;
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 600;
}

.estado {
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
}

.estado.sin {
  background: #87661a;
}

.contenido {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 8px;
}

.pestanas {
  display: flex;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  padding-bottom: env(safe-area-inset-bottom);
}

.pestana {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-height: 64px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.pestana.router-link-exact-active {
  color: var(--color-primary);
}

.pestana svg {
  width: 24px;
  height: 24px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.icono-envio {
  position: relative;
  display: inline-flex;
}

.contador {
  position: absolute;
  top: -6px;
  right: -10px;
  min-width: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-danger);
  color: #fff;
  font-size: 11px;
  line-height: 18px;
  text-align: center;
}
</style>
