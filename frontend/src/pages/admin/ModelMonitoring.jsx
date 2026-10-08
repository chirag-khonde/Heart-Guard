import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Loading from '../../components/common/Loading'
import PageHeader from '../../components/common/PageHeader'
import { Activity, CheckCircle, AlertTriangle, Clock } from 'lucide-react'

export default function ModelMonitoring() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [statusRes, driftRes, perfRes] = await Promise.all([
          api.admin.getModelStatus(),
          api.admin.getDrift(),
          api.admin.getPerformance(),
        ])
        setData({
          status: statusRes.data,
          drift: driftRes.data,
          performance: perfRes.data,
        })
      } catch {
        setData(null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Loading model monitoring..." />

  return (
    <div className="space-y-6">
      <PageHeader title="Model Monitoring" description="Monitor model status, performance, and drift indicators" />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Model Status</p>
              <p className="text-lg font-semibold text-slate-900">{data?.status?.status || 'Active'}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Version</p>
              <p className="text-lg font-semibold text-slate-900">{data?.status?.version || 'v1.0.0'}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 rounded-lg">
              <Clock className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Last Trained</p>
              <p className="text-lg font-semibold text-slate-900">{data?.status?.last_trained || 'N/A'}</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card header="Performance Metrics">
          {data?.performance ? (
            <div className="space-y-3">
              {Object.entries(data.performance).map(([metric, value]) => (
                <div key={metric} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-600 capitalize">{metric.replace(/_/g, ' ')}</span>
                  <span className="text-sm font-medium text-slate-900">{typeof value === 'number' ? (value * 100).toFixed(1) + '%' : value}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">No performance data</p>
          )}
        </Card>

        <Card header="Data Drift Indicators">
          {data?.drift ? (
            <div className="space-y-3">
              {Object.entries(data.drift).map(([feature, value]) => (
                <div key={feature} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-600 capitalize">{feature.replace(/_/g, ' ')}</span>
                  <Badge variant={value > 0.1 ? 'critical' : value > 0.05 ? 'warning' : 'success'}>
                    {typeof value === 'number' ? value.toFixed(4) : value}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">No drift data</p>
          )}
        </Card>
      </div>
    </div>
  )
}
