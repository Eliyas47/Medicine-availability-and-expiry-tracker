import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, RefreshCw, Filter, CheckCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import inventoryService from '@/api/inventory'
import { formatDateTime, getApiErrorMessage } from '@/utils'
import { useAuth } from '@/features/auth/AuthContext'

const movementSchema = z.object({
  batch: z.string().uuid('Select a batch'),
  movement_type: z.enum(['sold', 'dispensed', 'adjustment', 'received', 'expired_removal', 'correction']),
  quantity: z.coerce.number().int().positive('Quantity must be positive'),
  unit_price: z.string().optional(),
  reference_number: z.string().optional(),
  notes: z.string().optional(),
})

type MovementForm = z.infer<typeof movementSchema>

export function MovementsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [movementType, setMovementTypeFilter] = useState('')
  const [page, setPage] = useState(1)

  const { data: response, isLoading, refetch } = useQuery({
    queryKey: ['movements', { movementType, page }],
    queryFn: () => inventoryService.listMovements({
      movement_type: movementType as never || undefined,
      page,
    }),
    select: (r) => r.data,
  })

  const { data: batchesRes } = useQuery({
    queryKey: ['batches-dropdown'],
    queryFn: () => inventoryService.listBatches({ status: 'active', page_size: 200 }),
    select: (r) => r.data.results,
    enabled: showForm,
  })

  const { register, handleSubmit, reset, formState: { errors } } = useForm<MovementForm>({
    resolver: zodResolver(movementSchema),
    defaultValues: { movement_type: 'sold' },
  })

  const mutation = useMutation({
    mutationFn: (data: MovementForm) => inventoryService.createMovement({
      batch: data.batch,
      movement_type: data.movement_type,
      quantity: data.quantity,
      unit_price: data.unit_price,
      reference_number: data.reference_number,
      notes: data.notes,
    }),
    onSuccess: (r) => {
      queryClient.invalidateQueries({ queryKey: ['movements'] })
      queryClient.invalidateQueries({ queryKey: ['batches'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      if (!r.data.is_approved) {
        toast.success('Movement recorded — pending admin approval')
      } else {
        toast.success('Movement recorded successfully')
      }
      reset()
      setShowForm(false)
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  })

  const approveMutation = useMutation({
    mutationFn: (id: string) => inventoryService.approveMovement(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['movements'] })
      toast.success('Movement approved')
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  })

  const canApprove = user?.role === 'pharmacy_admin' || user?.role === 'system_admin'

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Stock Movements</h1>
          <p className="text-sm text-slate-500 mt-0.5">Auditable history of all stock changes</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary gap-2">
          <Plus className="h-4 w-4" /> Record Movement
        </button>
      </div>

      {/* Movement form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center p-4">
          <div className="card p-6 w-full max-w-lg">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Record Stock Movement</h2>
            <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Batch *</label>
                <select className="input" {...register('batch')}>
                  <option value="">Select a batch…</option>
                  {batchesRes?.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.medicine.generic_name} — {b.batch_number} (qty: {b.quantity})
                    </option>
                  ))}
                </select>
                {errors.batch && <p className="mt-1 text-xs text-red-600">{errors.batch.message}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Type *</label>
                  <select className="input" {...register('movement_type')}>
                    <option value="sold">Sold</option>
                    <option value="dispensed">Dispensed</option>
                    <option value="received">Received</option>
                    <option value="adjustment">Adjustment</option>
                    <option value="expired_removal">Expired Removal</option>
                    <option value="correction">Correction (needs approval)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Quantity *</label>
                  <input type="number" min="1" className="input" {...register('quantity')} />
                  {errors.quantity && <p className="mt-1 text-xs text-red-600">{errors.quantity.message}</p>}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Unit Price (ETB)</label>
                  <input type="number" step="0.01" className="input" placeholder="0.00" {...register('unit_price')} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Reference #</label>
                  <input type="text" className="input" placeholder="RX-001" {...register('reference_number')} />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
                <textarea className="input resize-none h-16" {...register('notes')} />
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={mutation.isPending} className="btn-primary gap-2">
                  {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Saving…</> : 'Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card p-4 flex gap-3">
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <select className="input pl-9 appearance-none" value={movementType}
            onChange={(e) => { setMovementTypeFilter(e.target.value); setPage(1) }}>
            <option value="">All types</option>
            {['received', 'sold', 'dispensed', 'adjustment', 'expired_removal', 'correction'].map((t) => (
              <option key={t} value={t}>{t.replace('_', ' ')}</option>
            ))}
          </select>
        </div>
        <button onClick={() => refetch()} className="btn-ghost gap-2 text-sm">
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Table */}
      <div className="table-container">
        {isLoading ? (
          <div className="flex items-center justify-center h-48"><div className="spinner h-8 w-8" /></div>
        ) : !response?.results.length ? (
          <div className="text-center py-16 text-slate-400 text-sm">No movements found</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Medicine</th>
                <th>Batch</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Reference</th>
                <th>By</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {response.results.map((m) => (
                <tr key={m.id}>
                  <td className="text-xs text-slate-400 whitespace-nowrap">{formatDateTime(m.created_at)}</td>
                  <td className="font-medium text-slate-800">{m.medicine.generic_name}</td>
                  <td className="text-xs font-mono text-slate-500">{m.batch?.batch_number ?? '—'}</td>
                  <td>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${
                      m.movement_type === 'received' ? 'bg-green-100 text-green-700' :
                      ['sold', 'dispensed'].includes(m.movement_type) ? 'bg-blue-100 text-blue-700' :
                      m.movement_type === 'expired_removal' ? 'bg-red-100 text-red-700' :
                      m.movement_type === 'correction' ? 'bg-purple-100 text-purple-700' :
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {m.movement_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td className={`font-semibold ${m.quantity > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {m.quantity > 0 ? '+' : ''}{m.quantity}
                  </td>
                  <td className="text-slate-500 text-sm">{m.reference_number || '—'}</td>
                  <td className="text-slate-500 text-sm">{m.performed_by?.full_name ?? '—'}</td>
                  <td>
                    {m.is_approved ? (
                      <span className="text-xs text-green-600 flex items-center gap-1">
                        <CheckCircle className="h-3.5 w-3.5" /> Approved
                      </span>
                    ) : canApprove ? (
                      <button
                        onClick={() => approveMutation.mutate(m.id)}
                        disabled={approveMutation.isPending}
                        className="text-xs btn-primary px-2 py-1"
                      >
                        Approve
                      </button>
                    ) : (
                      <span className="text-xs text-amber-600">Pending</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {response && response.total_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-600">
          <span>Page {response.current_page} of {response.total_pages}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!response.previous} className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40">Previous</button>
            <button onClick={() => setPage(p => p + 1)} disabled={!response.next} className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  )
}
