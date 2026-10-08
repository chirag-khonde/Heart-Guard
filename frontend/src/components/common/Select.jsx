import { ChevronDown } from 'lucide-react'

export default function Select({ label, error, options = [], placeholder, className = '', ...props }) {
  return (
    <div className={`space-y-1 ${className}`}>
      {label && <label className="block text-sm font-medium text-slate-700">{label}</label>}
      <div className="relative">
        <select
          className={`block w-full appearance-none rounded-lg border px-3 py-2 pr-8 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0 ${
            error
              ? 'border-red-300 text-red-900 focus:ring-red-500'
              : 'border-slate-300 text-slate-900 focus:ring-red-500 focus:border-red-500'
          }`}
          {...props}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  )
}
