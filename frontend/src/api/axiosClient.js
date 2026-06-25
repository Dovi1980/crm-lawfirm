import axios from 'axios'

const axiosClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  // Send the refresh-token HttpOnly cookie on same-origin requests.
  withCredentials: true,
})

// Request Interceptor: inject access token from in-memory/localStorage.
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Single-flight refresh: coalesce concurrent 401s into one /refresh call.
let refreshInFlight = null

async function performRefresh() {
  // The refresh token is read server-side from the HttpOnly cookie; no body.
  const response = await axios.post(
    '/api/auth/refresh',
    null,
    { withCredentials: true }
  )
  return response.data.access_token
}

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Never try to refresh on the refresh endpoint itself.
    const isAuthEndpoint = originalRequest?.url?.includes('/auth/refresh') ||
                           originalRequest?.url?.includes('/auth/login')

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true

      try {
        if (!refreshInFlight) {
          refreshInFlight = performRefresh().finally(() => { refreshInFlight = null })
        }
        const newAccessToken = await refreshInFlight

        localStorage.setItem('accessToken', newAccessToken)
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return axiosClient(originalRequest)
      } catch (refreshError) {
        localStorage.clear()
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default axiosClient
