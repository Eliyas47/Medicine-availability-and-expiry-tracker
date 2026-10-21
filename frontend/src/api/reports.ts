import apiClient from './client'

export interface ReportParams {
  pharmacy?: string
  medicine?: string
  category?: string
  date_from?: string
  date_to?: string
  format?: 'json' | 'csv'
  page?: number
  page_size?: number
}

const reportService = {
  stockSummary: (params?: ReportParams) =>
    apiClient.get('/reports/stock-summary/', {
      params,
      responseType: params?.format === 'csv' ? 'blob' : 'json',
    }),

  expiring: (params?: ReportParams) =>
    apiClient.get('/reports/expiring/', {
      params,
      responseType: params?.format === 'csv' ? 'blob' : 'json',
    }),

  expired: (params?: ReportParams) =>
    apiClient.get('/reports/expired/', {
      params,
      responseType: params?.format === 'csv' ? 'blob' : 'json',
    }),

  movements: (params?: ReportParams) =>
    apiClient.get('/reports/movements/', {
      params,
      responseType: params?.format === 'csv' ? 'blob' : 'json',
    }),

  lowStock: (params?: ReportParams) =>
    apiClient.get('/reports/low-stock/', {
      params,
      responseType: params?.format === 'csv' ? 'blob' : 'json',
    }),
}

export default reportService
