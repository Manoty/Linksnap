// Consistent page shell for all authenticated pages.

import Navbar from './Navbar'

export default function PageWrapper({ children }) {
  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <Navbar />
      <main className="max-w-6xl mx-auto px-6 py-10">
        {children}
      </main>
    </div>
  )
}