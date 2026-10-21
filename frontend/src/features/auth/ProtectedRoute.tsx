import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { UserRole } from '@/types'

interface ProtectedRouteProps {
  children: React.ReactNode
  roles?: UserRole[]
}

/**
 * Wraps a route to require authentication.
 * Optionally restricts to specific roles.
 * Redirects to /auth/login with the current location saved in state
 * so the user is returned after successful login.
 */
export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />
  }

  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/dashboard/overview" replace />
  }

  return <>{children}</>
}
