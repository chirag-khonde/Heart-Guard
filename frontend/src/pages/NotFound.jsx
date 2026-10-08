import { Link } from 'react-router-dom'
import { Heart, Home } from 'lucide-react'
import Button from '../components/common/Button'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-2xl mb-6">
          <Heart className="h-8 w-8 text-red-600" />
        </div>
        <h1 className="text-6xl font-extrabold text-slate-900">404</h1>
        <p className="mt-4 text-lg text-slate-600">Page not found</p>
        <p className="mt-2 text-sm text-slate-500">The page you&apos;re looking for doesn&apos;t exist.</p>
        <div className="mt-8">
          <Link to="/">
            <Button>
              <Home className="h-4 w-4" />
              Back to Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
