import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/routes/ProtectedRoute'
import RoleRoute from './components/routes/RoleRoute'
import PatientLayout from './components/layout/PatientLayout'
import ReviewerLayout from './components/layout/ReviewerLayout'
import AdminLayout from './components/layout/AdminLayout'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import AboutPage from './pages/About'
import PatientDashboard from './pages/patient/Dashboard'
import AssessmentPage from './pages/patient/AssessmentPage'
import HistoryPage from './pages/patient/HistoryPage'
import PredictionResult from './pages/patient/PredictionResult'
import AlertsPage from './pages/patient/AlertsPage'
import RecommendationsPage from './pages/patient/RecommendationsPage'
import PatientAnalyticsPage from './pages/patient/PatientAnalyticsPage'
import LifestyleAnalyzerPage from './pages/patient/LifestyleAnalyzerPage'
import ReportsPage from './pages/patient/ReportsPage'
import ReviewerDashboard from './pages/reviewer/ReviewerDashboard'
import ReviewQueue from './pages/reviewer/ReviewQueue'
import ReviewDetail from './pages/reviewer/ReviewDetail'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminAnalytics from './pages/admin/AdminAnalytics'
import ModelMonitoring from './pages/admin/ModelMonitoring'
import DataQuality from './pages/admin/DataQuality'
import SystemHealth from './pages/admin/SystemHealth'
import AuditLogs from './pages/admin/AuditLogs'
import UserManagement from './pages/admin/UserManagement'
import NotFoundPage from './pages/NotFound'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/about" element={<AboutPage />} />

        {/* Patient Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<PatientLayout />}>
            <Route path="/dashboard" element={<PatientDashboard />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/assessment/result" element={<PredictionResult />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
            <Route path="/analytics" element={<PatientAnalyticsPage />} />
            <Route path="/lifestyle" element={<LifestyleAnalyzerPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>
        </Route>

        {/* Reviewer Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<RoleRoute allowedRoles={['reviewer', 'admin']} />}>
            <Route element={<ReviewerLayout />}>
              <Route path="/reviewer" element={<ReviewerDashboard />} />
              <Route path="/reviewer/queue" element={<ReviewQueue />} />
              <Route path="/reviewer/assessment/:id" element={<ReviewDetail />} />
            </Route>
          </Route>
        </Route>

        {/* Admin Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<RoleRoute allowedRoles={['admin']} />}>
            <Route element={<AdminLayout />}>
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/analytics" element={<AdminAnalytics />} />
              <Route path="/admin/monitoring" element={<ModelMonitoring />} />
              <Route path="/admin/data-quality" element={<DataQuality />} />
              <Route path="/admin/health" element={<SystemHealth />} />
              <Route path="/admin/audit" element={<AuditLogs />} />
              <Route path="/admin/users" element={<UserManagement />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  )
}
