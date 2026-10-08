import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import Loading from '../../components/common/Loading'
import EmptyState from '../../components/common/EmptyState'
import PageHeader from '../../components/common/PageHeader'
import { ClipboardCheck, Eye } from 'lucide-react'

export default function ReviewQueue() {
  const [assessments, setAssessments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.reviews.getPending()
        setAssessments(res.data.items || res.data || [])
      } catch {
        setAssessments([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Loading review queue..." />

  return (
    <div className="space-y-6">
      <PageHeader title="Review Queue" description="Pending assessments awaiting clinical review" />

      {assessments.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="Queue empty" message="No pending assessments to review." />
      ) : (
        <Card padding="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">ID</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Patient</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Risk Score</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Category</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Date</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-600">Status</th>
                  <th className="px-6 py-3 text-right font-medium text-slate-600">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {assessments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-mono text-xs text-slate-500">#{a.id?.slice(0, 8)}</td>
                    <td className="px-6 py-4 font-medium text-slate-900">{a.patient_name || a.user_name || 'Unknown'}</td>
                    <td className="px-6 py-4 font-medium text-slate-900">{a.risk_percentage || a.risk_score}%</td>
                    <td className="px-6 py-4"><Badge variant={a.risk_category?.toLowerCase() || 'info'}>{a.risk_category}</Badge></td>
                    <td className="px-6 py-4 text-slate-500">{new Date(a.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4"><Badge variant="pending">Pending</Badge></td>
                    <td className="px-6 py-4 text-right">
                      <Link to={`/reviewer/assessment/${a.id}`}>
                        <Button size="sm" variant="secondary"><Eye className="h-4 w-4" /> Review</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
