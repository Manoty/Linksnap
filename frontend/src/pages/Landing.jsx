// frontend/src/pages/Landing.jsx
// Public landing page. Shows the URL shortener form + brand.
// No auth required. Anonymous users can shorten from here.

import { useState } from 'react'

export default function Landing() {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleShorten = async () => {
    if (!url) return
    setLoading(true)
    // Phase 3 will wire this to the real API
    setTimeout(() => {
      setResult({ short_url: 'https://qejani.io/aZ91x', original_url: url })
      setLoading(false)
    }, 800)
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white font-sans">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-zinc-800">
        <span className="text-xl font-bold tracking-tight text-orange-400">qejani</span>
        <div className="flex gap-4 text-sm text-zinc-400">
          <a href="/login" className="hover:text-white transition-colors">Sign in</a>
          <a href="/register" className="bg-orange-500 hover:bg-orange-400 text-white px-4 py-1.5 rounded-md transition-colors">
            Get started
          </a>
        </div>
      </nav>

      {/* Hero */}
      <main className="max-w-2xl mx-auto px-6 pt-28 pb-20 text-center">
        <h1 className="text-5xl font-bold leading-tight tracking-tight text-white mb-4">
          Short links.<br />
          <span className="text-orange-400">Big reach.</span>
        </h1>
        <p className="text-zinc-400 text-lg mb-12">
          Create, manage, and track your links. Built for teams and makers.
        </p>

        {/* Shorten form */}
        <div className="flex gap-2 bg-zinc-900 border border-zinc-700 rounded-xl p-2">
          <input
            type="url"
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder="Paste a long URL here..."
            className="flex-1 bg-transparent px-4 py-3 text-sm text-white placeholder-zinc-500 outline-none"
          />
          <button
            onClick={handleShorten}
            disabled={loading}
            className="bg-orange-500 hover:bg-orange-400 disabled:opacity-50 text-white text-sm font-medium px-6 py-3 rounded-lg transition-colors"
          >
            {loading ? 'Shortening...' : 'Shorten'}
          </button>
        </div>

        {/* Result */}
        {result && (
          <div className="mt-6 bg-zinc-900 border border-zinc-700 rounded-xl p-5 text-left">
            <p className="text-xs text-zinc-500 mb-1">Your short link</p>
            <div className="flex items-center justify-between">
              <span className="text-orange-400 font-medium">{result.short_url}</span>
              <button
                onClick={() => navigator.clipboard.writeText(result.short_url)}
                className="text-xs text-zinc-400 hover:text-white border border-zinc-600 px-3 py-1.5 rounded-md transition-colors"
              >
                Copy
              </button>
            </div>
            <p className="text-xs text-zinc-600 mt-2 truncate">{result.original_url}</p>
          </div>
        )}
      </main>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-6 pb-24 grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { icon: '⚡', title: 'Instant', desc: 'Links generated in milliseconds with Base62 encoding.' },
          { icon: '📊', title: 'Analytics', desc: 'Track clicks, traffic sources, and link performance.' },
          { icon: '🔒', title: 'Managed', desc: 'Set expiry dates, deactivate links, custom aliases.' },
        ].map(f => (
          <div key={f.title} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="text-2xl mb-3">{f.icon}</div>
            <h3 className="font-semibold text-white mb-1">{f.title}</h3>
            <p className="text-sm text-zinc-400">{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  )
}