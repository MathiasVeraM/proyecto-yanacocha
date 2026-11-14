<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { ITEMS_NAVEGACION } from '@/config/modulos'
import { useMenuLateral } from '@/composables/useMenuLateral'
import { useAuthStore } from '@/stores/auth'
import logoCompleto from '@/assets/images/logo-yanacocha.png'
import logoIcono from '@/assets/images/logo-yanacocha-icono.png'

const auth = useAuthStore()

// Solo se muestran los módulos a los que el rol del usuario tiene acceso
const items = computed(() => ITEMS_NAVEGACION.filter((item) => auth.tieneAcceso(item.codigoServicio)))

const { contraido, alternar } = useMenuLateral()
</script>

<template>
  <aside id="menu-lateral" class="sidebar" :class="{ contraido }">
    <div class="brand">
      <!-- Botón para ocultar o mostrar el menú, arriba del logo -->
      <button
        class="toggle-menu"
        type="button"
        :aria-label="contraido ? 'Mostrar menú' : 'Ocultar menú'"
        :title="contraido ? 'Mostrar menú' : 'Ocultar menú'"
        aria-controls="menu-lateral"
        :aria-expanded="!contraido"
        @click="alternar"
      >
        <!-- Chevron de dos hojas: la punta indica hacia dónde se moverá el menú
             (derecha = desplegar, izquierda = ocultar) -->
        <svg class="hojas" :class="{ 'apunta-izquierda': !contraido }" viewBox="0 0 24 24" aria-hidden="true">
          <defs>
            <linearGradient id="hojas-claro" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stop-color="#c3d77a" />
              <stop offset="1" stop-color="#8fb24a" />
            </linearGradient>
            <linearGradient id="hojas-oscuro" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stop-color="#5f9a45" />
              <stop offset="1" stop-color="#2e6b34" />
            </linearGradient>
          </defs>
          <!-- Hoja de arriba (clara) -->
          <g transform="rotate(30 18 12)">
            <path class="hoja" fill="url(#hojas-claro)" d="M4.6 12C7.2 8.2 12.8 7.6 18.2 12 13.2 14.4 8 14.6 4.6 12Z" />
            <path class="vena" d="M5.8 12C9.8 11.2 13.6 11.3 17 12" />
            <path class="vena-fina" d="M9.4 11.5l1.3-1.6M12.6 11.4l1.2-1.3" />
          </g>
          <!-- Hoja de abajo (oscura, reflejada para que curve hacia afuera) -->
          <g transform="rotate(-30 18 12) translate(0 24) scale(1 -1)">
            <path class="hoja" fill="url(#hojas-oscuro)" d="M4.6 12C7.2 8.2 12.8 7.6 18.2 12 13.2 14.4 8 14.6 4.6 12Z" />
            <path class="vena clara" d="M5.8 12C9.8 11.2 13.6 11.3 17 12" />
            <path class="vena-fina clara" d="M9.4 11.5l1.3-1.6M12.6 11.4l1.2-1.3" />
          </g>
        </svg>
      </button>

      <!-- Desplegado: logo completo. Contraído: solo el ícono del cocodrilo. -->
      <img
        v-if="contraido"
        class="brand-icono"
        :src="logoIcono"
        alt="YanaCocha, Centro de Rescate de Fauna Silvestre"
      />
      <img
        v-else
        class="brand-logo"
        :src="logoCompleto"
        alt="YanaCocha, Centro de Rescate de Fauna Silvestre"
      />
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
          <!-- Huella con la almohadilla en forma de hoja vertical -->
          <svg v-if="item.ruta === 'fichas'" viewBox="0 0 24 24">
            <ellipse cx="4.6" cy="10.4" rx="1.7" ry="2.2" transform="rotate(-24 4.6 10.4)" />
            <ellipse cx="8.6" cy="5.4" rx="1.8" ry="2.3" transform="rotate(-8 8.6 5.4)" />
            <ellipse cx="15.4" cy="5.4" rx="1.8" ry="2.3" transform="rotate(8 15.4 5.4)" />
            <ellipse cx="19.4" cy="10.4" rx="1.7" ry="2.2" transform="rotate(24 19.4 10.4)" />
            <path d="M12 9.6C15.6 12.6 17.4 15.4 17.4 17.6A5.4 5.4 0 0 1 6.6 17.6C6.6 15.4 8.4 12.6 12 9.6Z" />
            <path d="M12 22.4V14.2M12 19.4l2.2-2.2M12 17.2l-1.9-1.9" stroke-width="1.4" />
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

/* Menú abierto: logo horizontal a la izquierda y el botón de hojas a su derecha, en la misma fila.
   Menú contraído: botón arriba y el ícono del cocodrilo debajo, centrados. */
.brand {
  position: relative;
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 8px;
  padding: 16px 10px 16px 14px;
}

/* División entre el logo y los íconos de los módulos: línea más marcada y con
   margen a los lados, para que el logo no se confunda con un botón del menú */
.brand::after {
  content: '';
  position: absolute;
  right: 14px;
  bottom: 0;
  left: 14px;
  height: 1px;
  background: var(--color-border-strong);
}

.toggle-menu {
  display: grid;
  flex-shrink: 0;
  order: 2;
  place-items: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid var(--color-border-strong);
  border-radius: 50%;
  background: var(--color-surface);
  box-shadow: 0 1px 4px rgba(35, 40, 31, 0.08);
}

.contraido .toggle-menu {
  order: 0;
}

.toggle-menu:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

/* ---- Ícono de hojas (chevron) ---- */
.hojas {
  width: 24px;
  height: 24px;
  transition: transform 0.25s ease;
}

/* Menú abierto: la punta mira a la izquierda (acción: ocultar) */
.hojas.apunta-izquierda {
  transform: scaleX(-1);
}

.toggle-menu:hover .hojas {
  transform: scale(1.08);
}

.toggle-menu:hover .hojas.apunta-izquierda {
  transform: scaleX(-1) scale(1.08);
}

.hojas .hoja {
  stroke: var(--color-primary);
  stroke-width: 0.9;
  stroke-linejoin: round;
}

.hojas .vena,
.hojas .vena-fina {
  fill: none;
  stroke: var(--color-primary);
  stroke-linecap: round;
}

.hojas .vena {
  stroke-width: 0.8;
}

.hojas .vena-fina {
  stroke-width: 0.6;
}

.hojas .clara {
  stroke: #dbe8b4;
}

@media (prefers-reduced-motion: reduce) {
  .hojas {
    transition: none;
  }
}

.brand-logo {
  display: block;
  flex: 1;
  min-width: 0;
  max-height: 56px;
  object-fit: contain;
  object-position: left center;
}

.brand-icono {
  display: block;
  width: 56px;
  height: auto;
}

.nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 16px 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  font-family: var(--font-menu);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.25;
}

.nav-item:hover {
  background: var(--color-surface-alt);
}

.nav-item.router-link-active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 700;
}

.nav-ico {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
}

.nav-ico svg {
  width: 26px;
  height: 26px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* Si un nombre no cabe, baja a una segunda línea en vez de cortarse.
   El mínimo evita que se parta en muchas líneas mientras el menú se anima al abrirse. */
.nav-label {
  flex: 1;
  min-width: 120px;
}

/* ---- Menú contraído: solo íconos ---- */
.sidebar {
  overflow: hidden;
}

.contraido .brand {
  flex-direction: column;
  gap: 10px;
  padding: 12px 0 14px;
}

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

.contraido .nav-ico {
  width: 32px;
  height: 32px;
}

.contraido .nav-ico svg {
  width: 30px;
  height: 30px;
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
