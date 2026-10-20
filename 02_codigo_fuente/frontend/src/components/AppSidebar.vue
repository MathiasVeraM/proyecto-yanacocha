<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import UserAvatar from '@/components/UserAvatar.vue'
import { ITEMS_NAVEGACION } from '@/config/modulos'
import { useAuthStore } from '@/stores/auth'
import { useRolesStore } from '@/stores/roles'

const router = useRouter()
const auth = useAuthStore()
const rolesStore = useRolesStore()

// Solo se muestran los módulos a los que el rol del usuario tiene acceso
const items = computed(() => ITEMS_NAVEGACION.filter((item) => auth.tieneAcceso(item.codigoServicio)))

const menuAbierto = ref(false)
const correo = computed(() => auth.payload?.sub ?? '')
const nombreRol = computed(() => rolesStore.nombreDe(auth.payload?.id_rol))

function cerrarSesion() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <span class="brand-logo">Y</span>
      <div>
        <strong>Yanacocha</strong>
        <small>Gestión de Fauna</small>
      </div>
    </div>

    <nav class="nav">
      <RouterLink
        v-for="item in items"
        :key="item.codigoServicio"
        :to="{ name: item.ruta }"
        class="nav-item"
      >
        <span class="dot" />
        <span class="nav-label">{{ item.label }}</span>
        <span v-if="item.badge" class="nav-badge" :class="{ alert: item.alert }">
          {{ item.badge }}
        </span>
      </RouterLink>
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
</template>

<style scoped>
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

.nav-item:hover {
  background: var(--color-surface-alt);
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
</style>
