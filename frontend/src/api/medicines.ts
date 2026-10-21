import apiClient from './client'
import type { Category, Medicine, PaginatedResponse, PaginationParams } from '@/types'

const medicineService = {
  // Categories
  listCategories: (params?: PaginationParams) =>
    apiClient.get<PaginatedResponse<Category>>('/categories/', { params }),

  createCategory: (data: Partial<Category>) =>
    apiClient.post<Category>('/categories/', data),

  updateCategory: (id: string, data: Partial<Category>) =>
    apiClient.patch<Category>(`/categories/${id}/`, data),

  deleteCategory: (id: string) =>
    apiClient.delete(`/categories/${id}/`),

  // Medicines
  list: (params?: PaginationParams & { search?: string; category?: string; dosage_form?: string }) =>
    apiClient.get<PaginatedResponse<Medicine>>('/medicines/', { params }),

  get: (id: string) =>
    apiClient.get<Medicine>(`/medicines/${id}/`),

  create: (data: Partial<Medicine>) =>
    apiClient.post<Medicine>('/medicines/', data),

  update: (id: string, data: Partial<Medicine>) =>
    apiClient.patch<Medicine>(`/medicines/${id}/`, data),

  deactivate: (id: string) =>
    apiClient.delete(`/medicines/${id}/`),
}

export default medicineService
