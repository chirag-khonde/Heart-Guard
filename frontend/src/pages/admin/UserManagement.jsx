import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Loading from '../../components/common/Loading'
import PageHeader from '../../components/common/PageHeader'
import { Users } from 'lucide-react'

export default function UserManagement() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.admin.getUsers()
        setUsers(res.data.items || res.data || [])
      } catch {
        setUsers([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Loading users..." />

  return (
    <div className="space-y-6">
      <PageHeader title="User Management" description="View and manage system users" />

      <Card padding="p-0">
        {users.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">No users found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Name</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Email</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Role</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Status</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-slate-600">{user.name?.[0] || 'U'}</span>
                        </div>
                        <span className="font-medium text-slate-900">{user.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600">{user.email}</td>
                    <td className="px-6 py-4">
                      <Badge variant={user.role === 'admin' ? 'danger' : user.role === 'reviewer' ? 'info' : 'success'}>
                        {user.role}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant={user.is_active !== false ? 'success' : 'danger'}>
                        {user.is_active !== false ? 'Active' : 'Inactive'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
