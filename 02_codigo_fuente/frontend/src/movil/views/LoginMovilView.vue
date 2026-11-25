<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError } from '@/api/http'
import logo from '@/assets/images/logo-yanacocha.png'
import { MODULO_PLANIFICACION } from '@/config/modulos'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({ correo: '', password: '' })
const error = ref('')
const cargando = ref(false)
const mostrarPassword = ref(false)

async function iniciarSesion() {
  error.value = ''
  cargando.value = true
  try {
    // En el móvil la sesión siempre se mantiene: se trabaja en campo, a menudo sin conexión
    await auth.login(form.correo, form.password, true)
    if (!auth.tieneAcceso(MODULO_PLANIFICACION)) {
      auth.logout()
      error.value = 'Tu rol no tiene acceso a las actividades del centro.'
      return
    }
    router.push({ name: 'actividades' })
  } catch (e) {
    error.value =
      e instanceof ApiError && e.status === 0
        ? 'Sin conexión. Para iniciar sesión necesitas señal; después podrás trabajar sin ella.'
        : e instanceof ApiError
          ? e.message
          : 'No se pudo iniciar sesión'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <main class="login">
    <img class="logo" :src="logo" alt="Centro de Rescate de Fauna Silvestre Yanacocha" />

    <form class="tarjeta" @submit.prevent="iniciarSesion">
      <h1>¡Hola de nuevo!</h1>
      <p class="sub">Accede para ver tus actividades</p>

      <div class="campo">
        <label for="correo">Correo</label>
        <input
          id="correo"
          v-model.trim="form.correo"
          type="email"
          class="m-input"
          placeholder="usuario@yanacocha.com"
          autocomplete="username"
          autocapitalize="none"
          required
        />
      </div>

      <div class="campo">
        <label for="password">Contraseña</label>
        <div class="password">
          <input
            id="password"
            v-model="form.password"
            :type="mostrarPassword ? 'text' : 'password'"
            class="m-input"
            placeholder="••••••••"
            autocomplete="current-password"
            required
          />
          <button type="button" class="ojo" @click="mostrarPassword = !mostrarPassword">
            {{ mostrarPassword ? 'Ocultar' : 'Ver' }}
          </button>
        </div>
      </div>

      <p v-if="error" class="alert-error">{{ error }}</p>

      <button type="submit" class="m-btn m-btn-primario m-btn-bloque" :disabled="cargando">
        {{ cargando ? 'Ingresando…' : 'Ingresar' }}
      </button>
    </form>
  </main>
</template>

<style scoped>
.login {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 24px 20px calc(24px + env(safe-area-inset-bottom));
  background: #1d3a1c url('@/assets/images/login-bg.png') center / cover no-repeat;
}

.logo {
  width: 150px;
  max-width: 50%;
}

.tarjeta {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px 20px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

h1 {
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 600;
}

.sub {
  margin-top: -10px;
  color: var(--color-text-muted);
}

.campo {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.password {
  position: relative;
}

.password .m-input {
  padding-right: 80px;
}

.ojo {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  min-width: 72px;
  border: none;
  background: transparent;
  color: var(--color-primary);
  font-weight: 600;
}
</style>
