import { ref, computed } from 'vue'

// Global admin state
const adminStatus = ref(null)
const isLoading = ref(false)

export function useAdmin() {
  const isAdmin = computed(() => adminStatus.value?.is_admin || false)
  const adminInfo = computed(() => adminStatus.value || {})

  const checkAdminStatus = async () => {
    if (isLoading.value) return adminStatus.value

    try {
      isLoading.value = true
      // Check current URL for admin parameters
      const urlParams = new URLSearchParams(window.location.search)
      const adminParam = urlParams.get('admin')
      
      let headers = {}
      if (adminParam && adminParam !== 'true') {
        // If admin parameter is not just 'true', treat it as a token
        headers['X-Admin-Token'] = adminParam
      } else if (adminParam === 'true') {
        headers['X-Admin-Mode'] = 'true'
      }

      const response = await fetch('/api/admin/status', {
        headers: headers
      })
      
      if (response.ok) {
        const data = await response.json()
        adminStatus.value = data
        return data
      }
    } catch (error) {
      console.error('Error checking admin status:', error)
    } finally {
      isLoading.value = false
    }
    
    return adminStatus.value
  }

  const enableAdminMode = (token = 'true') => {
    const url = new URL(window.location)
    url.searchParams.set('admin', token)
    window.location.href = url.toString()
  }

  const disableAdminMode = () => {
    const url = new URL(window.location)
    url.searchParams.delete('admin')
    window.location.href = url.toString()
  }

  const makeAdminRequest = async (url, options = {}) => {
    // Add admin headers to requests
    const urlParams = new URLSearchParams(window.location.search)
    const adminParam = urlParams.get('admin')
    
    const headers = {
      ...options.headers
    }

    if (adminParam && adminParam !== 'true') {
      headers['X-Admin-Token'] = adminParam
    } else if (adminParam === 'true') {
      headers['X-Admin-Mode'] = 'true'
    }

    return fetch(url, {
      ...options,
      headers
    })
  }

  return {
    isAdmin,
    adminInfo,
    isLoading,
    checkAdminStatus,
    enableAdminMode,
    disableAdminMode,
    makeAdminRequest
  }
}