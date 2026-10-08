import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import RiskGauge from '../../components/common/RiskGauge'
import Loading from '../../components/common/Loading'
import PageHeader from '../../components/common/PageHeader'
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

export default function ReviewDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [assessment, setAssessment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ status: 'approved', notes: '' })

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.assessments.getById(id)
        setAssessment(res.data)
      } catch {
        setAssessment(null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      await api.reviews.create(id, form)
      navigate('/reviewer/queue')
    } catch {
      setSubmitting(false)
    }
  }

  if (loading) return <Loading text="Loading assessment..." />
  if (!assessment) return <div className="text-center py-12 text-red-600">Assessment not found</div>

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title={`Review Assessment #${id?.slice(0, 8)}`}
        description="Review assessment details and provide clinical feedback"
        actions={
          <Button variant="secondary" onClick={() => navigate('/reviewer/queue')}>
            <ArrowLeft className="h-4 w-4" /> Back to Queue
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="text-center">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Risk Score</h3>
          <RiskGauge score={assessment.risk_percentage || assessment.risk_score || 0} size={140} />
          <Badge variant={assessment.risk_category?.toLowerCase() || 'info'} className="mt-4">
            {assessment.risk_category}
          </Badge>
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Assessment Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Age:</span> <span className="font-medium">{assessment.age}</span></div>
            <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Sex:</span> <span className="font-medium">{assessment.sex}</span></div>
            <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Chest Pain:</span> <span className="font-medium">{assessment.chest_pain_type}</span></div>
            <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">BP:</span> <span className="font-medium">{assessment.resting_blood_pressure}</span></div>
            <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Cholesterol:</span> <span className="font-medium">{assessment.cholesterol}</span></div>
            <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Max HR:</span> <span className="font-medium">{assessment.max_heart_rate}</span></div>
            <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">ST Depression:</span> <span className="font-medium">{assessment.st_depression}</span></div>
            <div className="bg-slate-50 p-3 rounded-lg"><span className="text-slate-500">Vessels:</span> <span className="font-medium">{assessment.num_major_vessels}</span></div>
          </div>
          {assessment.lifestyle_text && (
            <div className="mt-4 bg-slate-50 p-3 rounded-lg text-sm">
              <span className="text-slate-500">Lifestyle:</span>
              <p className="mt-1 text-slate-700">{assessment.lifestyle_text}</p>
            </div>
          )}
        </Card>
      </div>

      {/* Review Form */}
      <Card>
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Clinical Review</h3>
        <div className="space-y-4">
          <div className="flex gap-4">
            <Button
              variant={form.status === 'approved' ? 'primary' : 'secondary'}
              onClick={() => setForm({ ...form, status: 'approved' })}
            >
              <CheckCircle className="h-4 w-4" /> Approve
            </Button>
            <Button
              variant={form.status === 'rejected' ? 'danger' : 'secondary'}
              onClick={() => setForm({ ...form, status: 'rejected' })}
            >
              <XCircle className="h-4 w-4" /> Reject
            </Button>
            <Button
              variant={form.status === 'flagged' ? 'ghost' : 'secondary'}
              onClick={() => setForm({ ...form, status: 'flagged' })}
            >
              <AlertTriangle className="h-4 w-4" /> Flag
            </Button>
          </div>
          <textarea
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            rows={4}
            placeholder="Add review notes (optional)..."
            className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <div className="flex justify-end">
            <Button onClick={handleSubmit} loading={submitting}>Submit Review</Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
