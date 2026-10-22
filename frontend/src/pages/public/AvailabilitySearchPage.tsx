import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, MapPin, Phone, Clock, AlertCircle, Loader2, Pill } from 'lucide-react'
import { useForm } from 'react-hook-form'
import inventoryService from '@/api/inventory'
import { formatRelativeTime, cn } from '@/utils'
import type { AvailabilityResult } from '@/types'

interface SearchForm {
  medicine: string
  city: string
  region: string
}

function ResultCard({ result }: { result: AvailabilityResult }) {
  return (
    <div className={cn('card p-5 transition-all', result.is_stale && 'border-amber-200 bg-amber-50/30')}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-slate-900">{result.pharmacy.name}</h3>
            {result.is_stale && (
              <span className="inline-flex items-center gap-1 text-xs font-medium bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                <AlertCircle className="h-3 w-3" /> Stock info may be outdated
              </span>
            )}
            {result.medicine.requires_prescription && (
              <span className="text-xs font-medium bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                Prescription required
              </span>
            )}
          </div>

          <div className="mt-1 flex items-center gap-1 text-sm text-slate-500">
            <MapPin className="h-3.5 w-3.5 flex-shrink-0" />
            <span>{result.pharmacy.address}, {result.pharmacy.city}</span>
          </div>

          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600">
            <span className="flex items-center gap-1">
              <Phone className="h-3.5 w-3.5 text-slate-400" />
              <a href={`tel:${result.pharmacy.phone}`} className="hover:text-brand-600">{result.pharmacy.phone}</a>
            </span>
            {result.last_confirmed_at && (
              <span className="flex items-center gap-1 text-slate-400">
                <Clock className="h-3.5 w-3.5" />
                Last confirmed {formatRelativeTime(result.last_confirmed_at)}
              </span>
            )}
          </div>

          <div className="mt-3 text-sm text-slate-600">
            <span className="font-medium text-slate-800">{result.medicine.generic_name}</span>
            {result.medicine.brand_name && <span className="text-slate-400"> ({result.medicine.brand_name})</span>}
            <span className="mx-1 text-slate-300">·</span>
            <span>{result.medicine.strength}</span>
            <span className="mx-1 text-slate-300">·</span>
            <span className="capitalize">{result.medicine.dosage_form}</span>
          </div>
        </div>

        <div className="text-right flex-shrink-0">
          <div className={cn(
            'text-2xl font-bold',
            result.usable_quantity > 50 ? 'text-green-600' :
            result.usable_quantity > 10 ? 'text-amber-600' : 'text-red-500'
          )}>
            {result.usable_quantity}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">units available</div>
        </div>
      </div>
    </div>
  )
}

export function AvailabilitySearchPage() {
  const [searchParams, setSearchParams] = useState<{ medicine: string; city?: string; region?: string } | null>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<SearchForm>()

  const { data, isLoading, error } = useQuery({
    queryKey: ['availability', searchParams],
    queryFn: () => inventoryService.searchAvailability(searchParams!),
    enabled: !!searchParams?.medicine,
    select: (r) => r.data,
  })

  const onSubmit = (values: SearchForm) => {
    setSearchParams({
      medicine: values.medicine.trim(),
      city: values.city || undefined,
      region: values.region || undefined,
    })
  }

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Find Medicine Availability</h1>
        <p className="mt-2 text-slate-500">
          Search for medicines at participating pharmacies. Availability is reported by pharmacies and may not reflect real-time stock.
        </p>
      </div>

      {/* Search form */}
      <form onSubmit={handleSubmit(onSubmit)} className="card p-5 mb-8">
        <div className="grid sm:grid-cols-3 gap-4">
          <div className="sm:col-span-3 md:col-span-1">
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Medicine name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              className="input"
              placeholder="e.g. Amoxicillin"
              {...register('medicine', { required: 'Enter a medicine name' })}
            />
            {errors.medicine && <p className="mt-1 text-xs text-red-600">{errors.medicine.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">City</label>
            <input type="text" className="input" placeholder="Addis Ababa" {...register('city')} />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Region</label>
            <input type="text" className="input" placeholder="Addis Ababa" {...register('region')} />
          </div>
        </div>
        <button type="submit" className="btn-primary mt-4 gap-2">
          <Search className="h-4 w-4" />
          Search
        </button>
      </form>

      {/* Results */}
      {isLoading && (
        <div className="flex items-center justify-center py-20 text-brand-600">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span className="text-slate-500">Searching pharmacies…</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
          <p className="font-medium">Search failed</p>
          <p className="text-sm mt-1">Please try again or refine your search terms.</p>
        </div>
      )}

      {data && !isLoading && (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-slate-600">
              {data.results.length > 0
                ? <><span className="font-semibold text-slate-900">{data.results.length}</span> {data.results.length === 1 ? 'result' : 'results'} for &ldquo;{data.query}&rdquo;</>
                : <>No results for &ldquo;{data.query}&rdquo;</>}
            </p>
          </div>

          {data.results.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <Pill className="h-10 w-10 mx-auto mb-3 opacity-40" />
              <p className="font-medium text-slate-600">No pharmacies found with available stock</p>
              <p className="text-sm mt-1">Try a different medicine name or remove location filters.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {data.results.map((result, i) => (
                <ResultCard key={i} result={result} />
              ))}
            </div>
          )}
        </>
      )}

      {!searchParams && !isLoading && (
        <div className="text-center py-20 text-slate-400">
          <Search className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p className="font-medium text-slate-600">Enter a medicine name to start searching</p>
        </div>
      )}
    </div>
  )
}
