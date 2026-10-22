import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/features/auth/AuthContext'
import inventoryService from '@/api/inventory'
import { formatDateTime, formatCurrency, getBatchStatusColor, getBatchStatusLabel, formatRelativeTime } from '@/utils'
import {
  Package, AlertTriangle, Bell, XCircle, TrendingDown,
  Activity, Loader2, RefreshCw
} from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer,
} from 'recharts'
import type { PharmacyDashboardStats } from '@/types'

const COLORS = ['#0d9488', '#14b8a6', '#2dd4bf', '#5eead4', '#99f6e4', '#f59e0b', '#ef4444']

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: string | number; icon: React.ElementType; color: string
}) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-lg flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
      </div>
    </div>
  )
}

function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-200 rounded ${className}`} />
}

export function DashboardOverviewPage() {
  const { user } = useAuth()

  const { data: response, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard', 'pharmacy'],
    queryFn: () => inventoryService.getPharmacyDashboard(),
    select: (r) => r.data as PharmacyDashboardStats,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <div className="grid lg:grid-cols-2 gap-6">
          <Skeleton className="h-72" />
          <Skeleton className="h-72" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-center">
        <p className="text-red-700 font-medium">Failed to load dashboard</p>
        <button onClick={() => refetch()} className="btn-secondary mt-3 gap-2">
          <RefreshCw className="h-4 w-4" /> Try again
        </button>
      </div>
    )
  }

  const d = response!
  const stats = d.stats

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">{d.pharmacy.name}</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Welcome back, {user?.full_name?.split(' ')[0]}
          </p>
        </div>
        <button onClick={() => refetch()} className="btn-ghost gap-2 text-sm">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Medicines" value={stats.total_medicines} icon={Package} color="bg-brand-100 text-brand-600" />
        <StatCard label="Active Batches" value={stats.active_batches} icon={Activity} color="bg-green-100 text-green-600" />
        <StatCard label="Low Stock Items" value={stats.low_stock_items} icon={Bell} color="bg-orange-100 text-orange-600" />
        <StatCard label="Expired Batches" value={stats.expired_batches} icon={XCircle} color="bg-red-100 text-red-600" />
      </div>

      {/* Secondary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Expiring this week', value: d.expiry_breakdown.this_week, color: 'text-red-600' },
          { label: 'Expiring this month', value: d.expiry_breakdown.this_month, color: 'text-orange-500' },
          { label: `Within warning window`, value: d.expiry_breakdown.within_warning_window, color: 'text-amber-600' },
          { label: 'Depleted items', value: stats.depleted_items, color: 'text-slate-500' },
        ].map((s) => (
          <div key={s.label} className="card p-4 text-center">
            <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-slate-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Category pie chart */}
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 mb-4">Stock by Category</h2>
          {d.stock_by_category.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">No category data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={d.stock_by_category} cx="50%" cy="50%" outerRadius={80}
                  dataKey="usable_quantity" nameKey="category" label={({ category }) => category}>
                  {d.stock_by_category.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => [`${v} units`, 'Quantity']} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Summary card */}
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 mb-4">Inventory Summary</h2>
          <dl className="space-y-3">
            {[
              { label: 'Total batches', value: stats.total_batches },
              { label: 'Active batches', value: stats.active_batches },
              { label: 'Expiring soon', value: stats.expiring_soon_batches },
              { label: 'Expired (with stock)', value: stats.expired_batches },
              { label: 'Depleted', value: stats.depleted_items },
              { label: 'Stock value (approx.)', value: formatCurrency(stats.total_usable_stock_value) },
            ].map((item) => (
              <div key={item.label} className="flex justify-between items-center py-1 border-b border-slate-100 last:border-0">
                <dt className="text-sm text-slate-600">{item.label}</dt>
                <dd className="text-sm font-semibold text-slate-900">{item.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      {/* Recent movements */}
      <div className="card">
        <div className="px-5 py-4 border-b border-slate-100">
          <h2 className="font-semibold text-slate-900">Recent Movements</h2>
        </div>
        {d.recent_movements.length === 0 ? (
          <div className="text-center py-10 text-slate-400 text-sm">No movements yet</div>
        ) : (
          <div className="table-container rounded-none border-0">
            <table className="table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Type</th>
                  <th>Quantity</th>
                  <th>By</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {d.recent_movements.map((m) => (
                  <tr key={m.id}>
                    <td className="font-medium text-slate-800">{m.medicine.generic_name}</td>
                    <td>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${
                        m.movement_type === 'received' ? 'bg-green-100 text-green-700' :
                        m.movement_type === 'sold' || m.movement_type === 'dispensed' ? 'bg-blue-100 text-blue-700' :
                        m.movement_type === 'expired_removal' ? 'bg-red-100 text-red-700' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        {m.movement_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className={m.quantity > 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                      {m.quantity > 0 ? '+' : ''}{m.quantity}
                    </td>
                    <td className="text-slate-500">{m.performed_by?.full_name ?? '—'}</td>
                    <td className="text-slate-400 text-xs">{formatRelativeTime(m.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
