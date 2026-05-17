// Per-link analytics: total clicks, device chart, daily trend, recent events.

import { useParams, Link }  from 'react-router-dom'
import { useQuery }         from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts'
import { analyticsApi }  from '../../api/analytics'
import PageWrapper       from '../../components/layout/PageWrapper'
import StatCard          from '../../components/ui/StatCard'
import Badge             from '../../components/ui/Badge'
import Spinner           from '../../components/ui/Spinner'
import { formatDateTime, truncate } from '../../utils/format'

const DEVICE_COLORS = {
  desktop: '#f97316',
  mobile:  '#3b82f6',
  tablet:  '#8b5cf6',
  bot:     '#6b7280',
}

export default function LinkAnalytics() {
  const { shortCode } = useParams()

  const { data, isLoading, error } = useQuery({
    queryKey: ['linkStats', shortCode],
    queryFn:  () => analyticsApi.linkStats(shortCode).then(r => r.data),
  })

  if (isLoading) return (
    <PageWrapper>
      <div className="flex justify-center mt-20"><Spinner size="lg" /></div>
    </PageWrapper>
  )

  if (error) return (
    <PageWrapper>
      <p className="text-red-400 text-center mt-20">Failed to load analytics.</p>
    </PageWrapper>
  )

  const dailyData   = (data.daily_clicks || []).map(d => ({ day: d.day, clicks: d.count }))
  const deviceData  = (data.device_breakdown || []).map(d => ({
    name:   d.device_type || 'unknown',
    clicks: d.count,
  }))

  return (
    <PageWrapper>
      {/* Header */}
      <div className="mb-8">
        <Link to="/links" className="text-xs text-zinc-500 hover:text-zinc-300 mb-3 inline-block">
          ← Back to links
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white">/{shortCode}</h1>
        </div>
        <p className="text-zinc-500 text-sm mt-1 truncate">{data.original_url || ''}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <StatCard label="Total Clicks"  value={data.total_clicks} />
        <StatCard label="Top Referrers" value={data.top_referrers?.length || 0} sub="unique sources" />
        <StatCard label="Devices"       value={deviceData.length} sub="device types seen" />
      </div>

      {/* Daily trend */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
        <h2 className="text-sm font-medium text-zinc-400 mb-6">Daily clicks — last 30 days</h2>
        {dailyData.length === 0 ? (
          <p className="text-zinc-600 text-sm text-center py-10">No click data in the last 30 days.</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={dailyData}>
              <XAxis
                dataKey="day"
                tick={{ fill: '#71717a', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#71717a', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                width={25}
              />
              <Tooltip
                contentStyle={{
                  background: '#18181b',
                  border:     '1px solid #3f3f46',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                labelStyle={{ color: '#a1a1aa' }}
              />
              <Bar dataKey="clicks" fill="#f97316" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device breakdown */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-sm font-medium text-zinc-400 mb-4">Device breakdown</h2>
          {deviceData.length === 0 ? (
            <p className="text-zinc-600 text-sm text-center py-8">No device data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={deviceData} layout="vertical">
                <XAxis type="number" tick={{ fill: '#71717a', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 12 }} axisLine={false} tickLine={false} width={60} />
                <Tooltip
                  contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="clicks" radius={[0, 3, 3, 0]}>
                  {deviceData.map(d => (
                    <Cell key={d.name} fill={DEVICE_COLORS[d.name] || '#6b7280'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Recent clicks */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-sm font-medium text-zinc-400 mb-4">Recent clicks</h2>
          {data.recent_clicks?.length === 0 ? (
            <p className="text-zinc-600 text-sm text-center py-8">No clicks recorded yet.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {data.recent_clicks?.map((click, i) => (
                <div key={i} className="flex items-start justify-between gap-2 text-xs">
                  <div>
                    <span className="text-zinc-300 capitalize">{click.device_type || 'unknown'}</span>
                    {click.referrer && (
                      <span className="text-zinc-600 ml-2 truncate block max-w-xs">
                        via {truncate(click.referrer, 35)}
                      </span>
                    )}
                  </div>
                  <span className="text-zinc-600 shrink-0">{formatDateTime(click.clicked_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}