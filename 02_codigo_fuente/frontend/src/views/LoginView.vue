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

async function iniciarSesion() {
  error.value = ''
  cargando.value = true
  try {
    await auth.login(form.correo, form.password, form.recordar)
    router.push({ name: 'usuarios' })
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
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="input"
              placeholder="••••••••"
              autocomplete="current-password"
              required
            />
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
