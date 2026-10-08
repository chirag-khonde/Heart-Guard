import { Heart } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white">
      <nav className="border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-red-600 rounded-lg"><Heart className="h-5 w-5 text-white" /></div>
            <span className="text-xl font-bold text-slate-900">HeartGuard</span>
          </div>
          <Link to="/" className="text-sm text-slate-600 hover:text-slate-900">Back to Home</Link>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="text-4xl font-bold text-slate-900 mb-6">About HeartGuard</h1>
        <div className="prose prose-slate max-w-none space-y-6 text-slate-600 leading-relaxed">
          <p>
            HeartGuard is an AI-powered heart disease risk assessment platform designed to help
            individuals and healthcare professionals identify cardiovascular risk factors early.
          </p>
          <h2 className="text-2xl font-semibold text-slate-900 mt-8">Our Mission</h2>
          <p>
            To democratize heart health screening by making accurate, explainable AI-based risk
            assessment accessible to everyone. Early detection of heart disease risk factors
            can significantly improve outcomes and save lives.
          </p>
          <h2 className="text-2xl font-semibold text-slate-900 mt-8">Technology</h2>
          <p>
            HeartGuard uses machine learning models trained on clinical datasets to predict
            heart disease risk. Our models provide SHAP-based explanations so users and
            clinicians understand exactly what factors contribute to each prediction.
          </p>
          <h2 className="text-2xl font-semibold text-slate-900 mt-8">Disclaimer</h2>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
            <p className="text-amber-800">
              HeartGuard is a screening tool and does not replace professional medical advice,
              diagnosis, or treatment. Always consult with a qualified healthcare provider for
              medical decisions.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
