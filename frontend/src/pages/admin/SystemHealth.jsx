import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Loading from '../../components/common/Loading'
import PageHeader from '../../components/common/PageHeader'
import { Server, CheckCircle, XCircle, Clock } from 'lucide-react'

export default function SystemHealth() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.health.check()
        setHealth(res.data)
      } catch {
        setHealth({ status: 'unhealthy', error: 'Cannot reach server' })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Checking system health..." />

  const checks = [
    { name: 'API Server', status: health?.status === 'healthy' ? 'healthy' : 'unhealthy' },
    { name: 'Database', status: health?.database || 'unknown' },
    { name: 'ML Model', status: health?.model || 'unknown' },
    { name: 'Redis Cache', status: health?.redis || 'unknown' },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="System Health" description="Monitor system component health status" />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {checks.map((check) => (
          <Card key={check.name} className="text-center">
            <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full mb-3 ${
              check.status === 'healthy' ? 'bg-green-100' : 'bg-red-100'
            }`}>
              {check.status === 'healthy' ? (
                <CheckCircle className="h-6 w-6 text-green-600" />
              ) : (
                <XCircle className="h-6 w-6 text-red-600" />
              )}
            </div>
            <h3 className="text-sm font-semibold text-slate-900">{check.name}</h3>
            <Badge variant={check.status === 'healthy' ? 'success' : 'danger'} className="mt-2">
              {check.status}
            </Badge>
          </Card>
        ))}
      </div>

      <Card header="System Information">
        <div className="space-y-3">
          {health?.version && (
            <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
              <span className="text-sm text-slate-600">Version</span>
              <span className="text-sm font-medium text-slate-900">{health.version}</span>
            </div>
          )}
          {health?.uptime && (
            <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
              <span className="text-sm text-slate-600">Uptime</span>
              <span className="text-sm font-medium text-slate-900">{health.uptime}</span>
            </div>
          )}
          {health?.environment && (
            <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
              <span className="text-sm text-slate-600">Environment</span>
              <span className="text-sm font-medium text-slate-900">{health.environment}</span>
            </div>
          )}
          <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
            <span className="text-sm text-slate-600">Last Checked</span>
            <span className="text-sm font-medium text-slate-900">{new Date().toLocaleString()}</span>
          </div>
        </div>
      </Card>
    </div>
  )
}
