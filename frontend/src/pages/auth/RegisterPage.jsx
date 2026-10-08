import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Heart, Eye, EyeOff } from 'lucide-react'
import Button from '../../components/common/Button'
import Input from '../../components/common/Input'
import { formatApiError } from '../../utils/errors'

export default function RegisterPage() {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { register } = useAuth()
  const navigate = useNavigate()

  const validate = () => {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Name is required'
    if (!form.email.trim()) errs.email = 'Email is required'
    if (form.password.length < 8) {
      errs.password = 'Password must be at least 8 characters'
    } else if (!/[a-zA-Z]/.test(form.password) || !/[0-9]/.test(form.password)) {
      errs.password = 'Password must contain at least one letter and one number'
    }
    if (form.password !== form.confirmPassword) errs.confirmPassword = 'Passwords do not match'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!validate()) return
    setLoading(true)
    try {
      await register({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        confirm_password: form.confirmPassword,
        confirmPassword: form.confirmPassword,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(formatApiError(err, 'Registration failed'))
    } finally {
      setLoading(false)
    }
  }

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 px-6">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex items-center justify-center gap-2 mb-6">
          <div className="p-2 bg-red-600 rounded-lg">
            <Heart className="h-6 w-6 text-white" />
          </div>
          <span className="text-2xl font-bold text-slate-900">HeartGuard</span>
        </div>
        <h2 className="text-center text-2xl font-bold text-slate-900">Create your account</h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          Already have an account?{' '}
          <Link to="/login" className="text-red-600 hover:text-red-700 font-medium">Sign in</Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm rounded-xl border border-slate-200">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
                {error}
              </div>
            )}
            <Input
              label="Full name"
              value={form.name}
              onChange={update('name')}
              placeholder="John Doe"
              error={errors.name}
              required
            />
            <Input
              label="Email address"
              type="email"
              value={form.email}
              onChange={update('email')}
              placeholder="you@example.com"
              error={errors.email}
              required
            />
            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={update('password')}
                placeholder="Min. 8 characters"
                error={errors.password}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-8 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <Input
              label="Confirm password"
              type={showPassword ? 'text' : 'password'}
              value={form.confirmPassword}
              onChange={update('confirmPassword')}
              placeholder="Re-enter password"
              error={errors.confirmPassword}
              required
            />
            <Button type="submit" loading={loading} className="w-full">
              Create Account
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
