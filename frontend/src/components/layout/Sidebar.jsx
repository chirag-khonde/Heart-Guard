import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  Heart, LayoutDashboard, ClipboardPlus, History, Bell, Lightbulb,
  BarChart3, Activity, FileText, LogOut, Menu, X, Shield, ChevronRight
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/assessment', icon: ClipboardPlus, label: 'Assessment' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/recommendations', icon: Lightbulb, label: 'Recommendations' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/lifestyle', icon: Activity, label: 'Lifestyle' },
  { to: '/reports', icon: FileText, label: 'Reports' },
]

export default function Sidebar() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const content = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-200">
        <div className="p-2 bg-red-600 rounded-lg">
          <Heart className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">HeartGuard</h1>
          <p className="text-xs text-slate-500">Patient Portal</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-red-50 text-red-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-slate-600">{user?.name?.[0] || 'U'}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 rounded-lg"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile */}
      <div className="lg:hidden">
        <button onClick={() => setOpen(true)} className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md">
          <Menu className="h-5 w-5 text-slate-600" />
        </button>
        {open && (
          <>
            <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setOpen(false)} />
            <div className="fixed inset-y-0 left-0 w-72 bg-white z-50 shadow-xl">
              <button onClick={() => setOpen(false)} className="absolute top-4 right-4 p-1">
                <X className="h-5 w-5 text-slate-400" />
              </button>
              {content}
            </div>
          </>
        )}
      </div>

      {/* Desktop */}
      <div className="hidden lg:block w-64 bg-white border-r border-slate-200 h-screen fixed left-0 top-0">
        {content}
      </div>
    </>
  )
}
