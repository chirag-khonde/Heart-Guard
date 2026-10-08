import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Button from '../../components/common/Button'
import Loading from '../../components/common/Loading'
import EmptyState from '../../components/common/EmptyState'
import PageHeader from '../../components/common/PageHeader'
import { FileText, Download, Loader2 } from 'lucide-react'
import { useToast } from '../../components/common/Toast'

export default function ReportsPage() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(null)
  const { addToast } = useToast()

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.reports.getAll()
        const list = Array.isArray(res.data) ? res.data : (res.data?.items || [])
        setReports(list)
      } catch {
        setReports([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleDownload = async (report) => {
    const reportId = report.id || report.assessment_id
    setGenerating(reportId)
    try {
      const res = await api.reports.download(reportId)
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = report.filename || `HeartGuard-Report-${reportId}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      addToast('Report downloaded successfully', 'success')
    } catch {
      addToast('Failed to download report', 'error')
    } finally {
      setGenerating(null)
    }
  }

  if (loading) return <Loading text="Loading reports..." />

  return (
    <div className="space-y-6">
      <PageHeader title="Reports" description="Generate and download your health reports" />

      {reports.length === 0 ? (
        <EmptyState icon={FileText} title="No reports yet" message="Complete assessments to generate reports." />
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <Card key={report.id || report.assessment_id} className="hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-red-50 rounded-lg">
                    <FileText className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">{report.title || `Report #${report.id || report.assessment_id}`}</h4>
                    <p className="text-xs text-slate-500">{new Date(report.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
                <Button size="sm" variant="secondary" loading={generating === (report.id || report.assessment_id)} onClick={() => handleDownload(report)}>
                  <Download className="h-4 w-4" /> Download PDF
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
