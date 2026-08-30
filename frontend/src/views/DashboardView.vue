<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import type { DemoCase } from '../types'

const router = useRouter()
const cases = ref<DemoCase[]>([])
const query = ref('')
const newCaseName = ref('')
const loading = ref(false)
const error = ref('')

const filteredCases = computed(() => {
  const needle = query.value.toLowerCase().trim()
  if (!needle) return cases.value
  return cases.value.filter((item) => item.name.toLowerCase().includes(needle) || item.status.toLowerCase().includes(needle))
})

async function loadCases() {
  loading.value = true
  error.value = ''
  try {
    cases.value = await api.get<DemoCase[]>('/cases')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load cases'
  } finally {
    loading.value = false
  }
}

async function createCase() {
  const name = newCaseName.value.trim()
  if (!name) return
  const created = await api.post<DemoCase>('/cases', { name, notes: 'Created from frontend command centre.' })
  newCaseName.value = ''
  cases.value = [created, ...cases.value]
  router.push('/cases/' + created.id)
}

onMounted(loadCases)
</script>

<template>
  <main class="page-grid">
    <section class="page-heading">
      <p class="eyebrow">Shared broker workspace</p>
      <h1>Case dashboard</h1>
      <p>Start from a case, then move through documents, bridge evidence, Fact Find, adapters, and results.</p>
    </section>

    <section class="metric-row">
      <article class="metric-card"><strong>{{ cases.length }}</strong><span>Open cases</span></article>
      <article class="metric-card"><strong>4</strong><span>Workflow stages</span></article>
      <article class="metric-card"><strong>2</strong><span>Calculator adapters</span></article>
    </section>

    <section class="toolbar panel">
      <input v-model="query" placeholder="Search cases" />
      <input v-model="newCaseName" placeholder="New case name" @keyup.enter="createCase" />
      <button class="primary-button" @click="createCase">Create case</button>
    </section>

    <p v-if="loading">Loading cases...</p>
    <p v-if="error" class="error-text">{{ error }}</p>

    <section class="case-grid">
      <article v-for="item in filteredCases" :key="item.id" class="panel case-card" @click="router.push('/cases/' + item.id)">
        <div>
          <span class="status-pill">{{ item.status }}</span>
          <h2>{{ item.name }}</h2>
          <p>{{ item.notes || 'No notes recorded yet.' }}</p>
        </div>
        <small>Updated {{ new Date(item.updated_at).toLocaleString() }}</small>
      </article>
    </section>
  </main>
</template>
