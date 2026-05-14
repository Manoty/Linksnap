// Reusable button. Variants: primary, secondary, danger, ghost.

export default function Button({
  children, onClick, type = 'button',
  variant = 'primary', disabled = false, className = '', size = 'md'
}) {
  const base = 'inline-flex items-center justify-center font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed'

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-sm',
  }

  const variants = {
    primary:   'bg-orange-500 hover:bg-orange-400 text-white',
    secondary: 'bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700',
    danger:    'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30',
    ghost:     'hover:bg-zinc-800 text-zinc-400 hover:text-white',
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  )
}