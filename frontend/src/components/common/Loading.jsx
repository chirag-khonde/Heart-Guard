import { Loader2 } from 'lucide-react'

export default function Loading({ text = 'Loading...', fullScreen = false }) {
  if (fullScreen) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-red-600 mx-auto" />
          <p className="mt-3 text-sm text-slate-500">{text}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center py-12">
      <div className="text-center">
        <Loader2 className="h-6 w-6 animate-spin text-red-600 mx-auto" />
        <p className="mt-2 text-sm text-slate-500">{text}</p>
      </div>
    </div>
  )
}
