import { useState, useEffect } from 'react'
import api from '../../services/api'
import StatCard from '../../components/common/StatCard'
import Card from '../../components/common/Card'
import Loading from '../../components/common/Loading'
import PageHeader from '../../components/common/PageHeader'
import { Users, ClipboardCheck, AlertTriangle, Activity, TrendingUp, Shield } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const COLORS = ['#16A34A', '#D97706', '#F59E0B', '#DC2626']

export default function AdminDashboard() {
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

  if (loading) return <Loading text="Loading admin dashboard..." />

  const riskDist = data?.risk_distribution
    ? Object.entries(data.risk_distribution).map(([name, value]) => ({ name, value }))
    : []

  return (
    <div className="space-y-6">
      <PageHeader title="Admin Dashboard" description="System overview and key metrics" />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={Users} label="Total Users" value={data?.total_users || 0} color="blue" />
        <StatCard icon={ClipboardCheck} label="Total Assessments" value={data?.total_assessments || 0} color="green" />
        <StatCard icon={AlertTriangle} label="Critical Cases" value={data?.critical_cases || 0} color="red" />
        <StatCard icon={Activity} label="Avg Risk Score" value={`${data?.avg_risk || 0}%`} color="amber" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card header="Risk Distribution">
          {riskDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={riskDist} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {riskDist.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">No data</p>
          )}
        </Card>

        <Card header="Prediction Trends">
          {data?.prediction_trends?.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={data.prediction_trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#1E3A8A" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">No trend data</p>
          )}
        </Card>
      </div>

      <Card header="System Status">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <Shield className="h-6 w-6 text-green-600 mx-auto" />
            <p className="mt-2 text-sm font-medium text-green-800">All Systems Operational</p>
          </div>
          <div className="text-center p-4 bg-slate-50 rounded-lg">
            <p className="text-2xl font-bold text-slate-900">{data?.uptime || '99.9%'}</p>
            <p className="text-sm text-slate-500">Uptime</p>
          </div>
          <div className="text-center p-4 bg-slate-50 rounded-lg">
            <p className="text-2xl font-bold text-slate-900">{data?.response_time || '<100ms'}</p>
            <p className="text-sm text-slate-500">Avg Response</p>
          </div>
          <div className="text-center p-4 bg-slate-50 rounded-lg">
            <p className="text-2xl font-bold text-slate-900">{data?.model_version || 'v1.0'}</p>
            <p className="text-sm text-slate-500">Model Version</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
