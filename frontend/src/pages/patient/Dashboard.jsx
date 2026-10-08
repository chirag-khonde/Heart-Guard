import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import api from '../../services/api'
import RiskGauge from '../../components/common/RiskGauge'
import StatCard from '../../components/common/StatCard'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Loading from '../../components/common/Loading'
import { ClipboardPlus, History, AlertTriangle, Activity, TrendingUp, Lightbulb } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function PatientDashboard() {
  const { user } = useAuth()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.dashboard.getDashboard()
        setDashboard(res.data)
      } catch (err) {
        setError('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Loading dashboard..." />
  if (error) return <div className="text-center py-12 text-red-600">{error}</div>

  const risk = dashboard?.latest_assessment
  const trend = dashboard?.risk_trend || []

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold">Welcome back, {user?.name?.split(' ')[0]}</h1>
        <p className="mt-1 text-red-100">Here&apos;s your heart health overview</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={ClipboardPlus} label="Total Assessments" value={dashboard?.total_assessments || 0} color="red" />
        <StatCard icon={TrendingUp} label="Avg Risk Score" value={`${dashboard?.avg_risk || 0}%`} color="amber" />
        <StatCard icon={AlertTriangle} label="Critical Alerts" value={dashboard?.critical_alerts || 0} color="red" />
        <StatCard icon={Activity} label="Latest Category" value={risk?.risk_category || 'N/A'} color="blue" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Gauge */}
        <Card className="lg:col-span-1">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Latest Risk Score</h3>
          {risk ? (
            <div className="flex flex-col items-center">
              <RiskGauge score={risk.risk_percentage || risk.risk_score || 0} size={160} />
              <Badge variant={risk.risk_category?.toLowerCase() || 'info'} className="mt-4">
                {risk.risk_category || 'Unknown'}
              </Badge>
              <Link to="/assessment" className="mt-4 text-sm text-red-600 hover:text-red-700 font-medium">
                Take New Assessment →
              </Link>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-slate-500 mb-4">No assessments yet</p>
              <Link to="/assessment" className="text-sm text-red-600 hover:text-red-700 font-medium">
                Take Your First Assessment →
              </Link>
            </div>
          )}
        </Card>

        {/* Risk Trend */}
        <Card className="lg:col-span-2">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Risk Trend</h3>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="risk_score" stroke="#DC2626" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[200px] text-sm text-slate-500">
              Complete multiple assessments to see your risk trend
            </div>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Assessments */}
        <Card header="Recent Assessments">
          {dashboard?.recent_assessments?.length > 0 ? (
            <div className="space-y-3">
              {dashboard.recent_assessments.map((a) => (
                <div key={a.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{new Date(a.created_at).toLocaleDateString()}</p>
                    <p className="text-xs text-slate-500">Risk: {a.risk_percentage || a.risk_score}%</p>
                  </div>
                  <Badge variant={a.risk_category?.toLowerCase() || 'info'}>{a.risk_category}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-4">No assessments yet</p>
          )}
        </Card>

        {/* Recommendations */}
        <Card header="Recommendations">
          {dashboard?.recent_recommendations?.length > 0 ? (
            <div className="space-y-3">
              {dashboard.recent_recommendations.slice(0, 4).map((r, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                  <Lightbulb className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-slate-700">{r.content || r.text}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-4">No recommendations yet</p>
          )}
          <Link to="/recommendations" className="block mt-4 text-sm text-red-600 hover:text-red-700 font-medium text-center">
            View All →
          </Link>
        </Card>
      </div>
    </div>
  )
}
