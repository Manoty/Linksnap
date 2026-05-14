// pages/auth/Register.jsx

import { useState }          from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth }           from '../../context/AuthContext'
import Button                from '../../components/ui/Button'
import Input                 from '../../components/ui/Input'

export default function Register() {
  const { register } = useAuth()
  const navigate     = useNavigate()
  const [form, setForm]     = useState({ email: '', password: '', full_name: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form.email, form.password, form.full_name)
      navigate('/dashboard')
    } catch (err) {
      const data = err.response?.data
      const msg  = data?.detail || data?.email?.[0] || data?.password?.[0] || 'Registration failed.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Link to="/" className="text-2xl font-bold text-orange-400">qejani</Link>
          <p className="text-zinc-400 text-sm mt-2">Create your free account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 flex flex-col gap-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <Input
            label="Full name"
            id="full_name"
            type="text"
            placeholder="Jane Smith"
            value={form.full_name}
            onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
          />

          <Input
            label="Email"
            id="email"
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
            required
          />

          <Input
            label="Password"
            id="password"
            type="password"
            placeholder="Min 8 characters"
            value={form.password}
            onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
            required
          />

          <Button type="submit" disabled={loading} size="lg" className="mt-2 w-full">
            {loading ? 'Creating account...' : 'Create account'}
          </Button>

          <p className="text-center text-sm text-zinc-500">
            Already have an account?{' '}
            <Link to="/login" className="text-orange-400 hover:text-orange-300">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}