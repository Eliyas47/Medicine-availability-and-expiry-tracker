import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import inventoryService from '@/api/inventory'
import medicineService from '@/api/medicines'
import { getApiErrorMessage, getApiFieldErrors } from '@/utils'

const schema = z.object({
  medicine_id: z.string().uuid('Select a medicine'),
  batch_number: z.string().min(1, 'Batch number is required'),
  quantity: z.coerce.number().int().positive('Quantity must be a positive integer'),
  received_date: z.string().min(1, 'Received date is required'),
  expiry_date: z.string().min(1, 'Expiry date is required'),
  supplier: z.string().optional(),
  unit_cost: z.string().optional(),
  notes: z.string().optional(),
}).refine(
  (d) => new Date(d.expiry_date) > new Date(),
  { message: 'Expiry date must be in the future', path: ['expiry_date'] }
)

type FormValues = z.infer<typeof schema>

export function BatchFormPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const today = new Date().toISOString().split('T')[0]

  const { data: medicinesRes } = useQuery({
    queryKey: ['medicines-dropdown'],
    queryFn: () => medicineService.list({ page_size: 200 }),
    select: (r) => r.data.results,
  })

  const { register, handleSubmit, setError, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { received_date: today },
  })

  const mutation = useMutation({
    mutationFn: (data: FormValues) => inventoryService.createBatch({
      medicine: data.medicine_id,
      batch_number: data.batch_number,
      quantity: data.quantity,
      received_date: data.received_date,
      expiry_date: data.expiry_date,
      supplier: data.supplier,
      unit_cost: data.unit_cost,
      notes: data.notes,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Batch added successfully')
      navigate('/dashboard/batches')
    },
    onError: (err) => {
      const fieldErrors = getApiFieldErrors(err)
      if (Object.keys(fieldErrors).length > 0) {
        Object.entries(fieldErrors).forEach(([field, msgs]) => {
          setError(field as keyof FormValues, { message: msgs[0] })
        })
      } else {
        toast.error(getApiErrorMessage(err))
      }
    },
  })

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Add New Batch</h1>
          <p className="text-sm text-slate-500">A received stock movement will be created automatically.</p>
        </div>
      </div>

      <div className="card p-6">
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Medicine <span className="text-red-500">*</span>
            </label>
            <select className="input" {...register('medicine_id')}>
              <option value="">Select a medicine…</option>
              {medicinesRes?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.generic_name} {m.strength} ({m.dosage_form})
                </option>
              ))}
            </select>
            {errors.medicine_id && <p className="mt-1 text-xs text-red-600">{errors.medicine_id.message}</p>}
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Batch Number <span className="text-red-500">*</span>
              </label>
              <input type="text" className="input" placeholder="e.g. AMX-2024-001" {...register('batch_number')} />
              {errors.batch_number && <p className="mt-1 text-xs text-red-600">{errors.batch_number.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Quantity <span className="text-red-500">*</span>
              </label>
              <input type="number" min="1" className="input" placeholder="100" {...register('quantity')} />
              {errors.quantity && <p className="mt-1 text-xs text-red-600">{errors.quantity.message}</p>}
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Received Date <span className="text-red-500">*</span>
              </label>
              <input type="date" className="input" {...register('received_date')} />
              {errors.received_date && <p className="mt-1 text-xs text-red-600">{errors.received_date.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Expiry Date <span className="text-red-500">*</span>
              </label>
              <input type="date" className="input" {...register('expiry_date')} />
              {errors.expiry_date && <p className="mt-1 text-xs text-red-600">{errors.expiry_date.message}</p>}
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Supplier</label>
              <input type="text" className="input" placeholder="Supplier name" {...register('supplier')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Unit Cost (ETB)</label>
              <input type="number" step="0.01" min="0" className="input" placeholder="0.00" {...register('unit_cost')} />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
            <textarea className="input min-h-[80px] resize-y" placeholder="Optional notes…" {...register('notes')} />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary gap-2">
              {mutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Saving…</> : 'Add Batch'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
