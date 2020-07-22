export const hash2path = (hash) => {
  return hash.replace(/^#/, '')
}

export const path2hash = (path) => {
  return `#${path}`
}

export const isHistoryMode = (options) => {
  const { mode = 'hash' } = options

  return mode === 'history'
}