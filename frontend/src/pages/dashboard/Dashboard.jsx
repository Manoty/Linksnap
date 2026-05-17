
// Shows total stats, 14-day click trend chart, top links, recent activity.

import { useQuery }    from '@tanstack/react-query'
import { Link }        from 'react-router-dom'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { analyticsApi } from '../../api/analytics'
import { useAuth }      from '../../context/AuthContext'
import PageWrapper      from '../../components/layout/PageWrapper'
import StatCard         from '../../components/ui/StatCard'
import Badge            from '../../components/ui/Badge'
import Spinner          from '../../components/ui/Spinner'
import { formatDate, truncate } from '../../utils/format'

export default function Dashboard() {
  const { user } = useAuth()

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn:  () => analyticsApi.dashboard().then(r => r.data),
  })

  if (isLoading) return (
    <PageWrapper>
      <div className="flex justify-center mt-20"><Spinner size="lg" /></div>
    </PageWrapper>
  )

  if (error) return (
    <PageWrapper>
      <p className="text-red-400 text-center mt-20">Failed to load dashboard.</p>
    </PageWrapper>
  )

  // Normalize daily_trend so the chart always has a label
  const chartData = (data.daily_trend || []).map(d => ({
    day:    d.day,
    clicks: d.count,
  }))

  return (
    <PageWrapper>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''} 👋
        </h1>
        <p className="text-zinc-500 text-sm mt-1">Here's how your links are performing.</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Links"   value={data.total_links}  />
        <StatCard label="Active Links"  value={data.active_links} />
        <StatCard label="Total Clicks"  value={data.total_clicks} />
        <StatCard label="Clicks (7d)"   value={data.clicks_7d}   />
      </div>

      {/* Click trend chart */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-8">
        <h2 className="text-sm font-medium text-zinc-400 mb-6">Click trend — last 14 days</h2>
        {chartData.length === 0 ? (
          <p className="text-zinc-600 text-sm text-center py-10">
            No click data yet. Share a link to see activity here.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="clickGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#f97316" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0}   />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="day"
                tick={{ fill: '#71717a', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#71717a', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={30}
              />
              <Tooltip
                contentStyle={{
                  background: '#18181b',
                  border:     '1px solid #3f3f46',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '13px',
                }}
                labelStyle={{ color: '#a1a1aa' }}
              />
              <Area
                type="monotone"
                dataKey="clicks"
                stroke="#f97316"
                strokeWidth={2}
                fill="url(#clickGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top links */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-zinc-400">Top links</h2>
            <Link to="/links" className="text-xs text-orange-400 hover:text-orange-300">
              View all →
            </Link>
          </div>
          {data.top_links?.length === 0 ? (
            <p className="text-zinc-600 text-sm text-center py-8">No link activity yet.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {data.top_links?.map(link => (
                <Link
                  key={link.id}
                  to={`/analytics/${link.short_code}`}
                  className="flex items-center justify-between group"
                >
                  <div className="min-w-0">
                    <p className="text-sm text-orange-400 font-medium group-hover:text-orange-300">
                      /{link.short_code}
                    </p>
                    <p className="text-xs text-zinc-500 truncate">{truncate(link.original_url, 45)}</p>
                  </div>
                  <span className="text-sm font-semibold text-white ml-4 shrink-0">
                    {link.click_count}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Device split */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-sm font-medium text-zinc-400 mb-4">Device breakdown</h2>
          {data.device_split?.length === 0 ? (
            <p className="text-zinc-600 text-sm text-center py-8">No device data yet.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {data.device_split?.map(d => {
                const total = data.device_split.reduce((s, x) => s + x.count, 0)
                const pct   = total ? Math.round((d.count / total) * 100) : 0
                return (
                  <div key={d.device_type}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-zinc-300 capitalize">{d.device_type || 'unknown'}</span>
                      <span className="text-zinc-500">{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-orange-500 rounded-full transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}