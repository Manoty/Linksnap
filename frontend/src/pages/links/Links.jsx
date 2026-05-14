// pages/links/Links.jsx
// Create, copy, deactivate, delete links. Full CRUD UI.

import { useState }    from 'react'
import { Link }        from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { linksApi }    from '../../api/links'
import PageWrapper     from '../../components/layout/PageWrapper'
import Button          from '../../components/ui/Button'
import Input           from '../../components/ui/Input'
import Badge           from '../../components/ui/Badge'
import Spinner         from '../../components/ui/Spinner'
import { formatDate, truncate, copyToClipboard } from '../../utils/format'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function CreateLinkForm({ onSuccess }) {
  const [url, setUrl]         = useState('')
  const [alias, setAlias]     = useState('')
  const [error, setError]     = useState('')
  const [copied, setCopied]   = useState(false)

  const mutation = useMutation({
    mutationFn: () => linksApi.create({
      original_url:  url,
      custom_alias:  alias || undefined,
    }),
    onSuccess: () => {
      setUrl(''); setAlias(''); setError('')
      onSuccess()
    },
    onError: (err) => {
      const data = err.response?.data
      setError(data?.detail || data?.original_url?.[0] || 'Failed to create link.')
    },
  })

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-8">
      <h2 className="text-sm font-medium text-zinc-300 mb-4">Shorten a new URL</h2>
      <div className="flex flex-col sm:flex-row gap-3">
        <Input
          placeholder="https://your-long-url.com/..."
          value={url}
          onChange={e => setUrl(e.target.value)}
          className="flex-1"
          error={error}
        />
        <Input
          placeholder="custom-alias (optional)"
          value={alias}
          onChange={e => setAlias(e.target.value)}
          className="sm:w-48"
        />
        <Button
          onClick={() => mutation.mutate()}
          disabled={!url || mutation.isPending}
          className="shrink-0"
        >
          {mutation.isPending ? 'Creating...' : 'Create link'}
        </Button>
      </div>
    </div>
  )
}

function LinkRow({ link, onDelete, onToggle }) {
  const [copied, setCopied] = useState(false)
  const shortUrl = `${BASE_URL}/r/${link.short_code}/`

  const handleCopy = async () => {
    await copyToClipboard(shortUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-3 py-4 border-b border-zinc-800 last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-orange-400 font-medium text-sm">/{link.short_code}</span>
          <Badge status={link.status} />
        </div>
        <p className="text-xs text-zinc-500 truncate">{truncate(link.original_url, 60)}</p>
        <p className="text-xs text-zinc-600 mt-0.5">{formatDate(link.created_at)} · {link.click_count} clicks</p>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <Button size="sm" variant="ghost" onClick={handleCopy}>
          {copied ? '✓ Copied' : 'Copy'}
        </Button>
        <Link to={`/analytics/${link.short_code}`}>
          <Button size="sm" variant="ghost">Stats</Button>
        </Link>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onToggle(link)}
        >
          {link.status === 'active' ? 'Deactivate' : 'Activate'}
        </Button>
        <Button size="sm" variant="danger" onClick={() => onDelete(link)}>
          Delete
        </Button>
      </div>
    </div>
  )
}

export default function Links() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState('')

  const { data: links = [], isLoading } = useQuery({
    queryKey: ['links'],
    queryFn:  () => linksApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (shortCode) => linksApi.delete(shortCode),
    onSuccess:  () => queryClient.invalidateQueries({ queryKey: ['links'] }),
  })

  const toggleMutation = useMutation({
    mutationFn: (link) => linksApi.update(link.short_code, {
      status: link.status === 'active' ? 'inactive' : 'active',
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['links'] }),
  })

  const filtered = links.filter(l =>
    !filter ||
    l.short_code.includes(filter) ||
    l.original_url.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <PageWrapper>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">My Links</h1>
        <p className="text-zinc-500 text-sm mt-1">Manage and track all your shortened URLs.</p>
      </div>

      <CreateLinkForm onSuccess={() => queryClient.invalidateQueries({ queryKey: ['links'] })} />

      {/* Filter */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-zinc-500">{links.length} link{links.length !== 1 ? 's' : ''}</p>
        <Input
          placeholder="Filter links..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="w-48 py-1.5 text-xs"
        />
      </div>

      {/* Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl px-6">
        {isLoading ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : filtered.length === 0 ? (
          <p className="text-zinc-600 text-sm text-center py-16">
            {filter ? 'No links match your filter.' : 'No links yet. Create one above.'}
          </p>
        ) : (
          filtered.map(link => (
            <LinkRow
              key={link.id}
              link={link}
              onDelete={l  => {
                if (confirm(`Delete /${l.short_code}? This cannot be undone.`))
                  deleteMutation.mutate(l.short_code)
              }}
              onToggle={l  => toggleMutation.mutate(l)}
            />
          ))
        )}
      </div>
    </PageWrapper>
  )
}