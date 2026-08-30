<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useSessionStore } from '../stores/session'

const username = ref('broker@example.com')
const password = ref('demo')
const error = ref('')
const loading = ref(false)
const router = useRouter()
const session = useSessionStore()

async function login() {
  loading.value = true
  error.value = ''
  try {
    const result = await api.post<{ token: string; display_name: string; role: string }>('/auth/login', { username: username.value, password: password.value })
    session.setSession(result.token, result.display_name, result.role)
    router.push('/cases')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="hero-card">
      <p class="eyebrow">Australian broker workflow</p>
      <h1>Turn messy loan documents into a lender-ready assessment trail.</h1>
      <p>Thin slice covering case intake, document jobs, Fact Find review, calculator adapters, and borrowing results.</p>
    </section>
    <form class="panel login-card" @submit.prevent="login">
      <h2>Sign in</h2>
      <label>Email<input v-model="username" /></label>
      <label>Password<input v-model="password" type="password" /></label>
      <button class="primary-button" :disabled="loading">{{ loading ? 'Signing in...' : 'Enter workspace' }}</button>
      <p v-if="error" class="error-text">{{ error }}</p>
    </form>
  </main>
</template>
