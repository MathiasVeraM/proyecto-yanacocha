<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { CATEGORIAS_OBSERVACION } from '@/config/actividades'
import { useActividadesMovilStore } from '../stores/actividades'
import { useSincronizacionStore } from '../stores/sincronizacion'

const router = useRouter()
const auth = useAuthStore()
const actividades = useActividadesMovilStore()
const sync = useSincronizacionStore()

function titulo(idActividad: number) {
  const actividad = actividades.actividades.find((a) => a.id_actividad === idActividad)
  return actividad ? actividades.describir.titulo(actividad) : `Actividad #${idActividad}`
}

const hora = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)} ${iso.slice(11, 16)}`

async function salir() {
  // Lo que quedó sin enviar se conserva en el teléfono y se envía al volver a entrar
  await sync.detener()
  actividades.limpiar()
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="vista">
    <h1>Envío de datos</h1>

    <section class="estado" :class="{ sin: !sync.hayRed }">
      <p class="titulo">
        {{ sync.sincronizando ? 'Enviando…' : sync.hayRed ? 'Con conexión' : 'Sin conexión' }}
      </p>
      <p v-if="sync.totalPendientes">
        {{ sync.totalPendientes }} registro{{ sync.totalPendientes > 1 ? 's' : '' }} por enviar.
        Se envían solos al haber señal.
      </p>
      <p v-else>Todo está enviado.</p>
      <p v-if="sync.errorEnvio" class="error">{{ sync.errorEnvio }}</p>
      <p v-if="sync.ultimoEnvio" class="sutil">Último envío: {{ hora(sync.ultimoEnvio) }}</p>
      <button
        class="m-btn m-btn-primario"
        :disabled="!sync.totalPendientes || sync.sincronizando || !sync.hayRed"
        @click="sync.sincronizar()"
      >
        Enviar ahora
      </button>
    </section>

    <section v-if="sync.pendientes.length">
      <h2>Por enviar</h2>
      <ul class="lista">
        <li v-for="op in sync.pendientes" :key="op.tipo === 'completar' ? op.id_local : op.id_cliente">
          <strong>{{ op.tipo === 'completar' ? 'Marcada como hecha' : 'Observación' }}</strong>
          <span>{{ titulo(op.id_actividad) }}</span>
          <span class="sutil">
            <template v-if="op.tipo === 'observacion'">
              {{ CATEGORIAS_OBSERVACION[op.categoria].label }} · {{ op.severidad }} ·
            </template>
            {{ hora(op.tipo === 'completar' ? op.fecha_completada : op.fecha_registro) }}
          </span>
        </li>
      </ul>
    </section>

    <section v-if="sync.rechazadas.length">
      <h2>No se pudieron guardar</h2>
      <ul class="lista">
        <li v-for="r in sync.rechazadas" :key="r.id" class="rechazada">
          <strong>{{ r.tipo === 'completar' ? 'Marcar como hecha' : 'Observación' }}</strong>
          <span>{{ titulo(r.id_actividad) }}</span>
          <span class="sutil">{{ r.motivo }}</span>
          <button class="descartar" @click="sync.descartarRechazada(r.id)">Entendido</button>
        </li>
      </ul>
    </section>

    <section class="cuenta">
      <p class="sutil">Sesión: {{ auth.payload?.sub }}</p>
      <button class="m-btn m-btn-secundario m-btn-bloque" @click="salir">Cerrar sesión</button>
    </section>
  </div>
</template>

<style scoped>
.vista {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 16px;
}

h1 {
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 600;
}

h2 {
  font-size: 15px;
  margin-bottom: 8px;
}

.estado {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  align-items: flex-start;
}

.estado.sin {
  background: #f5e9c4;
}

.titulo {
  font-weight: 700;
  font-size: 18px;
}

.sutil {
  font-size: 13px;
  color: var(--color-text-muted);
}

.error {
  font-size: 13px;
  color: var(--color-danger);
}

.lista {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lista li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  align-items: flex-start;
}

.rechazada {
  border-color: #e6b8b2;
}

.descartar {
  margin-top: 6px;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface-alt);
}

.cuenta {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
}
</style>
