import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, XCircle, RefreshCw } from 'lucide-react'
import inventoryService from '@/api/inventory'
import { formatDate, getExpiryColor, getBatchStatusColor, getBatchStatusLabel, cn } from '@/utils'

type Tab = 'expiring' | 'expired'

export function ExpiryPage() {
  const [tab, setTab] = useState<Tab>('expiring')
  const [page, setPage] = useState(1)

  const { data: expiringRes, isLoading: loadingExpiring } = useQuery({
    queryKey: ['batches-expiring', page],
    queryFn: () => inventoryService.getExpiringBatches({ page }),
    select: (r) => r.data,
    enabled: tab === 'expiring',
  })

  const { data: expiredRes, isLoading: loadingExpired } = useQuery({
    queryKey: ['batches-expired', page],
    queryFn: () => inventoryService.getExpiredBatches({ page }),
    select: (r) => r.data,
    enabled: tab === 'expired',
  })

  const data = tab === 'expiring' ? expiringRes : expiredRes
  const isLoading = tab === 'expiring' ? loadingExpiring : loadingExpired

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Expiry Management</h1>
        <p className="text-sm text-slate-500 mt-0.5">Monitor and remove expired stock from your inventory</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        {(['expiring', 'expired'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setPage(1) }}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize flex items-center gap-2',
              tab === t
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            )}
          >
            {t === 'expiring' ? <AlertTriangle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            {t === 'expiring' ? 'Expiring Soon' : 'Expired'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="table-container">
        {isLoading ? (
          <div className="flex items-center justify-center h-48"><div className="spinner h-8 w-8" /></div>
        ) : !data?.results.length ? (
          <div className="text-center py-16 text-slate-400">
            <p className="font-medium text-slate-600">
              {tab === 'expiring' ? 'No batches expiring soon' : 'No expired batches with remaining stock'}
            </p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Batch #</th>
                <th>Quantity</th>
                <th>Expiry Date</th>
                <th>Days</th>
                <th>Status</th>
                <th>Supplier</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((batch) => (
                <tr key={batch.id}>
                  <td>
                    <div className="font-medium text-slate-800">{batch.medicine.generic_name}</div>
                    <div className="text-xs text-slate-400">{batch.medicine.strength}</div>
                  </td>
                  <td className="font-mono text-xs text-slate-600">{batch.batch_number}</td>
                  <td className="font-semibold text-slate-900">{batch.quantity}</td>
                  <td className="text-sm text-slate-600">{formatDate(batch.expiry_date)}</td>
                  <td>
                    <span className={cn('text-sm font-semibold', getExpiryColor(batch.days_until_expiry))}>
                      {batch.days_until_expiry < 0
                        ? `${Math.abs(batch.days_until_expiry)}d ago`
                        : `${batch.days_until_expiry}d`}
                    </span>
                  </td>
                  <td>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getBatchStatusColor(batch.status)}`}>
                      {getBatchStatusLabel(batch.status)}
                    </span>
                  </td>
                  <td className="text-sm text-slate-500">{batch.supplier || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-600">
          <span>Page {data.current_page} of {data.total_pages}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.previous} className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40">Previous</button>
            <button onClick={() => setPage(p => p + 1)} disabled={!data.next} className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  )
}
