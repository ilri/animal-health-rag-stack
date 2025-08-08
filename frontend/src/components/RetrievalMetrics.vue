<template>
  <div class="retrieval-metrics">
    <h2>Retrieval Metrics</h2>
    <div v-if="loading" class="loading">Loading retrieval metrics...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="summary" class="grid">
      <div class="card">
        <div class="label">Overall Precision</div>
        <div class="value">{{ (summary.overall_precision * 100).toFixed(1) }}%</div>
      </div>
      <div class="card">
        <div class="label">Precision@5</div>
        <div class="value">{{ (summary["precision@5"] * 100).toFixed(1) }}%</div>
      </div>
      <div class="card">
        <div class="label">Precision@10</div>
        <div class="value">{{ (summary["precision@10"] * 100).toFixed(1) }}%</div>
      </div>
      <div class="card">
        <div class="label">Total Judgments</div>
        <div class="value">{{ summary.total_judgments }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'RetrievalMetrics',
  setup() {
    const loading = ref(false)
    const error = ref('')
    const summary = ref(null)

    const loadSummary = async () => {
      loading.value = true
      error.value = ''
      try {
        const res = await fetch('/api/retrieval/eval/summary')
        if (!res.ok) throw new Error('Failed to load retrieval metrics')
        summary.value = await res.json()
      } catch (e) {
        error.value = e.message
      } finally {
        loading.value = false
      }
    }

    onMounted(loadSummary)

    return { loading, error, summary }
  }
}
</script>

<style scoped>
.retrieval-metrics { margin-top: 20px; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  text-align: center;
}
.label { color: #666; margin-bottom: 8px; }
.value { font-size: 28px; font-weight: bold; color: #333; }
.loading { color: #666; }
.error { color: #b00020; }
</style> 