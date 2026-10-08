import { AlertTriangle } from 'lucide-react'

export default function ErrorState({ title = 'Something went wrong', message = 'An unexpected error occurred.', onRetry }) {
  return (
    <div className="text-center py-12">
      <AlertTriangle className="h-12 w-12 text-red-400 mx-auto" />
      <h3 className="mt-3 text-sm font-medium text-slate-900">{title}</h3>
      <p className="mt-1 text-sm text-slate-500">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100"
        >
          Try Again
        </button>
      )}
    </div>
  )
}
