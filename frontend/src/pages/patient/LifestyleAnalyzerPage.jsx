import { useState } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Button from '../../components/common/Button'
import Badge from '../../components/common/Badge'
import PageHeader from '../../components/common/PageHeader'
import { Activity, Lightbulb, AlertCircle, CheckCircle2 } from 'lucide-react'
import { formatApiError } from '../../utils/errors'

export default function LifestyleAnalyzerPage() {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleAnalyze = async () => {
    if (!text.trim()) return
    setLoading(true)
    setResult(null)
    try {
      let res
      if (api.lifestyle?.analyze) {
        res = await api.lifestyle.analyze({ text: text.trim() })
      } else {
        res = await api.assessments.create({ lifestyle_text: text.trim() })
      }
      setResult(res.data)
    } catch (err) {
      setResult({ error: formatApiError(err, 'Analysis failed. Please try again.') })
    } finally {
      setLoading(false)
    }
  }

  const score = result?.lifestyle_score ?? result?.risk_score ?? result?.overall_risk
  const category = result?.risk_category || 'LOW'

  const getCategoryVariant = (cat) => {
    const c = String(cat).toUpperCase()
    if (c === 'CRITICAL' || c === 'HIGH') return 'danger'
    if (c === 'ELEVATED' || c === 'MODERATE') return 'warning'
    return 'success'
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader title="Lifestyle Analyzer" description="Analyze how your daily habits impact your heart health" />

      <Card>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">Describe Your Lifestyle</h3>
        <p className="text-sm text-slate-500 mb-4">
          Share details about your daily routine, diet, exercise, sleep patterns, and stress levels.
        </p>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={7}
          placeholder="e.g. I walk 30 minutes daily, eat lots of vegetables, drink 2 cups of coffee, sleep 6-7 hours, work in an office with moderate stress..."
          className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
        />
        <div className="mt-4 flex justify-end">
          <Button onClick={handleAnalyze} loading={loading}>
            <Activity className="h-4 w-4" /> Analyze Lifestyle
          </Button>
        </div>
      </Card>

      {result && !result.error && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Analysis Results</h3>
            <Badge variant={getCategoryVariant(category)}>{category} RISK</Badge>
          </div>
          <div className="space-y-5">
            {score !== undefined && (
              <div className="bg-slate-50 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Lifestyle Risk Score</p>
                  <p className="text-3xl font-bold text-slate-900 mt-1">{score}%</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Signals Detected</p>
                  <p className="text-lg font-semibold text-slate-700 mt-1">
                    {result.detected_risk_factors?.length || 0} factor{result.detected_risk_factors?.length === 1 ? '' : 's'}
                  </p>
                </div>
              </div>
            )}

            {result.detected_risk_factors && result.detected_risk_factors.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-slate-800 mb-2">Detected Risk Factors</h4>
                <div className="flex flex-wrap gap-2">
                  {result.detected_risk_factors.map((f, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200"
                    >
                      <AlertCircle className="h-3 w-3" />
                      {typeof f === 'string' ? f : f.display_name || f.category || JSON.stringify(f)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.recommendations && result.recommendations.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-slate-800 mb-2">Personalized Recommendations</h4>
                <div className="space-y-2">
                  {result.recommendations.map((r, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <Lightbulb className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-slate-700">{typeof r === 'string' ? r : r.content || r.title}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.summary && (
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">AI Clinical Summary</h4>
                <p className="text-sm text-slate-600 whitespace-pre-line">{result.summary}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {result?.error && (
        <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
          {result.error}
        </div>
      )}
    </div>
  )
}
