import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Heart, Shield, Brain, Activity, Bell, Eye, Lock,
  ArrowRight, CheckCircle, ChevronRight
} from 'lucide-react'

const features = [
  { icon: Brain, title: 'AI Prediction', desc: 'Advanced machine learning models analyze your health data for accurate heart risk assessment.' },
  { icon: Eye, title: 'Explainable AI', desc: 'Transparent SHAP-based explanations showing exactly what drives your risk predictions.' },
  { icon: Activity, title: 'Personalized Insights', desc: 'Tailored recommendations based on your unique health profile and lifestyle factors.' },
  { icon: Shield, title: 'Professional Review', desc: 'Clinical reviewer validation ensuring AI predictions meet medical standards.' },
  { icon: Bell, title: 'Emergency Alerts', desc: 'Instant notifications when critical risk levels are detected.' },
  { icon: Lock, title: 'Secure & Private', desc: 'Enterprise-grade security with HIPAA-compliant data handling.' },
]

const steps = [
  { num: '01', title: 'Enter Health Data', desc: 'Provide your clinical measurements and lifestyle information through our guided assessment form.' },
  { num: '02', title: 'AI Analysis', desc: 'Our trained model processes your data, analyzing clinical and lifestyle factors simultaneously.' },
  { num: '03', title: 'Personalized Results', desc: 'Receive your risk assessment with clear explanations, recommendations, and actionable insights.' },
]

const fadeUp = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-red-600 rounded-lg">
              <Heart className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-900">HeartGuard</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 px-4 py-2">Sign In</Link>
            <Link to="/register" className="text-sm font-medium text-white bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-7xl mx-auto px-6 py-24 lg:py-32">
          <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.6 }} className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-red-50 text-red-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
              <Heart className="h-4 w-4" />
              AI-Powered Heart Health Assessment
            </div>
            <h1 className="text-4xl lg:text-6xl font-extrabold text-slate-900 leading-tight">
              Protect Your Heart with{' '}
              <span className="text-red-600">Intelligent</span> Risk Assessment
            </h1>
            <p className="mt-6 text-lg text-slate-600 leading-relaxed">
              HeartGuard combines advanced machine learning with clinical expertise to provide
              personalized, explainable heart disease risk assessments. Early detection saves lives.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/register"
                className="inline-flex items-center gap-2 bg-red-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-red-700 transition-colors"
              >
                Start Free Assessment
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/about"
                className="inline-flex items-center gap-2 bg-white text-slate-700 px-6 py-3 rounded-lg font-medium border border-slate-300 hover:bg-slate-50 transition-colors"
              >
                Learn More
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">Comprehensive Heart Health Platform</h2>
            <p className="mt-3 text-slate-600 max-w-2xl mx-auto">
              Everything you need for proactive heart health monitoring and risk management.
            </p>
          </motion.div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((f, i) => (
              <motion.div
                key={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
                transition={{ delay: i * 0.1 }}
                className="p-6 bg-slate-50 rounded-xl border border-slate-100 hover:shadow-md transition-shadow"
              >
                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center mb-4">
                  <f.icon className="h-5 w-5 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{f.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">How It Works</h2>
            <p className="mt-3 text-slate-600">Three simple steps to your heart health assessment</p>
          </motion.div>
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((s, i) => (
              <motion.div
                key={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
                transition={{ delay: i * 0.15 }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-16 h-16 bg-red-600 text-white rounded-2xl text-xl font-bold mb-6">
                  {s.num}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{s.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}>
            <h2 className="text-3xl font-bold text-slate-900">Take Charge of Your Heart Health</h2>
            <p className="mt-3 text-slate-600 max-w-xl mx-auto">
              Join thousands of users who trust HeartGuard for early heart disease detection.
            </p>
            <div className="mt-8 flex items-center justify-center gap-4">
              <Link
                to="/register"
                className="inline-flex items-center gap-2 bg-red-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-red-700 transition-colors"
              >
                Get Started Free
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Heart className="h-4 w-4 text-red-600" />
            <span className="text-sm font-medium text-slate-900">HeartGuard</span>
          </div>
          <p className="text-sm text-slate-500">&copy; 2026 HeartGuard. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
