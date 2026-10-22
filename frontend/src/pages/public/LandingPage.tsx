import { Link } from 'react-router-dom'
import { Search, Package, AlertTriangle, Bell, FileText, Shield, ArrowRight, CheckCircle } from 'lucide-react'

const features = [
  {
    icon: Package,
    title: 'Batch Inventory Tracking',
    desc: 'Manage medicine batches with quantities, expiry dates, and supplier details at the pharmacy level.',
  },
  {
    icon: AlertTriangle,
    title: 'Expiry Management',
    desc: 'Get ahead of expiring stock with configurable warning windows. Expired batches are never shown as available.',
  },
  {
    icon: Bell,
    title: 'Low-Stock Alerts',
    desc: 'Set minimum thresholds per medicine and get notified before you run out of critical stock.',
  },
  {
    icon: Search,
    title: 'Availability Search',
    desc: 'Patients and healthcare workers can search for medicines at participating pharmacies near them.',
  },
  {
    icon: FileText,
    title: 'Reports & Export',
    desc: 'Generate stock summaries, expiry reports, and movement histories. Export to CSV for offline use.',
  },
  {
    icon: Shield,
    title: 'Role-Based Access',
    desc: 'System admins, pharmacy admins, and inventory staff each have appropriate access levels.',
  },
]

const steps = [
  { step: '01', title: 'Register your pharmacy', desc: 'Create an account and set up your pharmacy profile with location and contact details.' },
  { step: '02', title: 'Add your inventory', desc: 'Add medicine batches with quantities and expiry dates. Stock movements are tracked automatically.' },
  { step: '03', title: 'Monitor and manage', desc: 'Use the dashboard to track expiring stock, low inventory, and availability across all your medicines.' },
]

export function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-600 to-brand-800 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
          <div className="max-w-3xl">
            <span className="inline-block text-brand-200 text-sm font-medium tracking-wide uppercase mb-4">
              For Ethiopian Pharmacies
            </span>
            <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-6">
              Medicine Inventory &amp; Availability Tracking
            </h1>
            <p className="text-xl text-brand-100 mb-8 leading-relaxed">
              A centralized platform for pharmacies to manage stock, track expiry dates,
              and share medicine availability with the public — reducing waste and improving access.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/search" className="inline-flex items-center gap-2 bg-white text-brand-700 font-semibold px-6 py-3 rounded-lg hover:bg-brand-50 transition-colors">
                <Search className="h-5 w-5" />
                Search Medicine Availability
              </Link>
              <Link to="/auth/register" className="inline-flex items-center gap-2 border border-white/40 text-white font-semibold px-6 py-3 rounded-lg hover:bg-white/10 transition-colors">
                Register Your Pharmacy
                <ArrowRight className="h-5 w-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-slate-900">Everything your pharmacy needs</h2>
            <p className="mt-3 text-lg text-slate-500 max-w-2xl mx-auto">
              Built for the realities of pharmacy operations in Ethiopia — simple, reliable, and offline-ready.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((f) => (
              <div key={f.title} className="p-6 rounded-xl border border-slate-200 hover:border-brand-300 hover:shadow-sm transition-all">
                <div className="w-10 h-10 rounded-lg bg-brand-100 flex items-center justify-center mb-4">
                  <f.icon className="h-5 w-5 text-brand-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">{f.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-slate-900">Get started in minutes</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((s) => (
              <div key={s.step} className="relative">
                <div className="text-5xl font-bold text-brand-100 mb-4">{s.step}</div>
                <h3 className="font-semibold text-slate-900 mb-2">{s.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why trust section */}
      <section className="py-16 bg-brand-600 text-white">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-10 items-center">
            <div>
              <h2 className="text-2xl font-bold mb-4">Accuracy you can rely on</h2>
              <ul className="space-y-3">
                {[
                  'Expired medicines never shown as available stock',
                  'Concurrent stock updates protected by database locks',
                  'All changes recorded in an auditable movement history',
                  'Stale availability data is clearly flagged to the public',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3 text-brand-100">
                    <CheckCircle className="h-5 w-5 text-brand-300 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="text-center md:text-right">
              <p className="text-brand-200 text-sm mb-4">Ready to modernize your pharmacy operations?</p>
              <Link to="/auth/register" className="inline-flex items-center gap-2 bg-white text-brand-700 font-semibold px-6 py-3 rounded-lg hover:bg-brand-50 transition-colors">
                Get started free
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
