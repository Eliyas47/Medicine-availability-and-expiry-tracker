import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, RefreshCw, Search, Filter } from 'lucide-react'
import inventoryService from '@/api/inventory'
import { formatDate, getBatchStatusColor, getBatchStatusLabel, getExpiryColor, cn } from '@/utils'
import type { BatchStatus } from '@/types'

const STATUS_OPTIONS: { value: BatchStatus | ''; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'active', label: 'Active' },
  { value: 'expiring_soon', label: 'Expiring Soon' },
  { value: 'low_stock', label: 'Low Stock' },
  { value: 'expired', label: 'Expired' },
  { value: 'depleted', label: 'Depleted' },
]

export function BatchListPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<BatchStatus | ''>('')
  const [page, setPage] = useState(1)

  const { data: response, isLoading, refetch } = useQuery({
    queryKey: ['batches', { search, status, page }],
    queryFn: () => inventoryService.listBatches({ search, status: status || undefined, page }),
    select: (r) => r.data,
  })

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Inventory Batches</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage medicine batches and stock levels</p>
        </div>
        <Link to="/dashboard/batches/new" className="btn-primary gap-2">
          <Plus className="h-4 w-4" /> Add Batch
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by medicine or batch number…"
            className="input pl-9"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <select
            className="input pl-9 pr-8 appearance-none"
            value={status}
            onChange={(e) => { setStatus(e.target.value as BatchStatus | ''); setPage(1) }}
          >
            {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <button onClick={() => refetch()} className="btn-ghost gap-2 text-sm">
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Table */}
      <div className="table-container">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="spinner h-8 w-8" />
          </div>
        ) : !response || response.results.length === 0 ? (
          <div className="text-center py-16 text-slate-400">
            <p className="font-medium text-slate-600">No batches found</p>
            <p className="text-sm mt-1">
              {search || status ? 'Try clearing your filters.' : 'Add your first batch to get started.'}
            </p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Batch #</th>
                <th>Medicine</th>
                <th>Quantity</th>
                <th>Received</th>
                <th>Expiry</th>
                <th>Days Left</th>
                <th>Status</th>
                <th>Supplier</th>
              </tr>
            </thead>
            <tbody>
              {response.results.map((batch) => (
                <tr key={batch.id}>
                  <td className="font-mono text-xs text-slate-700">{batch.batch_number}</td>
                  <td>
                    <div className="font-medium text-slate-800">{batch.medicine.generic_name}</div>
                    <div className="text-xs text-slate-400">{batch.medicine.strength} · {batch.medicine.dosage_form}</div>
                  </td>
                  <td className="font-semibold text-slate-900">{batch.quantity}</td>
                  <td className="text-slate-500 text-sm">{formatDate(batch.received_date)}</td>
                  <td className="text-slate-500 text-sm">{formatDate(batch.expiry_date)}</td>
                  <td>
                    <span className={cn('text-sm font-medium', getExpiryColor(batch.days_until_expiry))}>
                      {batch.days_until_expiry < 0 ? 'Expired' : `${batch.days_until_expiry}d`}
                    </span>
                  </td>
                  <td>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getBatchStatusColor(batch.status)}`}>
                      {getBatchStatusLabel(batch.status)}
                    </span>
                  </td>
                  <td className="text-slate-500 text-sm">{batch.supplier || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {response && response.total_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-600">
          <span>Showing page {response.current_page} of {response.total_pages} ({response.count} total)</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!response.previous} className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40">
              Previous
            </button>
            <button onClick={() => setPage(p => p + 1)} disabled={!response.next} className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40">
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
