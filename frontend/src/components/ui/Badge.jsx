// Status badge for link status fields.

const variants = {
  active:   'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  inactive: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  expired:  'bg-red-500/10 text-red-400 border-red-500/20',
}

export default function Badge({ status }) {
  return (
    <span className={`
      inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border
      ${variants[status] || variants.inactive}
    `}>
      {status}
    </span>
  )
}