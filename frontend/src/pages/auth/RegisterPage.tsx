import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { Pill, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useState } from 'react'
import authService from '@/api/auth'
import { getApiErrorMessage, getApiFieldErrors } from '@/utils'

const schema = z.object({
  full_name: z.string().min(2, 'Full name must be at least 2 characters'),
  email: z.string().email('Enter a valid email address'),
  phone: z.string().optional(),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Za-z]/, 'Password must contain at least one letter')
    .regex(/\d/, 'Password must contain at least one number'),
  password_confirm: z.string(),
}).refine((d) => d.password === d.password_confirm, {
  message: "Passwords don't match",
  path: ['password_confirm'],
})

type FormValues = z.infer<typeof schema>

export function RegisterPage() {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, setError, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormValues) => {
    setIsLoading(true)
    try {
      await authService.register(data)
      toast.success('Registration successful! You can now sign in.')
      navigate('/auth/login')
    } catch (err) {
      const fieldErrors = getApiFieldErrors(err)
      if (Object.keys(fieldErrors).length > 0) {
        Object.entries(fieldErrors).forEach(([field, msgs]) => {
          setError(field as keyof FormValues, { message: msgs[0] })
        })
      } else {
        toast.error(getApiErrorMessage(err))
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-600 mb-4">
            <Pill className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-semibold text-slate-900">Create account</h1>
          <p className="mt-1 text-sm text-slate-500">Join Medicine Tracker</p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-slate-700 mb-1">
                Full name <span className="text-red-500">*</span>
              </label>
              <input id="full_name" type="text" className="input" placeholder="Abebe Kebede" {...register('full_name')} />
              {errors.full_name && <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>}
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
                Email address <span className="text-red-500">*</span>
              </label>
              <input id="email" type="email" className="input" placeholder="you@pharmacy.et" {...register('email')} />
              {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-slate-700 mb-1">
                Phone number
              </label>
              <input id="phone" type="tel" className="input" placeholder="+251911000000" {...register('phone')} />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1">
                Password <span className="text-red-500">*</span>
              </label>
              <input id="password" type="password" className="input" placeholder="Min. 8 characters" {...register('password')} />
              {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
            </div>

            <div>
              <label htmlFor="password_confirm" className="block text-sm font-medium text-slate-700 mb-1">
                Confirm password <span className="text-red-500">*</span>
              </label>
              <input id="password_confirm" type="password" className="input" placeholder="Repeat password" {...register('password_confirm')} />
              {errors.password_confirm && <p className="mt-1 text-xs text-red-600">{errors.password_confirm.message}</p>}
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary w-full mt-2">
              {isLoading ? <><Loader2 className="h-4 w-4 animate-spin" /> Creating account…</> : 'Create account'}
            </button>
          </form>
        </div>

        <p className="mt-4 text-center text-sm text-slate-600">
          Already have an account?{' '}
          <Link to="/auth/login" className="text-brand-600 font-medium hover:text-brand-700">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
