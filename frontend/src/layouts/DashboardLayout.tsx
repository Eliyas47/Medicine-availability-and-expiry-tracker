import { useState } from 'react'
import { Outlet, NavLink, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/features/auth/AuthContext'
import { cn } from '@/utils'
import {
  LayoutDashboard, Package, Layers, ArrowLeftRight,
  AlertTriangle, Bell, FileText, Building2, BookOpen,
  Users, ScrollText, Settings, Pill, LogOut, User,
  ChevronRight, Menu,
} from 'lucide-react'

interface NavItem {
  to: string
  label: string
  icon: React.ElementType
  roles?: string[]
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard/overview', label: 'Overview', icon: LayoutDashboard },
  { to: '/dashboard/inventory', label: 'Inventory', icon: Package },
  { to: '/dashboard/batches', label: 'Batches', icon: Layers },
  { to: '/dashboard/movements', label: 'Movements', icon: ArrowLeftRight },
  { to: '/dashboard/expiry', label: 'Expiry', icon: AlertTriangle },
  { to: '/dashboard/alerts', label: 'Alerts', icon: Bell },
  { to: '/dashboard/reports', label: 'Reports', icon: FileText },
  { to: '/dashboard/pharmacy', label: 'Pharmacy', icon: Building2 },
]

const ADMIN_NAV_ITEMS: NavItem[] = [
  { to: '/dashboard/medicines', label: 'Medicines', icon: BookOpen, roles: ['system_admin'] },
  { to: '/dashboard/users', label: 'Users', icon: Users, roles: ['system_admin', 'pharmacy_admin'] },
  { to: '/dashboard/audit', label: 'Audit Log', icon: ScrollText, roles: ['system_admin'] },
  { to: '/dashboard/settings', label: 'Settings', icon: Settings, roles: ['system_admin'] },
]

function SidebarLink({ item, onClick }: { item: NavItem; onClick?: () => void }) {
  return (
    <NavLink
      to={item.to}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive
            ? 'bg-brand-600 text-white'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
        )
      }
    >
      <item.icon className="h-4 w-4 flex-shrink-0" />
      {item.label}
    </NavLink>
  )
}

function Sidebar({ onClose }: { onClose?: () => void }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const visibleAdminItems = ADMIN_NAV_ITEMS.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role)),
  )

  const handleLogout = async () => {
    await logout()
    navigate('/auth/login')
  }

  return (
    <div className="flex h-full flex-col bg-white border-r border-slate-200">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 px-4 border-b border-slate-200">
        <Pill className="h-6 w-6 text-brand-600" />
        <span className="font-semibold text-slate-900">Medicine Tracker</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto sidebar-scroll p-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <SidebarLink key={item.to} item={item} onClick={onClose} />
        ))}

        {visibleAdminItems.length > 0 && (
          <>
            <div className="pt-4 pb-1 px-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Administration
              </p>
            </div>
            {visibleAdminItems.map((item) => (
              <SidebarLink key={item.to} item={item} onClick={onClose} />
            ))}
          </>
        )}
      </nav>

      {/* User section */}
      <div className="border-t border-slate-200 p-3 space-y-1">
        <Link
          to="/profile"
          onClick={onClose}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
        >
          <User className="h-4 w-4" />
          <div className="flex-1 min-w-0">
            <p className="truncate font-medium text-slate-900">{user?.full_name}</p>
            <p className="truncate text-xs text-slate-500">{user?.email}</p>
          </div>
          <ChevronRight className="h-4 w-4 flex-shrink-0" />
        </Link>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </div>
  )
}

export function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user } = useAuth()

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 flex-shrink-0">
        <Sidebar />
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-slate-900/50"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 w-72 flex flex-col">
            <Sidebar onClose={() => setSidebarOpen(false)} />
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-16 items-center gap-4 border-b border-slate-200 bg-white px-4 sm:px-6">
          <button
            className="lg:hidden p-2 rounded-md text-slate-600 hover:text-brand-600 hover:bg-slate-100"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="flex-1" />

          {/* User info badge */}
          <div className="hidden sm:flex items-center gap-2 text-sm text-slate-600">
            <div className="h-7 w-7 rounded-full bg-brand-600 text-white flex items-center justify-center text-xs font-semibold">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <span className="font-medium">{user?.full_name}</span>
          </div>
        </header>

        {/* Scrollable page content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
