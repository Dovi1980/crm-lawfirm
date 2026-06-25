import { useCallback, useRef, useState } from 'react'

/**
 * Streaming SSE consumer for /ai/* endpoints.
 *
 * Backend SSE frame format:
 *   data: {"text": "..."}\n\n     ← regular chunk
 *   event: error\ndata: {...}\n\n ← error
 *   data: [DONE]\n\n              ← terminator
 *
 * Calling `send` resets the streaming buffer; the consumer can read `streamingText`
 * to render the in-progress response, then handle completion via the `onChunk`
 * / `onDone` callbacks if it needs to commit it to a list.
 */
export function useAIStream({ onChunk, onDone, onError } = {}) {
  const [streamingText, setStreamingText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const send = useCallback(async (url, body) => {
    setStreamingText('')
    setError(null)
    setIsStreaming(true)
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    const token = localStorage.getItem('accessToken')
    const headers = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`

    let assembled = ''
    try {
      const resp = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        signal: abortRef.current.signal,
        headers,
        body: JSON.stringify(body),
      })
      if (!resp.ok) {
        const detail = await resp.text().catch(() => '')
        throw new Error(`HTTP ${resp.status}${detail ? `: ${detail}` : ''}`)
      }
      if (!resp.body) throw new Error('Stream no disponible')

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // SSE events are separated by blank lines (\n\n)
        let idx
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const rawEvent = buffer.slice(0, idx)
          buffer = buffer.slice(idx + 2)

          let eventType = 'message'
          const dataLines = []
          for (const line of rawEvent.split('\n')) {
            if (line.startsWith('event: ')) eventType = line.slice(7).trim()
            else if (line.startsWith('data: ')) dataLines.push(line.slice(6))
          }
          const data = dataLines.join('\n')
          if (!data) continue
          if (data === '[DONE]') continue

          if (eventType === 'error') {
            let detail = 'Error generando respuesta'
            try { detail = JSON.parse(data).detail || detail } catch {}
            throw new Error(detail)
          }

          try {
            const parsed = JSON.parse(data)
            if (parsed.text) {
              assembled += parsed.text
              setStreamingText(assembled)
              onChunk?.(parsed.text, assembled)
            }
          } catch {
            // ignore malformed frame
          }
        }
      }
      onDone?.(assembled)
    } catch (e) {
      if (e.name !== 'AbortError') {
        setError(e.message)
        onError?.(e)
      }
    } finally {
      setIsStreaming(false)
    }
  }, [onChunk, onDone, onError])

  const abort = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }, [])

  const reset = useCallback(() => {
    setStreamingText('')
    setError(null)
  }, [])

  return { streamingText, isStreaming, error, send, abort, reset }
}
