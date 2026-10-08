import { NavLink, Outlet } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import Topbar from './Topbar'
import {
  Heart, LayoutDashboard, BarChart3, Activity, Database, Server,
  FileText, Users, Menu, X, Shield
} from 'lucide-react'

const navItems = [
  { to: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/admin/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/admin/monitoring', icon: Activity, label: 'Model Monitoring' },
  { to: '/admin/data-quality', icon: Database, label: 'Data Quality' },
  { to: '/admin/health', icon: Server, label: 'System Health' },
  { to: '/admin/audit', icon: FileText, label: 'Audit Logs' },
  { to: '/admin/users', icon: Users, label: 'User Management' },
]

function AdminSidebar({ open, onClose }) {
  const { user } = useAuth()

  const content = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-200">
        <div className="p-2 bg-slate-900 rounded-lg">
          <Heart className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">HeartGuard</h1>
          <p className="text-xs text-slate-500">Admin Portal</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/admin'}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50'
              }`
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
            <Shield className="h-4 w-4 text-slate-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500">Administrator</p>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <>
      <div className="lg:hidden">
        {open && (
          <>
            <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
            <div className="fixed inset-y-0 left-0 w-72 bg-white z-50 shadow-xl">
              <button onClick={onClose} className="absolute top-4 right-4 p-1">
                <X className="h-5 w-5 text-slate-400" />
              </button>
              {content}
            </div>
          </>
        )}
      </div>
      <div className="hidden lg:block w-64 bg-white border-r border-slate-200 h-screen fixed left-0 top-0">
        {content}
      </div>
    </>
  )
}

export default function AdminLayout() {
  const [open, setOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50">
      <AdminSidebar open={open} onClose={() => setOpen(false)} />
      <div className="lg:ml-64">
        <div className="lg:hidden fixed top-4 left-4 z-50">
          <button onClick={() => setOpen(true)} className="p-2 bg-white rounded-lg shadow-md">
            <Menu className="h-5 w-5 text-slate-600" />
          </button>
        </div>
        <Topbar />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
