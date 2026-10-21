import apiClient from './client'
import type { Pharmacy, PharmacyMembership, PaginatedResponse, PaginationParams } from '@/types'

const pharmacyService = {
  list: (params?: PaginationParams & { search?: string; city?: string; region?: string }) =>
    apiClient.get<PaginatedResponse<Pharmacy>>('/pharmacies/', { params }),

  get: (id: string) =>
    apiClient.get<Pharmacy>(`/pharmacies/${id}/`),

  create: (data: Partial<Pharmacy>) =>
    apiClient.post<Pharmacy>('/pharmacies/', data),

  update: (id: string, data: Partial<Pharmacy>) =>
    apiClient.patch<Pharmacy>(`/pharmacies/${id}/`, data),

  deactivate: (id: string) =>
    apiClient.delete(`/pharmacies/${id}/`),

  getMembers: (pharmacyId: string) =>
    apiClient.get<PaginatedResponse<PharmacyMembership>>(`/pharmacies/${pharmacyId}/members/`),

  addMember: (pharmacyId: string, data: { email: string; role: string }) =>
    apiClient.post<PharmacyMembership>(`/pharmacies/${pharmacyId}/members/`, data),

  removeMember: (pharmacyId: string, userId: string) =>
    apiClient.delete(`/pharmacies/${pharmacyId}/members/${userId}/`),
}

export default pharmacyService
