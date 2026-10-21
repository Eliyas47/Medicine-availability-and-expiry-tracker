/**
 * Axios client with:
 * - Base URL from VITE_API_BASE_URL
 * - Request interceptor: attaches JWT access token
 * - Response interceptor: silent token refresh on 401, then retry once
 */
import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

// Token storage keys
export const ACCESS_TOKEN_KEY = 'mt_access_token'
export const REFRESH_TOKEN_KEY = 'mt_refresh_token'

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

// ---- Axios instance ----

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// ---- Request interceptor ----

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ---- Response interceptor with refresh logic ----

let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token!)
    }
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Only attempt refresh on 401, and only once
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/token/refresh/')
    ) {
      if (isRefreshing) {
        // Queue while a refresh is already in progress
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        clearTokens()
        processQueue(error, null)
        isRefreshing = false
        window.dispatchEvent(new CustomEvent('auth:logout'))
        return Promise.reject(error)
      }

      try {
        const { data } = await axios.post<{ access: string; refresh: string }>(
          `${BASE_URL}/auth/token/refresh/`,
          { refresh: refreshToken },
        )
        setTokens(data.access, data.refresh)
        apiClient.defaults.headers.common.Authorization = `Bearer ${data.access}`
        processQueue(null, data.access)
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        clearTokens()
        processQueue(refreshError, null)
        window.dispatchEvent(new CustomEvent('auth:logout'))
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default apiClient
