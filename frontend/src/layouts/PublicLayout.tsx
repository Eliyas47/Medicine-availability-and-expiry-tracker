import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/AuthContext'
import { Pill, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/utils'

export function PublicLayout() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Top navigation */}
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 text-brand-600 hover:text-brand-700">
              <Pill className="h-6 w-6" />
              <span className="font-semibold text-lg hidden sm:block">Medicine Tracker</span>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/" className="text-sm font-medium text-slate-600 hover:text-brand-600 transition-colors">
                Home
              </Link>
              <Link to="/search" className="text-sm font-medium text-slate-600 hover:text-brand-600 transition-colors">
                Find Medicine
              </Link>
              {isAuthenticated ? (
                <button
                  onClick={() => navigate('/dashboard/overview')}
                  className="btn-primary text-sm"
                >
                  Dashboard
                </button>
              ) : (
                <div className="flex items-center gap-3">
                  <Link to="/auth/login" className="text-sm font-medium text-slate-600 hover:text-brand-600">
                    Sign In
                  </Link>
                  <Link to="/auth/register" className="btn-primary text-sm">
                    Register Pharmacy
                  </Link>
                </div>
              )}
            </nav>

            {/* Mobile hamburger */}
            <button
              className="md:hidden p-2 rounded-md text-slate-600 hover:text-brand-600 hover:bg-slate-100"
              onClick={() => setMenuOpen((o) => !o)}
              aria-label="Toggle menu"
            >
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        <div className={cn('md:hidden border-t border-slate-200 bg-white', !menuOpen && 'hidden')}>
          <nav className="flex flex-col px-4 py-3 gap-1">
            <Link to="/" className="px-3 py-2 text-sm font-medium text-slate-700 rounded-md hover:bg-slate-100">Home</Link>
            <Link to="/search" className="px-3 py-2 text-sm font-medium text-slate-700 rounded-md hover:bg-slate-100">Find Medicine</Link>
            {isAuthenticated ? (
              <Link to="/dashboard/overview" className="px-3 py-2 text-sm font-medium text-brand-600 rounded-md hover:bg-brand-50">Dashboard</Link>
            ) : (
              <>
                <Link to="/auth/login" className="px-3 py-2 text-sm font-medium text-slate-700 rounded-md hover:bg-slate-100">Sign In</Link>
                <Link to="/auth/register" className="px-3 py-2 text-sm font-medium text-brand-600 rounded-md hover:bg-brand-50">Register Pharmacy</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-slate-900 text-slate-300">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-white">
              <Pill className="h-5 w-5 text-brand-400" />
              <span className="font-semibold">Medicine Tracker</span>
            </div>
            <p className="text-sm text-center">
              Supporting better medicine inventory management in Ethiopia.
            </p>
            <p className="text-sm">
              © {new Date().getFullYear()} Medicine Tracker. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
