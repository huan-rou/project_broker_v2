<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import type { CalculatorResult, DemoCase, DemoDocument, FactFindSnapshot, JobTrace } from '../types'

const route = useRoute()
const caseId = computed(() => Number(route.params.id))
const activeTab = ref<'documents' | 'factFind' | 'calculator' | 'results'>('documents')
const currentCase = ref<DemoCase | null>(null)
const documents = ref<DemoDocument[]>([])
const jobs = ref<Record<number, JobTrace[]>>({})
const factFind = ref<FactFindSnapshot | null>(null)
const results = ref<CalculatorResult[]>([])
const statusMessage = ref('')
const error = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const sortedResults = computed(() => [...results.value].sort((a, b) => b.max_borrowing_capacity - a.max_borrowing_capacity))

async function refresh() {
  error.value = ''
  try {
    const [caseData, docs, fact, calc] = await Promise.all([
      api.get<DemoCase>('/cases/' + caseId.value),
      api.get<DemoDocument[]>('/cases/' + caseId.value + '/documents'),
      api.get<FactFindSnapshot>('/cases/' + caseId.value + '/fact-find/current'),
      api.get<CalculatorResult[]>('/cases/' + caseId.value + '/calculator/results')
    ])
    currentCase.value = caseData
    documents.value = docs
    factFind.value = fact
    results.value = calc
    await Promise.all(docs.map((doc) => loadJobs(doc.id)))
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Could not load case'
  }
}

async function upload() {
  const files = fileInput.value?.files
  if (!files || files.length === 0) return
  const body = new FormData()
  body.append('file', files[0])
  await api.post<DemoDocument>('/cases/' + caseId.value + '/documents/upload', body)
  statusMessage.value = 'Document uploaded.'
  await refresh()
}

async function queue(doc: DemoDocument, action: 'process-ocr' | 'build-evidence' | 'map-fact-find') {
  const response = await api.post<{ message: string }>('/cases/' + caseId.value + '/documents/' + doc.id + '/' + action)
  statusMessage.value = response.message
  await loadJobs(doc.id)
}

async function loadJobs(documentId: number) {
  jobs.value[documentId] = await api.get<JobTrace[]>('/cases/' + caseId.value + '/documents/' + documentId + '/jobs')
}

async function applyPreview() {
  const firstPreview = documents.value.find((doc) => doc.fact_find_preview)?.fact_find_preview ?? {
    income: { gross_annual: 128000, source: 'manual preview', confidence: 0.8 }
  }
  factFind.value = await api.post<FactFindSnapshot>('/cases/' + caseId.value + '/fact-find/apply-preview', { changes: firstPreview })
  statusMessage.value = 'Fact Find v' + factFind.value.version + ' saved.'
}

async function autoPopulate() {
  const response = await api.post<{ status: string }>('/cases/' + caseId.value + '/calculator/auto-populate')
  statusMessage.value = 'Adapter package ' + response.status + '. Review lender-specific notes before run.'
}

async function runCalculators() {
  results.value = await api.post<CalculatorResult[]>('/cases/' + caseId.value + '/calculator/run')
  activeTab.value = 'results'
  statusMessage.value = 'Calculator run complete.'
}

function formatMoney(value: number) {
  return new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD', maximumFractionDigits: 0 }).format(value)
}

onMounted(refresh)
</script>

<template>
  <main class="case-page">
    <section class="case-header panel">
      <div>
        <p class="eyebrow">Case command centre</p>
        <h1>{{ currentCase?.name || 'Loading case...' }}</h1>
        <p>{{ currentCase?.notes }}</p>
      </div>
      <div class="workflow-ribbon">
        <span>Upload</span><span>OCR</span><span>Bridge</span><span>Review</span><span>Adapter</span><span>Results</span>
      </div>
    </section>

    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="statusMessage" class="success-text">{{ statusMessage }}</p>

    <nav class="tabs">
      <button :class="{ active: activeTab === 'documents' }" @click="activeTab = 'documents'">Documents</button>
      <button :class="{ active: activeTab === 'factFind' }" @click="activeTab = 'factFind'">Fact Find</button>
      <button :class="{ active: activeTab === 'calculator' }" @click="activeTab = 'calculator'">Calculator</button>
      <button :class="{ active: activeTab === 'results' }" @click="activeTab = 'results'">Results</button>
    </nav>

    <section v-if="activeTab === 'documents'" class="content-grid">
      <div class="panel">
        <h2>Document intake</h2>
        <input ref="fileInput" type="file" />
        <button class="primary-button" @click="upload">Upload to case</button>
      </div>
      <article v-for="doc in documents" :key="doc.id" class="panel document-card">
        <span class="status-pill">{{ doc.status }}</span>
        <h3>{{ doc.original_filename }}</h3>
        <p>Category: {{ doc.document_category || 'Unclassified' }}</p>
        <div class="button-row">
          <button @click="queue(doc, 'process-ocr')">Process OCR</button>
          <button @click="queue(doc, 'build-evidence')">Build evidence</button>
          <button @click="queue(doc, 'map-fact-find')">Map Fact Find</button>
        </div>
        <details>
          <summary>Job trace</summary>
          <ul class="trace-list">
            <li v-for="job in jobs[doc.id] || []" :key="job.id">
              <strong>{{ job.stage }}</strong> / {{ job.status }} - {{ job.message }}
              <span v-if="job.error_code">({{ job.error_code }})</span>
            </li>
          </ul>
        </details>
      </article>
    </section>

    <section v-if="activeTab === 'factFind'" class="panel">
      <div class="section-title">
        <h2>Fact Find v{{ factFind?.version }}</h2>
        <button class="primary-button" @click="applyPreview">Apply first preview</button>
      </div>
      <div class="fact-grid">
        <article v-for="(value, key) in factFind?.form_data" :key="String(key)" class="fact-section">
          <h3>{{ key }}</h3>
          <pre>{{ JSON.stringify(value, null, 2) }}</pre>
        </article>
      </div>
    </section>

    <section v-if="activeTab === 'calculator'" class="panel">
      <h2>Calculator adapters</h2>
      <p>Fact Find is the unified contract. Per-lender adapters decide how raw fields map into each calculator.</p>
      <div class="adapter-grid">
        <article><h3>BOCAL adapter</h3><p>Supports negative gearing fields for investment-purpose debt.</p></article>
        <article><h3>Brighten adapter</h3><p>Flags investment debt treatment for broker review before submission.</p></article>
      </div>
      <div class="button-row">
        <button class="primary-button" @click="autoPopulate">Auto-populate from Fact Find</button>
        <button class="primary-button" @click="runCalculators">Run BOCAL + Brighten</button>
      </div>
    </section>

    <section v-if="activeTab === 'results'" class="results-grid">
      <article v-for="result in sortedResults" :key="result.id" class="panel result-card">
        <span class="status-pill">{{ result.status }}</span>
        <h2>{{ result.lender }}</h2>
        <strong>{{ formatMoney(result.max_borrowing_capacity) }}</strong>
        <p>Monthly surplus: {{ formatMoney(result.monthly_surplus) }}</p>
        <p>Assessment rate: {{ result.assessment_rate }}%</p>
        <pre>{{ JSON.stringify(result.notes, null, 2) }}</pre>
      </article>
    </section>
  </main>
</template>
