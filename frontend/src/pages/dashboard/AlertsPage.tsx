import { useQuery } from '@tanstack/react-query'
import { Bell, TrendingDown, RefreshCw } from 'lucide-react'
import inventoryService from '@/api/inventory'

export function AlertsPage() {
  const { data: response, isLoading, refetch } = useQuery({
    queryKey: ['low-stock'],
    queryFn: () => inventoryService.getLowStockBatches({ page_size: 100 }),
    select: (r) => r.data,
  })

  const items = (response as unknown as { count: number; results: Array<{
    medicine_name: string; pharmacy_name: string; usable_quantity: number;
    minimum_threshold: number; shortfall: number;
  }> })?.results ?? []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Low-Stock Alerts</h1>
          <p className="text-sm text-slate-500 mt-0.5">Medicines below their minimum stock threshold</p>
        </div>
        <button onClick={() => refetch()} className="btn-ghost gap-2 text-sm">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48"><div className="spinner h-8 w-8" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <Bell className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p className="font-medium text-slate-600">All stock levels are healthy</p>
          <p className="text-sm mt-1">No medicines are below their minimum threshold.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Pharmacy</th>
                <th>Current Stock</th>
                <th>Minimum Threshold</th>
                <th>Shortfall</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => {
                const ratio = item.usable_quantity / (item.minimum_threshold || 1)
                const severity = ratio === 0 ? 'critical' : ratio < 0.5 ? 'high' : 'medium'
                return (
                  <tr key={i}>
                    <td className="font-medium text-slate-800">{item.medicine_name}</td>
                    <td className="text-slate-500 text-sm">{item.pharmacy_name}</td>
                    <td className={`font-semibold ${item.usable_quantity === 0 ? 'text-red-600' : 'text-orange-600'}`}>
                      {item.usable_quantity}
                    </td>
                    <td className="text-slate-600">{item.minimum_threshold}</td>
                    <td className="text-red-600 font-semibold">-{item.shortfall}</td>
                    <td>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        severity === 'critical' ? 'bg-red-100 text-red-700' :
                        severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        'bg-amber-100 text-amber-700'
                      }`}>
                        {severity}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
