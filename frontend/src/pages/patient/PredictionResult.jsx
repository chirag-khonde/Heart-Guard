import { useLocation, Link } from 'react-router-dom'
import RiskGauge from '../../components/common/RiskGauge'
import Card from '../../components/common/Card'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import PageHeader from '../../components/common/PageHeader'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { AlertTriangle, Download, ArrowLeft, Lightbulb } from 'lucide-react'

export default function PredictionResult() {
  const location = useLocation()
  const assessment = location.state?.assessment

  if (!assessment) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-amber-400 mx-auto" />
        <h2 className="mt-4 text-lg font-semibold text-slate-900">No Assessment Result</h2>
        <p className="mt-2 text-sm text-slate-500">Please complete an assessment first.</p>
        <Link to="/assessment" className="mt-4 inline-block">
          <Button>Take Assessment</Button>
        </Link>
      </div>
    )
  }

  const riskScore = assessment.risk_percentage || assessment.risk_score || 0
  const riskCategory = assessment.risk_category || 'Unknown'

  const shapData = assessment.shap_explanation
    ? Object.entries(assessment.shap_explanation).map(([feature, value]) => ({
        feature: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: Number(value),
        positive: Number(value) > 0,
      })).sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    : []

  const recommendations = assessment.recommendations || []

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader title="Assessment Result" description="Your heart disease risk assessment is ready" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Score */}
        <Card className="lg:col-span-1 text-center">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Risk Score</h3>
          <RiskGauge score={riskScore} size={180} />
          <Badge variant={riskCategory.toLowerCase()} className="mt-4 text-sm">
            {riskCategory}
          </Badge>
          <div className="mt-6 space-y-2 text-sm">
            {assessment.clinical_risk !== undefined && (
              <div className="flex justify-between"><span className="text-slate-500">Clinical Risk:</span><span className="font-medium">{assessment.clinical_risk}%</span></div>
            )}
            {assessment.lifestyle_risk !== undefined && (
              <div className="flex justify-between"><span className="text-slate-500">Lifestyle Risk:</span><span className="font-medium">{assessment.lifestyle_risk}%</span></div>
            )}
          </div>
        </Card>

        {/* SHAP Explanation */}
        <Card className="lg:col-span-2">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Risk Factor Contributions</h3>
          {shapData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={shapData} layout="vertical" margin={{ left: 100 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis dataKey="feature" type="category" width={120} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val) => [val.toFixed(3), 'SHAP Value']} />
                <Bar
                  dataKey="value"
                  fill="#DC2626"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">No explanation data available</p>
          )}
        </Card>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Recommendations</h3>
          <div className="space-y-3">
            {recommendations.map((r, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <Lightbulb className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-slate-700">{typeof r === 'string' ? r : r.content || r.text}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
        <p className="text-sm text-amber-800">
          <strong>Disclaimer:</strong> This is an AI-based screening tool. It does not replace professional medical advice.
          Please consult a healthcare provider for diagnosis and treatment.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Link to="/dashboard">
          <Button variant="secondary"><ArrowLeft className="h-4 w-4" /> Back to Dashboard</Button>
        </Link>
        <Link to="/history">
          <Button variant="ghost">View History</Button>
        </Link>
      </div>
    </div>
  )
}
