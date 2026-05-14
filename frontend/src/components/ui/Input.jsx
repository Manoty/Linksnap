// Reusable input with label and error state.

export default function Input({
  label, id, error, className = '', ...props
}) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-sm text-zinc-400">
          {label}
        </label>
      )}
      <input
        id={id}
        className={`
          w-full bg-zinc-900 border rounded-lg px-4 py-2.5 text-sm text-white
          placeholder-zinc-500 outline-none transition-colors
          ${error
            ? 'border-red-500/50 focus:border-red-500'
            : 'border-zinc-700 focus:border-orange-500'
          }
          ${className}
        `}
        {...props}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}