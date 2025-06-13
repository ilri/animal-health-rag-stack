import { createApp } from 'vue'
import { createStore } from 'vuex'
import App from './App.vue'
import router from './router'
import './assets/main.css'

// Create Vuex store
const store = createStore({
  state() {
    return {
      query: '',
      results: null,
      loading: false,
      error: null,
      showIngestionProgress: true
    }
  },
  mutations: {
    setQuery(state, query) {
      state.query = query;
    },
    setResults(state, results) {
      state.results = results;
    },
    setLoading(state, loading) {
      state.loading = loading;
    },
    setError(state, error) {
      state.error = error;
    },
    setShowIngestionProgress(state, value) {
      state.showIngestionProgress = value;
    }
  },
  getters: {
    showIngestionProgress: state => {
      return state.showIngestionProgress;
    }
  },
  actions: {
    async submitQuery({ commit }, query) {
      try {
        commit('setLoading', true);
        commit('setError', null);
        commit('setQuery', query);
        
        const response = await fetch('/api/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            query: query,
            max_results: 5,
            use_memory: true
          })
        });
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        commit('setResults', data);
      } catch (error) {
        console.error('Error submitting query:', error);
        commit('setError', error.message);
      } finally {
        commit('setLoading', false);
      }
    }
  }
})

createApp(App)
  .use(store)
  .use(router)
  .mount('#app')