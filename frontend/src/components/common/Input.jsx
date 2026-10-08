export default function Input({ label, error, helperText, className = '', ...props }) {
  return (
    <div className={`space-y-1 ${className}`}>
      {label && <label className="block text-sm font-medium text-slate-700">{label}</label>}
      <input
        className={`block w-full rounded-lg border px-3 py-2 text-sm transition-colors placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-offset-0 ${
          error
            ? 'border-red-300 text-red-900 focus:ring-red-500 focus:border-red-500'
            : 'border-slate-300 text-slate-900 focus:ring-red-500 focus:border-red-500'
        }`}
        {...props}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      {helperText && !error && <p className="text-sm text-slate-500">{helperText}</p>}
    </div>
  )
}
