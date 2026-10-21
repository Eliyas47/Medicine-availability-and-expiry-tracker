import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { BatchStatus } from '@/types'

// ---- Tailwind class merging ----

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ---- Date formatting ----

const DATE_LOCALE = 'en-ET'

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleDateString(DATE_LOCALE, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleString(DATE_LOCALE, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return '—'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(dateString)
}

export function daysUntilExpiry(expiryDate: string): number {
  const expiry = new Date(expiryDate)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diffTime = expiry.getTime() - today.getTime()
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

// ---- Status helpers ----

export function getBatchStatusLabel(status: BatchStatus): string {
  const labels: Record<BatchStatus, string> = {
    active: 'Active',
    low_stock: 'Low Stock',
    expiring_soon: 'Expiring Soon',
    expired: 'Expired',
    depleted: 'Depleted',
  }
  return labels[status] ?? status
}

export function getBatchStatusColor(status: BatchStatus): string {
  const colors: Record<BatchStatus, string> = {
    active: 'bg-green-100 text-green-800',
    low_stock: 'bg-orange-100 text-orange-800',
    expiring_soon: 'bg-amber-100 text-amber-800',
    expired: 'bg-red-100 text-red-800',
    depleted: 'bg-gray-100 text-gray-600',
  }
  return colors[status] ?? 'bg-gray-100 text-gray-600'
}

export function getExpiryColor(days: number): string {
  if (days < 0) return 'text-red-600 font-semibold'
  if (days <= 7) return 'text-red-500 font-medium'
  if (days <= 30) return 'text-orange-500 font-medium'
  if (days <= 90) return 'text-amber-600'
  return 'text-gray-600'
}

// ---- Number formatting ----

export function formatCurrency(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—'
  const num = typeof value === 'string' ? parseFloat(value) : value
  return new Intl.NumberFormat('en-ET', {
    style: 'currency',
    currency: 'ETB',
    minimumFractionDigits: 2,
  }).format(num)
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-ET').format(value)
}

// ---- API error helpers ----

export function getApiErrorMessage(error: unknown): string {
  if (!error) return 'An unexpected error occurred.'
  // Axios error shape
  const axiosError = error as { response?: { data?: { error?: { message?: string } } }; message?: string }
  return (
    axiosError?.response?.data?.error?.message ??
    axiosError?.message ??
    'An unexpected error occurred.'
  )
}

export function getApiFieldErrors(error: unknown): Record<string, string[]> {
  const axiosError = error as { response?: { data?: { error?: { details?: Record<string, string[]> } } } }
  return axiosError?.response?.data?.error?.details ?? {}
}

// ---- Miscellaneous ----

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return `${str.slice(0, maxLength)}…`
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

export function toTitleCase(str: string): string {
  return str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function downloadCSV(data: string, filename: string): void {
  const blob = new Blob([data], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
