<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/api/http'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({ correo: '', password: '', recordar: false })
const error = ref('')
const cargando = ref(false)
const mostrarPassword = ref(false)

async function iniciarSesion() {
  error.value = ''
  cargando.value = true
  try {
    await auth.login(form.correo, form.password, form.recordar)
    // "/" redirige a la primera pantalla a la que el usuario tiene acceso
    router.push('/')
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : 'No se pudo iniciar sesión'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <main class="login">
    <section class="hero" aria-label="Centro de Rescate de Fauna Silvestre Yanacocha" />

    <section class="panel">
      <div class="card">
        <h1>¡Hola de nuevo!</h1>
        <p class="subtitle">Accede al sistema del centro</p>

        <form class="form" @submit.prevent="iniciarSesion">
          <div class="field">
            <label for="correo">Correo</label>
            <input
              id="correo"
              v-model.trim="form.correo"
              type="email"
              class="input"
              placeholder="usuario@yanacocha.com"
              autocomplete="username"
              required
            />
          </div>

          <div class="field">
            <label for="password">Contraseña</label>
            <div class="password-control">
              <input
                id="password"
                v-model="form.password"
                :type="mostrarPassword ? 'text' : 'password'"
                class="input"
                placeholder="••••••••"
                autocomplete="current-password"
                required
              />
              <button
                class="password-toggle"
                type="button"
                :aria-label="mostrarPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                :aria-pressed="mostrarPassword"
                @click="mostrarPassword = !mostrarPassword"
              >
                <svg
                  v-if="mostrarPassword"
                  viewBox="0 0 24 24"
                  width="19"
                  height="19"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M2.5 12s3.2-6 9.5-6 9.5 6 9.5 6-3.2 6-9.5 6-9.5-6-9.5-6Z"
                    stroke="currentColor"
                    stroke-width="1.7"
                  />
                  <circle cx="12" cy="12" r="2.7" stroke="currentColor" stroke-width="1.7" />
                </svg>
                <svg
                  v-else
                  viewBox="0 0 24 24"
                  width="19"
                  height="19"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M3 3l18 18M10.6 6.2A9.8 9.8 0 0 1 12 6c6.3 0 9.5 6 9.5 6a15 15 0 0 1-3.1 3.7M6.2 6.7C3.8 8.3 2.5 12 2.5 12s3.2 6 9.5 6c1 0 1.9-.2 2.7-.5"
                    stroke="currentColor"
                    stroke-width="1.7"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M9.9 9.9a3 3 0 0 0 4.2 4.2"
                    stroke="currentColor"
                    stroke-width="1.7"
                    stroke-linecap="round"
                  />
                </svg>
              </button>
            </div>
          </div>

          <label class="remember">
            <input v-model="form.recordar" type="checkbox" />
            Mantener sesión iniciada
          </label>

          <p v-if="error" class="alert-error">{{ error }}</p>

          <button type="submit" class="submit" :disabled="cargando">
            {{ cargando ? 'Ingresando…' : 'Iniciar sesión' }}
            <span aria-hidden="true">→</span>
          </button>
        </form>

        <p class="footnote">
          Acceso restringido · Personal del Centro de Rescate Yanacocha
        </p>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100%;
}

.hero {
  background: #1d3a1c url('@/assets/images/login-bg.png') center / cover no-repeat;
}

.panel {
  display: grid;
  place-items: center;
  padding: 32px;
  background: #f3eedf;
}

.card {
  width: 100%;
  max-width: 420px;
  padding: 40px 36px 28px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

h1 {
  font-family: var(--font-serif);
  font-size: 30px;
  font-weight: 600;
}

.subtitle {
  margin-top: 8px;
  color: var(--color-text-muted);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 32px;
}

.password-control {
  position: relative;
}

.password-control .input {
  padding-right: 46px;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 7px;
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  transform: translateY(-50%);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
}

.password-toggle:hover {
  background: var(--color-surface-alt);
  color: var(--color-text);
}

.password-toggle:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.remember {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-muted);
  cursor: pointer;
}

.remember input {
  accent-color: var(--color-primary);
}

.submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 8px;
  padding: 15px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-dark);
  color: #f3eedf;
  font-weight: 500;
  transition: background-color 0.15s;
}

.submit:hover:not(:disabled) {
  background: var(--color-dark-hover);
}

.footnote {
  margin-top: 28px;
  text-align: center;
  font-size: 12px;
  color: var(--color-text-subtle);
}

@media (max-width: 860px) {
  .login {
    grid-template-columns: 1fr;
  }

  .hero {
    min-height: 220px;
  }
}
</style>
