import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export default function RoleRoute({ allowedRoles = [] }) {
  const { user, hasRole } = useAuth()

  if (!hasRole(allowedRoles)) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
