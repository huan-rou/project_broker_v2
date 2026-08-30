<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSessionStore } from './stores/session'

const session = useSessionStore()
const router = useRouter()

function logout() {
  session.clear()
  router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/cases">
        <span class="brand-mark">PB</span>
        <span>
          <strong>Project Broker V2</strong>
          <small>Thin-slice command centre</small>
        </span>
      </RouterLink>
      <nav class="top-actions">
        <a href="http://localhost:8000/api/v1/system/preflight" target="_blank" rel="noreferrer">Preflight</a>
        <button v-if="session.token" class="ghost-button" @click="logout">Logout</button>
      </nav>
    </header>
    <RouterView />
  </div>
</template>
