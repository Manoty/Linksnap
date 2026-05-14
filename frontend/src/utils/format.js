// Formatting helpers used across pages.

export const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  })

export const formatDateTime = (iso) =>
  new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })

export const truncate = (str, n = 50) =>
  str?.length > n ? str.slice(0, n) + '…' : str

export const copyToClipboard = async (text) => {
  await navigator.clipboard.writeText(text)
}