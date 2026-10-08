import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Loading from '../../components/common/Loading'
import PageHeader from '../../components/common/PageHeader'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const COLORS = ['#16A34A', '#D97706', '#F59E0B', '#DC2626']

export default function AdminAnalytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.admin.getAnalytics()
        setData(res.data)
      } catch {
        setData(null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Loading analytics..." />

  const riskDist = data?.risk_distribution
    ? Object.entries(data.risk_distribution).map(([name, value]) => ({ name, value }))
    : []
  const trends = data?.prediction_trends || []
  const volume = data?.assessment_volume || []

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Comprehensive system analytics and insights" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card header="Risk Distribution">
          {riskDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={riskDist} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {riskDist.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-500 text-center py-12">No data available</p>
          )}
        </Card>

        <Card header="Prediction Trends">
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#1E3A8A" strokeWidth={2} />
                <Line type="monotone" dataKey="high_risk" stroke="#DC2626" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-500 text-center py-12">No trend data</p>
          )}
        </Card>

        <Card header="Assessment Volume">
          {volume.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={volume}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#DC2626" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-500 text-center py-12">No volume data</p>
          )}
        </Card>

        <Card header="Model Performance">
          <div className="space-y-4">
            {data?.model_performance ? (
              Object.entries(data.model_performance).map(([metric, value]) => (
                <div key={metric} className="flex items-center justify-between">
                  <span className="text-sm text-slate-600 capitalize">{metric.replace(/_/g, ' ')}</span>
                  <span className="text-sm font-medium text-slate-900">{typeof value === 'number' ? value.toFixed(3) : value}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500 text-center py-8">No performance data</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
