import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function StatCard({ icon: Icon, label, value, trend, trendValue, color = 'slate' }) {
  const bgColors = {
    red: 'bg-red-50',
    blue: 'bg-blue-50',
    green: 'bg-green-50',
    amber: 'bg-amber-50',
    slate: 'bg-slate-50',
  }
  const iconColors = {
    red: 'text-red-600',
    blue: 'text-blue-600',
    green: 'text-green-600',
    amber: 'text-amber-600',
    slate: 'text-slate-600',
  }

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendColor = trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-slate-400'

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between">
        <div className={`p-3 rounded-lg ${bgColors[color]}`}>
          <Icon className={`h-5 w-5 ${iconColors[color]}`} />
        </div>
        {trendValue !== undefined && (
          <div className={`flex items-center gap-1 text-sm ${trendColor}`}>
            <TrendIcon className="h-4 w-4" />
            <span>{trendValue}</span>
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm text-slate-500 mt-1">{label}</p>
      </div>
    </div>
  )
}
