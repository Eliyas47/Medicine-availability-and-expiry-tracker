import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/features/auth/AuthContext'
import authService from '@/api/auth'
import { getApiErrorMessage } from '@/utils'
import { Loader2, User, Lock } from 'lucide-react'
import toast from 'react-hot-toast'
import { useState } from 'react'

const profileSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  phone: z.string().optional(),
})

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Required'),
  new_password: z.string().min(8, 'At least 8 characters')
    .regex(/[A-Za-z]/, 'Must contain a letter')
    .regex(/\d/, 'Must contain a number'),
  new_password_confirm: z.string(),
}).refine(d => d.new_password === d.new_password_confirm, {
  message: "Passwords don't match",
  path: ['new_password_confirm'],
})

type ProfileForm = z.infer<typeof profileSchema>
type PasswordForm = z.infer<typeof passwordSchema>

export function UserProfilePage() {
  const { user, refreshUser } = useAuth()
  const [section, setSection] = useState<'profile' | 'password'>('profile')

  const { register: rProfile, handleSubmit: hsProfile, formState: { errors: eProfile } } =
    useForm<ProfileForm>({
      resolver: zodResolver(profileSchema),
      defaultValues: { full_name: user?.full_name ?? '', phone: user?.phone ?? '' },
    })

  const { register: rPwd, handleSubmit: hsPwd, reset: resetPwd, formState: { errors: ePwd } } =
    useForm<PasswordForm>({ resolver: zodResolver(passwordSchema) })

  const profileMutation = useMutation({
    mutationFn: (d: ProfileForm) => authService.updateProfile(d),
    onSuccess: async () => { await refreshUser(); toast.success('Profile updated') },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  })

  const passwordMutation = useMutation({
    mutationFn: (d: PasswordForm) => authService.changePassword(d),
    onSuccess: () => { resetPwd(); toast.success('Password changed — please sign in again') },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  })

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">My Profile</h1>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 mb-6">
        {(['profile', 'password'] as const).map((s) => (
          <button key={s} onClick={() => setSection(s)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px capitalize flex items-center gap-2 ${
              section === s ? 'border-brand-600 text-brand-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}>
            {s === 'profile' ? <User className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
            {s === 'profile' ? 'Profile Details' : 'Change Password'}
          </button>
        ))}
      </div>

      {section === 'profile' && (
        <div className="card p-6">
          <div className="mb-4 text-sm text-slate-500 bg-slate-50 rounded-lg px-4 py-3">
            <span className="font-medium">Role:</span> {user?.role?.replace('_', ' ')} ·{' '}
            <span className="font-medium">Email:</span> {user?.email} (cannot be changed)
          </div>
          <form onSubmit={hsProfile((d) => profileMutation.mutate(d))} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Full Name *</label>
              <input type="text" className="input" {...rProfile('full_name')} />
              {eProfile.full_name && <p className="mt-1 text-xs text-red-600">{eProfile.full_name.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Phone</label>
              <input type="tel" className="input" placeholder="+251911000000" {...rProfile('phone')} />
            </div>
            <button type="submit" disabled={profileMutation.isPending} className="btn-primary gap-2">
              {profileMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Saving…</> : 'Save Changes'}
            </button>
          </form>
        </div>
      )}

      {section === 'password' && (
        <div className="card p-6">
          <form onSubmit={hsPwd((d) => passwordMutation.mutate(d))} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Current Password *</label>
              <input type="password" className="input" {...rPwd('current_password')} />
              {ePwd.current_password && <p className="mt-1 text-xs text-red-600">{ePwd.current_password.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">New Password *</label>
              <input type="password" className="input" {...rPwd('new_password')} />
              {ePwd.new_password && <p className="mt-1 text-xs text-red-600">{ePwd.new_password.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Confirm New Password *</label>
              <input type="password" className="input" {...rPwd('new_password_confirm')} />
              {ePwd.new_password_confirm && <p className="mt-1 text-xs text-red-600">{ePwd.new_password_confirm.message}</p>}
            </div>
            <button type="submit" disabled={passwordMutation.isPending} className="btn-primary gap-2">
              {passwordMutation.isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Changing…</> : 'Change Password'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
