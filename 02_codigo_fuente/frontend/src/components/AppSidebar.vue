<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { ITEMS_NAVEGACION } from '@/config/modulos'
import { useMenuLateral } from '@/composables/useMenuLateral'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// Solo se muestran los módulos a los que el rol del usuario tiene acceso
const items = computed(() => ITEMS_NAVEGACION.filter((item) => auth.tieneAcceso(item.codigoServicio)))

const { contraido } = useMenuLateral()
</script>

<template>
  <aside id="menu-lateral" class="sidebar" :class="{ contraido }">
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
        :title="contraido ? item.label : undefined"
        :aria-label="item.label"
      >
        <span class="nav-ico" aria-hidden="true">
          <svg v-if="item.ruta === 'fichas'" viewBox="0 0 24 24">
            <path d="M12 13c-3 0-5 3-5 5 0 1.5 1.3 2 2.5 2 1 0 1.6-.5 2.5-.5s1.5.5 2.5.5c1.2 0 2.5-.5 2.5-2 0-2-2-5-5-5Z" />
            <circle cx="6" cy="10.5" r="1.6" /><circle cx="9.5" cy="6.5" r="1.6" />
            <circle cx="14.5" cy="6.5" r="1.6" /><circle cx="18" cy="10.5" r="1.6" />
          </svg>
          <svg v-else-if="item.ruta === 'planificacion'" viewBox="0 0 24 24">
            <rect x="3.5" y="5" width="17" height="15.5" rx="2.5" /><path d="M3.5 10h17M8 3v4M16 3v4" />
          </svg>
          <svg v-else-if="item.ruta === 'bienestar'" viewBox="0 0 24 24">
            <path d="M12 20s-7.5-4.4-7.5-10A4.2 4.2 0 0 1 12 7.4 4.2 4.2 0 0 1 19.5 10c0 5.6-7.5 10-7.5 10Z" />
          </svg>
          <svg v-else viewBox="0 0 24 24"><path d="M12 3l7 3v5c0 5-3.2 8.4-7 10-3.8-1.6-7-5-7-10V6Z" /><path d="m9 12 2 2 4-4" /></svg>
        </span>
        <span class="nav-label">{{ item.label }}</span>
        <span v-if="item.badge" class="nav-badge" :class="{ alert: item.alert }">
          {{ item.badge }}
        </span>
      </RouterLink>
    </nav>
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

.nav-ico {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

.nav-ico svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.nav-label {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
}

/* ---- Menú contraído: solo íconos ---- */
.sidebar {
  overflow: hidden;
}

.brand > div {
  white-space: nowrap;
}

.contraido .brand {
  justify-content: center;
  padding: 20px 0;
}

.contraido .brand > div,
.contraido .nav-label {
  display: none;
}

.contraido .nav {
  padding: 16px 10px;
}

.contraido .nav-item {
  position: relative;
  justify-content: center;
  padding: 11px 0;
}

.contraido .nav-ico svg {
  width: 21px;
  height: 21px;
}

.contraido .nav-badge {
  position: absolute;
  top: 3px;
  right: 6px;
  min-width: 16px;
  padding: 0 4px;
  font-size: 9px;
  line-height: 14px;
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

</style>
