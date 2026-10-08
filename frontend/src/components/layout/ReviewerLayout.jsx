import { NavLink } from 'react-router-dom'
import { Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Topbar from './Topbar'
import {
  Heart, LayoutDashboard, ClipboardCheck, ListTodo, LogOut, Menu, X
} from 'lucide-react'
import { useState } from 'react'

const navItems = [
  { to: '/reviewer', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/reviewer/queue', icon: ClipboardCheck, label: 'Review Queue' },
]

function ReviewerSidebar({ open, onClose }) {
  const { user } = useAuth()

  const content = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-200">
        <div className="p-2 bg-blue-800 rounded-lg">
          <Heart className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">HeartGuard</h1>
          <p className="text-xs text-slate-500">Reviewer Portal</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/reviewer'}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'
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
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-blue-600">{user?.name?.[0] || 'R'}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500">Reviewer</p>
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

export default function ReviewerLayout() {
  const [open, setOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50">
      <ReviewerSidebar open={open} onClose={() => setOpen(false)} />
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
