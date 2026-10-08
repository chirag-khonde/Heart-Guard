import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Loading from '../../components/common/Loading'
import EmptyState from '../../components/common/EmptyState'
import PageHeader from '../../components/common/PageHeader'
import { Bell, AlertTriangle } from 'lucide-react'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.dashboard.getDashboard()
        setAlerts(res.data.alerts || [])
      } catch {
        setAlerts([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Loading alerts..." />

  return (
    <div className="space-y-6">
      <PageHeader title="Alerts" description="View your health alerts and notifications" />

      {alerts.length === 0 ? (
        <EmptyState icon={Bell} title="No alerts" message="You have no alerts at this time." />
      ) : (
        <div className="space-y-3">
          {alerts.map((alert, i) => (
            <Card key={alert.id || i} className="hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                <div className={`p-2 rounded-lg ${
                  alert.severity === 'critical' ? 'bg-red-100' : alert.severity === 'warning' ? 'bg-amber-100' : 'bg-blue-100'
                }`}>
                  <AlertTriangle className={`h-5 w-5 ${
                    alert.severity === 'critical' ? 'text-red-600' : alert.severity === 'warning' ? 'text-amber-600' : 'text-blue-600'
                  }`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-slate-900">{alert.title || 'Alert'}</h4>
                    <Badge variant={alert.severity === 'critical' ? 'critical' : alert.severity === 'warning' ? 'warning' : 'info'}>
                      {alert.severity || 'info'}
                    </Badge>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{alert.message || alert.description}</p>
                  <p className="mt-2 text-xs text-slate-400">{alert.created_at ? new Date(alert.created_at).toLocaleString() : ''}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
