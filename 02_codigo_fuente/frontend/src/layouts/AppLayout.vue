<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useMenuLateral } from '@/composables/useMenuLateral'
import { useAuthStore } from '@/stores/auth'
import { useRolesStore } from '@/stores/roles'

const auth = useAuthStore()
const router = useRouter()
const { contraido } = useMenuLateral()
const rolesStore = useRolesStore()

const nombreRol = computed(() => rolesStore.nombreDe(auth.payload?.id_rol))
const correo = computed(() => auth.payload?.sub ?? '')

function cerrarSesion() {
  auth.logout()
  router.push({ name: 'login' })
}

onMounted(() => {
  rolesStore.cargar().catch(() => {
    // Si falla, los nombres de rol se muestran como "—"
  })
})
</script>

<template>
  <div class="shell" :class="{ contraido }">
    <AppSidebar />

    <div class="main">
      <header class="topbar">
        <!-- Las vistas teletransportan aquí su enlace de regreso (p. ej. "Volver a fichas") -->
        <div id="cabecera-navegacion" class="cabecera-navegacion"></div>

        <button class="bell" aria-label="Notificaciones">
          <svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true">
            <path d="M6 16v-5a6 6 0 1 1 12 0v5l1.5 2h-15L6 16Z" />
            <path d="M10 20.5a2.2 2.2 0 0 0 4 0" />
          </svg>
        </button>

        <details class="account-menu">
          <summary class="account-button" aria-label="Menú de usuario">
            <UserAvatar :nombre="correo" />
            <span class="account-info">
              <strong>{{ correo.split('@')[0] }}</strong>
              <small>Área: {{ nombreRol }}</small>
            </span>
            <svg class="account-chevron" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
              <path d="m6 9 6 6 6-6" />
            </svg>
          </summary>
          <div class="account-popover">
            <span class="account-email">{{ correo }}</span>
            <button type="button" @click="cerrarSesion">Cerrar sesión</button>
          </div>
        </details>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* El menú lateral y la cabecera quedan fijos: la ventana no hace scroll,
   solo el contenido de la página (.content). */
.shell {
  display: grid;
  grid-template-columns: 244px 1fr;
  grid-template-rows: minmax(0, 1fr);
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  transition: grid-template-columns 0.2s ease;
}

.shell.contraido {
  grid-template-columns: 72px 1fr;
}

@media (prefers-reduced-motion: reduce) {
  .shell {
    transition: none;
  }
}

.cabecera-navegacion {
  display: flex;
  align-items: center;
  min-width: 0;
  margin-right: auto;
}

.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.topbar {
  flex-shrink: 0;
}

.topbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  /* Cabecera delgada: solo lo justo para la campana y el botón de usuario */
  height: 52px;
  padding: 0 24px 0 32px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

/* Campana y botón de usuario: botones claros, bien redondeados y con sombra suave */
.bell {
  position: relative;
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: 12px;
  color: var(--color-text);
  box-shadow: 0 1px 3px rgba(35, 40, 31, 0.06);
}

.bell:hover {
  background: var(--color-surface-alt);
}

.bell svg {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.bell-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 15px;
  height: 15px;
  border-radius: 50%;
  background: var(--color-danger);
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  line-height: 15px;
}

.account-menu {
  position: relative;
}

.account-button {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 190px;
  height: 38px;
  padding: 0 10px 0 4px;
  list-style: none;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(35, 40, 31, 0.06);
  cursor: pointer;
}

/* Avatar cuadrado redondeado (solo en la cabecera; en otras vistas sigue circular) */
.account-button :deep(.avatar) {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  font-size: 11px;
}

.account-button::-webkit-details-marker {
  display: none;
}

.account-button:hover,
.account-menu[open] .account-button {
  background: var(--color-surface-alt);
}

.account-info {
  display: grid;
  flex: 1;
  min-width: 0;
  gap: 1px;
  font-size: 12px;
}

.account-info strong,
.account-email {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-info strong {
  color: var(--color-text);
  font-size: 13px;
  font-weight: 700;
}

.account-info small {
  color: var(--color-text-muted);
  font-size: 11px;
}

.account-chevron {
  flex-shrink: 0;
  fill: none;
  stroke: var(--color-text-muted);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform 0.15s ease;
}

.account-menu[open] .account-chevron {
  transform: rotate(180deg);
}

.account-popover {
  position: absolute;
  z-index: 20;
  top: calc(100% + 6px);
  right: 0;
  display: grid;
  gap: 8px;
  width: 220px;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.account-email {
  padding: 2px 6px 6px;
  color: var(--color-text-muted);
  font-size: 11px;
}

.account-popover button {
  padding: 8px 10px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-danger);
  text-align: left;
}

.account-popover button:hover {
  background: var(--color-danger-soft);
}

@media (max-width: 520px) {
  .topbar {
    gap: 8px;
    padding: 10px 12px;
  }

  .account-button {
    min-width: 0;
  }

  .account-info {
    display: none;
  }

  .account-popover {
    width: min(220px, calc(100vw - 24px));
  }
}

.content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  /* Margen alrededor de las pantallas: lo justo para separar del menú y la cabecera */
  padding: 12px 12px 14px;
}
</style>
