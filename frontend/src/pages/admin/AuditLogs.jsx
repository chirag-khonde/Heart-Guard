import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Loading from '../../components/common/Loading'
import PageHeader from '../../components/common/PageHeader'
import Select from '../../components/common/Select'
import { FileText } from 'lucide-react'

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ action: '', user_id: '' })

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.admin.getAuditLogs(filter)
        setLogs(res.data.items || res.data || [])
      } catch {
        setLogs([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [filter])

  if (loading) return <Loading text="Loading audit logs..." />

  return (
    <div className="space-y-6">
      <PageHeader title="Audit Logs" description="System audit trail and activity logs" />

      <div className="flex items-center gap-4">
        <Select
          label="Action"
          value={filter.action}
          onChange={(e) => setFilter({ ...filter, action: e.target.value })}
          options={[
            { value: '', label: 'All Actions' },
            { value: 'login', label: 'Login' },
            { value: 'assessment', label: 'Assessment' },
            { value: 'review', label: 'Review' },
            { value: 'create', label: 'Create' },
          ]}
        />
      </div>

      <Card padding="p-0">
        {logs.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">No audit logs found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Timestamp</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">User</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Action</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Resource</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Status</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {logs.map((log, i) => (
                  <tr key={log.id || i} className="hover:bg-slate-50">
                    <td className="px-6 py-4 text-slate-500">{new Date(log.timestamp || log.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4 font-medium text-slate-900">{log.user_email || log.user || 'System'}</td>
                    <td className="px-6 py-4">
                      <Badge variant={log.action === 'login' ? 'info' : log.action === 'assessment' ? 'success' : 'info'}>
                        {log.action}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-slate-600">{log.resource || log.resource_type || '-'}</td>
                    <td className="px-6 py-4">
                      <Badge variant={log.status === 'success' ? 'success' : log.status === 'failure' ? 'danger' : 'info'}>
                        {log.status || 'success'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-slate-500 font-mono text-xs">{log.ip_address || '-'}</td>
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
