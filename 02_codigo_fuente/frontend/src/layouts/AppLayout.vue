<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import { useMenuLateral } from '@/composables/useMenuLateral'
import { useAuthStore } from '@/stores/auth'
import { useRolesStore } from '@/stores/roles'

const auth = useAuthStore()
const { contraido, alternar } = useMenuLateral()
const rolesStore = useRolesStore()

const nombreRol = computed(() => rolesStore.nombreDe(auth.payload?.id_rol))

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
        <button
          class="toggle-menu"
          type="button"
          :aria-label="contraido ? 'Mostrar menú' : 'Ocultar menú'"
          :title="contraido ? 'Mostrar menú' : 'Ocultar menú'"
          aria-controls="menu-lateral"
          :aria-expanded="!contraido"
          @click="alternar"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
            <path d="M9.5 4.5v15" />
            <path v-if="contraido" d="m13.5 10 2 2-2 2" />
            <path v-else d="m15.5 10-2 2 2 2" />
          </svg>
        </button>

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
  transition: grid-template-columns 0.2s ease;
}

.shell.contraido {
  grid-template-columns: 72px 1fr;
}

.toggle-menu {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  margin-right: auto;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-muted);
}

.toggle-menu:hover {
  background: var(--color-surface-alt);
  color: var(--color-text);
}

.toggle-menu svg {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

@media (prefers-reduced-motion: reduce) {
  .shell {
    transition: none;
  }
}

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
