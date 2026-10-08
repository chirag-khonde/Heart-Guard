import { Inbox } from 'lucide-react'

export default function EmptyState({ icon: Icon = Inbox, title = 'No data', message = 'There is nothing to show here yet.' }) {
  return (
    <div className="text-center py-12">
      <Icon className="h-12 w-12 text-slate-300 mx-auto" />
      <h3 className="mt-3 text-sm font-medium text-slate-900">{title}</h3>
      <p className="mt-1 text-sm text-slate-500">{message}</p>
    </div>
  )
}
