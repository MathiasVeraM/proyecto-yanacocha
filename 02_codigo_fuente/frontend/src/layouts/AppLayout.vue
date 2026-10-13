<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import UserAvatar from '@/components/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'
import { useRolesStore } from '@/stores/roles'

const router = useRouter()
const auth = useAuthStore()
const rolesStore = useRolesStore()

// Solo "Seguridad & usuarios" tiene pantalla por ahora; el resto es visual
const navItems = [
  { label: 'Fichas de ejemplares', badge: 4 },
  { label: 'Planificación' },
  { label: 'Bienestar animal', badge: 3, alert: true },
  { label: 'Control e informes' },
  { label: 'Seguridad & usuarios', to: { name: 'usuarios' } },
]

const menuAbierto = ref(false)
const correo = computed(() => auth.payload?.sub ?? '')
const nombreRol = computed(() => rolesStore.nombreDe(auth.payload?.id_rol))

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
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-logo">Y</span>
        <div>
          <strong>Yanacocha</strong>
          <small>Gestión de Fauna</small>
        </div>
      </div>

      <nav class="nav">
        <component
          :is="item.to ? RouterLink : 'span'"
          v-for="item in navItems"
          :key="item.label"
          :to="item.to"
          class="nav-item"
          :class="{ disabled: !item.to }"
        >
          <span class="dot" />
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.badge" class="nav-badge" :class="{ alert: item.alert }">
            {{ item.badge }}
          </span>
        </component>
      </nav>

      <div class="user">
        <button class="user-card" @click="menuAbierto = !menuAbierto">
          <UserAvatar :nombre="correo" />
          <span class="user-info">
            <strong>{{ correo.split('@')[0] }}</strong>
            <small>{{ nombreRol }}</small>
          </span>
          <span class="chevron" :class="{ open: menuAbierto }">⌄</span>
        </button>
        <div v-if="menuAbierto" class="user-menu">
          <button @click="cerrarSesion">Cerrar sesión</button>
        </div>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <label class="search">
          <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
            <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2" />
            <path d="m20 20-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
          <input type="search" placeholder="Buscar ejemplar, especie…" />
        </label>

        <button class="bell" aria-label="Notificaciones">
          <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
            <path
              d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15L6 16Zm4 4h4"
              fill="#e0b23c"
              stroke="#b8861b"
              stroke-width="1.5"
              stroke-linejoin="round"
            />
          </svg>
          <span class="bell-badge">3</span>
        </button>

        <div class="area">
          <span class="area-dot" />
          Área: <strong>{{ nombreRol }}</strong>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  height: 100%;
}

/* ---- Sidebar ---- */

.sidebar {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 18px;
  border-bottom: 1px solid var(--color-border);
}

.brand-logo {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-serif);
  font-weight: 700;
  font-size: 16px;
}

.brand strong {
  display: block;
  font-size: 14px;
}

.brand small {
  font-size: 11px;
  color: var(--color-text-muted);
}

.nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 16px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.nav-item.disabled {
  cursor: default;
}

.nav-item.router-link-active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
}

.dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.6;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  min-width: 18px;
  padding: 1px 6px;
  border-radius: 9px;
  background: var(--color-border);
  font-size: 10px;
  font-weight: 700;
  text-align: center;
}

.nav-badge.alert {
  background: var(--color-danger);
  color: #fff;
}

.user {
  position: relative;
  padding: 12px;
  border-top: 1px solid var(--color-border);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  text-align: left;
}

.user-card:hover {
  background: var(--color-surface-alt);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-info strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.user-info small {
  font-size: 11px;
  color: var(--color-text-muted);
}

.chevron {
  color: var(--color-text-muted);
  transition: transform 0.15s;
}

.chevron.open {
  transform: rotate(180deg);
}

.user-menu {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: calc(100% - 4px);
  padding: 4px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
}

.user-menu button {
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: 4px;
  background: none;
  color: var(--color-danger);
  text-align: left;
}

.user-menu button:hover {
  background: var(--color-danger-soft);
}

/* ---- Topbar ---- */

.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 260px;
  padding: 8px 12px;
  background: var(--color-input);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  color: var(--color-text-subtle);
}

.search input {
  flex: 1;
  min-width: 0;
  border: none;
  background: none;
  outline: none;
  font-size: 12px;
}

.bell {
  position: relative;
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  background: var(--color-input);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
}

.bell-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  min-width: 15px;
  height: 15px;
  border-radius: 50%;
  background: var(--color-danger);
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  line-height: 15px;
}

.area {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  min-width: 200px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--color-text-muted);
}

.area strong {
  color: var(--color-text);
}

.area-dot {
  width: 7px;
  height: 7px;
  margin-right: 4px;
  border-radius: 50%;
  background: #3f9a45;
}

.content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}
</style>
