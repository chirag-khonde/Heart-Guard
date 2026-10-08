import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Loading from '../common/Loading'

export default function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <Loading fullScreen />

  if (!isAuthenticated) return <Navigate to="/login" replace />

  return <Outlet />
}
