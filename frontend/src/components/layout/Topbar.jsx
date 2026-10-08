import { useAuth } from '../../context/AuthContext'
import { Bell, LogOut, User } from 'lucide-react'

export default function Topbar() {
  const { user, logout } = useAuth()

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-end px-6 sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <button className="relative p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full" />
        </button>
        <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
          <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
            <User className="h-4 w-4 text-red-600" />
          </div>
          <span className="text-sm font-medium text-slate-700 hidden sm:block">{user?.name}</span>
        </div>
        <button
          onClick={logout}
          className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50"
          title="Sign Out"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}
