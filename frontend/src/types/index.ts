// ============================================================
// Core TypeScript types for the Medicine Tracker application
// ============================================================

// ---- Enums ----

export type UserRole = 'system_admin' | 'pharmacy_admin' | 'inventory_staff'

export type BatchStatus = 'active' | 'low_stock' | 'expiring_soon' | 'expired' | 'depleted'

export type MovementType =
  | 'received'
  | 'sold'
  | 'dispensed'
  | 'adjustment'
  | 'expired_removal'
  | 'correction'

export type DosageForm =
  | 'tablet'
  | 'capsule'
  | 'syrup'
  | 'injection'
  | 'cream'
  | 'drops'
  | 'suppository'
  | 'patch'
  | 'inhaler'
  | 'other'

export type AuditAction = 'create' | 'update' | 'delete' | 'login' | 'logout'

// ---- User / Auth ----

export interface User {
  id: string
  email: string
  full_name: string
  phone: string
  role: UserRole
  is_active: boolean
  date_joined: string
  last_login: string | null
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface LoginResponse extends AuthTokens {
  user: User
}

// ---- Pharmacy ----

export interface Pharmacy {
  id: string
  name: string
  license_number: string
  address: string
  city: string
  region: string
  phone: string
  email: string
  latitude: number | null
  longitude: number | null
  operating_hours: Record<string, string> | null
  is_active: boolean
  expiry_warning_days: number
  stale_stock_days: number
  created_at: string
  updated_at: string
}

export interface PharmacyMembership {
  id: string
  user: Pick<User, 'id' | 'email' | 'full_name' | 'role'>
  pharmacy: Pick<Pharmacy, 'id' | 'name'>
  role: 'pharmacy_admin' | 'inventory_staff'
  is_active: boolean
  created_at: string
}

// ---- Medicine ----

export interface Category {
  id: string
  name: string
  description: string
  is_active: boolean
  created_at: string
}

export interface Medicine {
  id: string
  generic_name: string
  brand_name: string
  strength: string
  dosage_form: DosageForm
  category: Category | null
  description: string
  unit_of_measure: string
  requires_prescription: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

// ---- Inventory ----

export interface Batch {
  id: string
  pharmacy: Pick<Pharmacy, 'id' | 'name'>
  medicine: Pick<Medicine, 'id' | 'generic_name' | 'brand_name' | 'strength' | 'dosage_form'>
  batch_number: string
  quantity: number
  received_date: string
  expiry_date: string
  supplier: string
  unit_cost: string | null
  status: BatchStatus
  days_until_expiry: number
  notes: string
  created_by: Pick<User, 'id' | 'full_name'> | null
  created_at: string
  updated_at: string
}

export interface StockMovement {
  id: string
  pharmacy: Pick<Pharmacy, 'id' | 'name'>
  medicine: Pick<Medicine, 'id' | 'generic_name'>
  batch: Pick<Batch, 'id' | 'batch_number'> | null
  movement_type: MovementType
  quantity: number
  unit_price: string | null
  reference_number: string
  notes: string
  performed_by: Pick<User, 'id' | 'full_name'> | null
  is_approved: boolean
  approved_by: Pick<User, 'id' | 'full_name'> | null
  approved_at: string | null
  created_at: string
}

// ---- Dashboard ----

export interface PharmacyDashboardStats {
  pharmacy: Pick<Pharmacy, 'id' | 'name'>
  stats: {
    total_medicines: number
    total_batches: number
    active_batches: number
    expired_batches: number
    expiring_soon_batches: number
    low_stock_items: number
    depleted_items: number
    total_usable_stock_value: string
  }
  expiry_breakdown: {
    this_week: number
    this_month: number
    within_warning_window: number
  }
  stock_by_category: Array<{
    category: string
    usable_quantity: number
    batch_count: number
  }>
  recent_movements: StockMovement[]
}

export interface SystemDashboardStats {
  total_pharmacies: number
  total_medicines: number
  total_users: number
  total_batches: number
  system_low_stock: number
  system_expired: number
  system_expiring_soon: number
}

// ---- Availability Search ----

export interface AvailabilityResult {
  pharmacy: Pick<Pharmacy, 'id' | 'name' | 'address' | 'city' | 'phone'>
  medicine: Pick<Medicine, 'id' | 'generic_name' | 'brand_name' | 'strength' | 'dosage_form' | 'requires_prescription'>
  usable_quantity: number
  last_confirmed_at: string | null
  is_stale: boolean
}

// ---- Audit ----

export interface AuditLog {
  id: number
  user: Pick<User, 'id' | 'full_name'> | null
  user_email: string
  action: AuditAction
  model_name: string
  object_id: string
  object_repr: string
  changes: Record<string, [unknown, unknown]> | null
  ip_address: string | null
  created_at: string
}

// ---- System Config ----

export interface SystemConfig {
  expiry_warning_days: number
  stale_stock_days: number
  low_stock_default_threshold: number
  updated_at: string
}

// ---- Pagination ----

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  total_pages: number
  current_page: number
  results: T[]
}

// ---- API Error ----

export interface ApiError {
  error: {
    code: string
    message: string
    details?: Record<string, string[]>
  }
}

// ---- Query Params ----

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface BatchFilters extends PaginationParams {
  medicine?: string
  status?: BatchStatus
  expiry_before?: string
  expiry_after?: string
  search?: string
  ordering?: string
}

export interface MovementFilters extends PaginationParams {
  medicine?: string
  movement_type?: MovementType
  date_from?: string
  date_to?: string
  batch?: string
}

export interface AvailabilitySearchParams {
  medicine: string
  city?: string
  region?: string
}
