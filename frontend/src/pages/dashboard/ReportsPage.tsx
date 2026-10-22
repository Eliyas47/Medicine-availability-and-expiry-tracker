import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, RefreshCw, FileText } from 'lucide-react'
import reportService from '@/api/reports'
import { formatDate, cn } from '@/utils'

type ReportType = 'stock-summary' | 'expiring' | 'expired' | 'movements' | 'low-stock'

const REPORT_TABS: { id: ReportType; label: string }[] = [
  { id: 'stock-summary', label: 'Stock Summary' },
  { id: 'expiring', label: 'Expiring Stock' },
  { id: 'expired', label: 'Expired Stock' },
  { id: 'movements', label: 'Movements' },
  { id: 'low-stock', label: 'Low Stock' },
]

export function ReportsPage() {
  const [activeReport, setActiveReport] = useState<ReportType>('stock-summary')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const params = {
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    page_size: 100,
  }

  const fetchers: Record<ReportType, () => ReturnType<typeof reportService.stockSummary>> = {
    'stock-summary': () => reportService.stockSummary(params),
    'expiring': () => reportService.expiring(params),
    'expired': () => reportService.expired(params),
    'movements': () => reportService.movements(params),
    'low-stock': () => reportService.lowStock(params),
  }

  const { data: response, isLoading, refetch } = useQuery({
    queryKey: ['report', activeReport, dateFrom, dateTo],
    queryFn: () => fetchers[activeReport](),
    select: (r) => r.data as { count: number; results: Record<string, unknown>[] },
  })

  const handleCsvExport = async () => {
    try {
      const res = await fetchers[activeReport]()
      // For CSV export — the API returns blob when ?format=csv
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${activeReport}_${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      /* handled silently */
    }
  }

  const columns = response?.results[0] ? Object.keys(response.results[0]) : []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Reports</h1>
          <p className="text-sm text-slate-500 mt-0.5">Generate and export inventory reports</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => refetch()} className="btn-ghost gap-2 text-sm">
            <RefreshCw className="h-4 w-4" />
          </button>
          <button onClick={handleCsvExport} className="btn-secondary gap-2 text-sm">
            <Download className="h-4 w-4" /> Export
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap border-b border-slate-200 gap-0">
        {REPORT_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveReport(tab.id)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeReport === tab.id
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Date filters */}
      <div className="flex gap-4 items-end">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">From</label>
          <input type="date" className="input text-sm" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">To</label>
          <input type="date" className="input text-sm" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
        {(dateFrom || dateTo) && (
          <button className="btn-ghost text-sm" onClick={() => { setDateFrom(''); setDateTo('') }}>
            Clear dates
          </button>
        )}
      </div>

      {/* Report table */}
      <div className="table-container">
        {isLoading ? (
          <div className="flex items-center justify-center h-48"><div className="spinner h-8 w-8" /></div>
        ) : !response?.results.length ? (
          <div className="text-center py-16 text-slate-400">
            <FileText className="h-8 w-8 mx-auto mb-3 opacity-40" />
            <p className="font-medium text-slate-600">No data for this report</p>
            <p className="text-sm mt-1">Try adjusting the date range or checking your inventory.</p>
          </div>
        ) : (
          <>
            <div className="px-4 py-2 bg-slate-50 border-b border-slate-200 text-xs text-slate-500">
              {response.count} row{response.count !== 1 ? 's' : ''}
            </div>
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th key={col} className="capitalize whitespace-nowrap">
                        {col.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {response.results.map((row, i) => (
                    <tr key={i}>
                      {columns.map((col) => (
                        <td key={col} className="text-sm whitespace-nowrap">
                          {String(row[col] ?? '—')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
