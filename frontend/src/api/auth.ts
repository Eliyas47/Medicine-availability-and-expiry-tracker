import apiClient from './client'
import type { LoginResponse, User } from '@/types'

export interface RegisterData {
  email: string
  full_name: string
  phone?: string
  password: string
  password_confirm: string
}

export interface LoginData {
  email: string
  password: string
}

export interface ChangePasswordData {
  current_password: string
  new_password: string
  new_password_confirm: string
}

const authService = {
  register: (data: RegisterData) =>
    apiClient.post<{ message: string }>('/auth/register/', data),

  login: (data: LoginData) =>
    apiClient.post<LoginResponse>('/auth/login/', data),

  logout: (refresh: string) =>
    apiClient.post('/auth/logout/', { refresh }),

  refreshToken: (refresh: string) =>
    apiClient.post<{ access: string; refresh: string }>('/auth/token/refresh/', { refresh }),

  getProfile: () =>
    apiClient.get<User>('/auth/profile/'),

  updateProfile: (data: Partial<Pick<User, 'full_name' | 'phone'>>) =>
    apiClient.patch<User>('/auth/profile/', data),

  changePassword: (data: ChangePasswordData) =>
    apiClient.post('/auth/change-password/', data),
}

export default authService
