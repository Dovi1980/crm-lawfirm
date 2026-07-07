import axios from 'axios'
import { getAccessToken, setAccessToken, clearAccessToken } from './tokenStore'

const axiosClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  // Send the refresh-token HttpOnly cookie on same-origin requests.
  withCredentials: true,
})

// Request Interceptor: inject the in-memory access token.
axiosClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
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

/**
 * Silent refresh used on app load: exchanges the HttpOnly refresh cookie for a
 * fresh access token (kept in memory). Returns the token, or null if there's no
 * valid session. Does not redirect.
 */
export async function silentRefresh() {
  try {
    const token = await performRefresh()
    setAccessToken(token)
    return token
  } catch {
    clearAccessToken()
    return null
  }
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

        setAccessToken(newAccessToken)
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return axiosClient(originalRequest)
      } catch (refreshError) {
        clearAccessToken()
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
