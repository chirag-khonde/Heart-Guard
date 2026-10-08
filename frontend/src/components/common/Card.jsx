export default function Card({ children, className = '', header, actions }) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-200 ${className}`}>
      {(header || actions) && (
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          {header && <h3 className="text-lg font-semibold text-slate-900">{header}</h3>}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  )
}
