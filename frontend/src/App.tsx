import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from '@/features/auth/AuthContext'
import { ProtectedRoute } from '@/features/auth/ProtectedRoute'
import { PublicLayout } from '@/layouts/PublicLayout'
import { DashboardLayout } from '@/layouts/DashboardLayout'

// Public pages
import { LandingPage } from '@/pages/public/LandingPage'
import { AvailabilitySearchPage } from '@/pages/public/AvailabilitySearchPage'

// Auth pages
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'

// Dashboard pages
import { DashboardOverviewPage } from '@/pages/dashboard/DashboardOverviewPage'
import { InventoryPage } from '@/pages/dashboard/InventoryPage'
import { BatchListPage } from '@/pages/dashboard/BatchListPage'
import { BatchFormPage } from '@/pages/dashboard/BatchFormPage'
import { MovementsPage } from '@/pages/dashboard/MovementsPage'
import { ExpiryPage } from '@/pages/dashboard/ExpiryPage'
import { AlertsPage } from '@/pages/dashboard/AlertsPage'
import { ReportsPage } from '@/pages/dashboard/ReportsPage'
import { PharmacyProfilePage } from '@/pages/dashboard/PharmacyProfilePage'
import { MedicineCatalogPage } from '@/pages/dashboard/MedicineCatalogPage'
import { UsersPage } from '@/pages/dashboard/UsersPage'
import { AuditLogPage } from '@/pages/dashboard/AuditLogPage'
import { SettingsPage } from '@/pages/dashboard/SettingsPage'
import { UserProfilePage } from '@/pages/dashboard/UserProfilePage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route element={<PublicLayout />}>
              <Route index element={<LandingPage />} />
              <Route path="search" element={<AvailabilitySearchPage />} />
            </Route>

            {/* Auth routes */}
            <Route path="auth">
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
            </Route>

            {/* Protected dashboard routes */}
            <Route
              path="dashboard"
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="overview" replace />} />
              <Route path="overview" element={<DashboardOverviewPage />} />
              <Route path="inventory" element={<InventoryPage />} />
              <Route path="batches" element={<BatchListPage />} />
              <Route path="batches/new" element={<BatchFormPage />} />
              <Route path="batches/:id/edit" element={<BatchFormPage />} />
              <Route path="movements" element={<MovementsPage />} />
              <Route path="expiry" element={<ExpiryPage />} />
              <Route path="alerts" element={<AlertsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="pharmacy" element={<PharmacyProfilePage />} />
              <Route
                path="medicines"
                element={
                  <ProtectedRoute roles={['system_admin']}>
                    <MedicineCatalogPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="users"
                element={
                  <ProtectedRoute roles={['system_admin', 'pharmacy_admin']}>
                    <UsersPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="audit"
                element={
                  <ProtectedRoute roles={['system_admin']}>
                    <AuditLogPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="settings"
                element={
                  <ProtectedRoute roles={['system_admin']}>
                    <SettingsPage />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Profile */}
            <Route
              path="profile"
              element={
                <ProtectedRoute>
                  <UserProfilePage />
                </ProtectedRoute>
              }
            />

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1e293b',
              color: '#f8fafc',
              borderRadius: '0.5rem',
            },
            success: { iconTheme: { primary: '#0d9488', secondary: '#f8fafc' } },
            error: { iconTheme: { primary: '#ef4444', secondary: '#f8fafc' } },
          }}
        />
      </AuthProvider>
    </QueryClientProvider>
  )
}
