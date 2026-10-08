import { useState, useEffect } from 'react'
import api from '../../services/api'
import Card from '../../components/common/Card'
import Loading from '../../components/common/Loading'
import EmptyState from '../../components/common/EmptyState'
import PageHeader from '../../components/common/PageHeader'
import { Lightbulb, Shield, Heart, Apple, Activity, Moon, Brain } from 'lucide-react'

const categoryIcons = {
  diet: Apple,
  exercise: Activity,
  sleep: Moon,
  stress: Brain,
  general: Heart,
  monitoring: Shield,
}

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.recommendations.getAll()
        setRecommendations(res.data.items || res.data || [])
      } catch {
        setRecommendations([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading text="Loading recommendations..." />

  const grouped = recommendations.reduce((acc, r) => {
    const cat = r.category || 'general'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(r)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <PageHeader title="Recommendations" description="Personalized health recommendations based on your assessments" />

      {recommendations.length === 0 ? (
        <EmptyState icon={Lightbulb} title="No recommendations yet" message="Complete an assessment to receive personalized recommendations." />
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([category, items]) => {
            const Icon = categoryIcons[category] || Lightbulb
            return (
              <div key={category}>
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="h-5 w-5 text-red-600" />
                  <h3 className="text-lg font-semibold text-slate-900 capitalize">{category}</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {items.map((r, i) => (
                    <Card key={r.id || i} className="hover:shadow-md transition-shadow">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-red-50 rounded-lg">
                          <Icon className="h-4 w-4 text-red-600" />
                        </div>
                        <div>
                          <p className="text-sm text-slate-700 leading-relaxed">
                            {typeof r === 'string' ? r : r.content || r.text || r.description}
                          </p>
                          {r.priority && (
                            <span className="inline-block mt-2 text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                              {r.priority} priority
                            </span>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
