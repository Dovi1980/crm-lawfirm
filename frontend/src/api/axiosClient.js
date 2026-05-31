import axios from 'axios'

const axiosClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: Automatically inject access token if available
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response Interceptor: Automatically handle token refreshing on 401
axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const refreshToken = localStorage.getItem('refreshToken')
      if (!refreshToken) {
        // Clear local storage and redirect to login
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        // Attempt token refresh rotation via POST
        // Note: The refresh endpoint expects query parameter 'refresh_token'
        const response = await axios.post(`/api/auth/refresh?refresh_token=${refreshToken}`)
        
        if (response.status === 200) {
          const { access_token, refresh_token } = response.data
          
          localStorage.setItem('accessToken', access_token)
          localStorage.setItem('refreshToken', refresh_token)
          
          // Re-attempt original failed request with the new active token
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return axiosClient(originalRequest)
        }
      } catch (refreshError) {
        // Refresh token itself expired or revoked
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Generic error handling formatting
    return Promise.reject(error)
  }
)

export default axiosClient
