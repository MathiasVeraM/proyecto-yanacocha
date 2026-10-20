<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { useRolesStore } from '@/stores/roles'

const auth = useAuthStore()
const rolesStore = useRolesStore()

const nombreRol = computed(() => rolesStore.nombreDe(auth.payload?.id_rol))

onMounted(() => {
  rolesStore.cargar().catch(() => {
    // Si falla, los nombres de rol se muestran como "—"
  })
})
</script>

<template>
  <div class="shell">
    <AppSidebar />

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
