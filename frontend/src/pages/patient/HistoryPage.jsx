import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Loading from '../../components/common/Loading'
import EmptyState from '../../components/common/EmptyState'
import PageHeader from '../../components/common/PageHeader'
import Select from '../../components/common/Select'
import { History, ChevronDown, ChevronUp, Filter } from 'lucide-react'

export default function HistoryPage() {
  const [assessments, setAssessments] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState(null)
  const [filter, setFilter] = useState({ risk_category: '', sort: 'newest' })

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.assessments.getAll(filter)
        setAssessments(res.data.items || res.data || [])
      } catch {
        setAssessments([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [filter])

  const toggle = (id) => setExpandedId(expandedId === id ? null : id)

  if (loading) return <Loading text="Loading history..." />

  return (
    <div className="space-y-6">
      <PageHeader title="Assessment History" description="View all your past assessments" />

      <div className="flex items-center gap-4">
        <Select
          label="Risk Category"
          value={filter.risk_category}
          onChange={(e) => setFilter({ ...filter, risk_category: e.target.value })}
          options={[
            { value: '', label: 'All' },
            { value: 'low', label: 'Low' },
            { value: 'moderate', label: 'Moderate' },
            { value: 'high', label: 'High' },
            { value: 'critical', label: 'Critical' },
          ]}
        />
        <Select
          label="Sort"
          value={filter.sort}
          onChange={(e) => setFilter({ ...filter, sort: e.target.value })}
          options={[
            { value: 'newest', label: 'Newest First' },
            { value: 'oldest', label: 'Oldest First' },
            { value: 'risk_high', label: 'Highest Risk' },
            { value: 'risk_low', label: 'Lowest Risk' },
          ]}
        />
      </div>

      {assessments.length === 0 ? (
        <EmptyState icon={History} title="No assessments yet" message="Take your first assessment to see results here." />
      ) : (
        <Card padding="p-0">
          <div className="divide-y divide-slate-200">
            {assessments.map((a) => (
              <div key={a.id}>
                <button
                  onClick={() => toggle(a.id)}
                  className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 text-left"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-900">{new Date(a.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
                      <p className="text-xs text-slate-500">Risk: {a.risk_percentage || a.risk_score}%</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={a.risk_category?.toLowerCase() || 'info'}>{a.risk_category}</Badge>
                    {expandedId === a.id ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                  </div>
                </button>
                {expandedId === a.id && (
                  <div className="px-6 pb-4 bg-slate-50">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div><span className="text-slate-500">Age:</span> <span className="font-medium">{a.age}</span></div>
                      <div><span className="text-slate-500">Sex:</span> <span className="font-medium">{a.sex}</span></div>
                      <div><span className="text-slate-500">BP:</span> <span className="font-medium">{a.resting_blood_pressure} mmHg</span></div>
                      <div><span className="text-slate-500">Cholesterol:</span> <span className="font-medium">{a.cholesterol} mg/dl</span></div>
                      <div><span className="text-slate-500">Max HR:</span> <span className="font-medium">{a.max_heart_rate}</span></div>
                      <div><span className="text-slate-500">Chest Pain:</span> <span className="font-medium">{a.chest_pain_type}</span></div>
                      <div><span className="text-slate-500">ST Depression:</span> <span className="font-medium">{a.st_depression}</span></div>
                      <div><span className="text-slate-500">Vessels:</span> <span className="font-medium">{a.num_major_vessels}</span></div>
                    </div>
                    {a.lifestyle_text && (
                      <div className="mt-3 text-sm"><span className="text-slate-500">Lifestyle:</span> <span className="text-slate-700">{a.lifestyle_text}</span></div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
