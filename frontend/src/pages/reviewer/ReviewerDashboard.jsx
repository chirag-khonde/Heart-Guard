import { useState, useEffect } from 'react'
import api from '../../services/api'
import StatCard from '../../components/common/StatCard'
import Card from '../../components/common/Card'
import Loading from '../../components/common/Loading'
import PageHeader from '../../components/common/PageHeader'
import { ClipboardCheck, Clock, CheckCircle, AlertTriangle } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function ReviewerDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.reviews.getStats()
        setStats(res.data)
      } catch {
        setStats(null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Loading dashboard..." />

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome, ${user?.name?.split(' ')[0]}`}
        description="Reviewer workspace - manage and validate assessments"
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={ClipboardCheck} label="Total Reviews" value={stats?.total_reviews || 0} color="blue" />
        <StatCard icon={Clock} label="Pending Reviews" value={stats?.pending_reviews || 0} color="amber" />
        <StatCard icon={CheckCircle} label="Completed" value={stats?.completed_reviews || 0} color="green" />
        <StatCard icon={AlertTriangle} label="Flagged" value={stats?.flagged_reviews || 0} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card header="Recent Activity">
          {stats?.recent_activity?.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_activity.map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-slate-900">Assessment #{item.assessment_id}</p>
                    <p className="text-xs text-slate-500">{new Date(item.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    item.status === 'approved' ? 'bg-green-100 text-green-700' :
                    item.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700'
                  }`}>{item.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-4">No recent activity</p>
          )}
        </Card>

        <Card header="Queue Summary">
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-amber-50 rounded-lg border border-amber-200">
              <div>
                <p className="text-sm font-medium text-amber-800">Pending Reviews</p>
                <p className="text-2xl font-bold text-amber-900">{stats?.pending_reviews || 0}</p>
              </div>
              <Clock className="h-8 w-8 text-amber-500" />
            </div>
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
              <div>
                <p className="text-sm font-medium text-green-800">Completed Today</p>
                <p className="text-2xl font-bold text-green-900">{stats?.completed_today || 0}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
