import apiClient from './client'
import type {
  Batch,
  StockMovement,
  PaginatedResponse,
  BatchFilters,
  MovementFilters,
  PharmacyDashboardStats,
  SystemDashboardStats,
  AvailabilityResult,
  AvailabilitySearchParams,
  SystemConfig,
} from '@/types'

const inventoryService = {
  // ---- Batches ----
  listBatches: (params?: BatchFilters) =>
    apiClient.get<PaginatedResponse<Batch>>('/batches/', { params }),

  getBatch: (id: string) =>
    apiClient.get<Batch>(`/batches/${id}/`),

  createBatch: (data: {
    medicine: string
    batch_number: string
    quantity: number
    received_date: string
    expiry_date: string
    supplier?: string
    unit_cost?: string
    notes?: string
  }) => apiClient.post<Batch>('/batches/', data),

  updateBatch: (id: string, data: Partial<Batch>) =>
    apiClient.patch<Batch>(`/batches/${id}/`, data),

  deleteBatch: (id: string) =>
    apiClient.delete(`/batches/${id}/`),

  getExpiringBatches: (params?: BatchFilters) =>
    apiClient.get<PaginatedResponse<Batch>>('/batches/expiring/', { params }),

  getExpiredBatches: (params?: BatchFilters) =>
    apiClient.get<PaginatedResponse<Batch>>('/batches/expired/', { params }),

  getLowStockBatches: (params?: BatchFilters) =>
    apiClient.get<PaginatedResponse<Batch>>('/batches/low-stock/', { params }),

  // ---- Movements ----
  listMovements: (params?: MovementFilters) =>
    apiClient.get<PaginatedResponse<StockMovement>>('/movements/', { params }),

  createMovement: (data: {
    batch: string
    movement_type: string
    quantity: number
    unit_price?: string
    reference_number?: string
    notes?: string
  }) => apiClient.post<StockMovement>('/movements/', data),

  approveMovement: (id: string) =>
    apiClient.post<StockMovement>(`/movements/${id}/approve/`),

  // ---- Dashboard ----
  getPharmacyDashboard: () =>
    apiClient.get<PharmacyDashboardStats>('/dashboard/pharmacy/'),

  getSystemDashboard: () =>
    apiClient.get<SystemDashboardStats>('/dashboard/system/'),

  // ---- Availability Search (public) ----
  searchAvailability: (params: AvailabilitySearchParams) =>
    apiClient.get<{ query: string; results: AvailabilityResult[] }>('/availability/', { params }),

  // ---- System Config ----
  getSystemConfig: () =>
    apiClient.get<SystemConfig>('/config/'),

  updateSystemConfig: (data: Partial<SystemConfig>) =>
    apiClient.patch<SystemConfig>('/config/', data),
}

export default inventoryService
