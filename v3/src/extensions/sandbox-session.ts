import { workerPrelude } from './worker-prelude'
import type { Capability } from './capabilities'
import type { SandboxRequest } from '../application/sandbox-bridge'

export interface SandboxOptions {
  source: string
  capabilities: Capability[]
  title: string
  theme: Record<string, string>
  request(request: SandboxRequest): Promise<unknown>
  failure(code: string): void
  ready?(): void
}
export class SandboxSession {
  readonly frame = document.createElement('iframe')
  private readonly channel = new MessageChannel()
  private readonly observer: ResizeObserver
  private disposed = false
  private connected = false
  private lastHeartbeat = Date.now()
  private watchdog: ReturnType<typeof setInterval>
  private count = 0
  private windowStart = 0
  private readonly motionQuery = matchMedia('(prefers-reduced-motion: reduce)')
  constructor(private readonly container: HTMLElement, private readonly options: SandboxOptions) {
    const frame = this.frame
    frame.title = options.title
    frame.setAttribute('sandbox', 'allow-scripts')
    frame.setAttribute('referrerpolicy', 'no-referrer')
    frame.setAttribute('allow', "camera 'none'; microphone 'none'; geolocation 'none'; clipboard-read 'none'; clipboard-write 'none'")
    frame.className = 'extension-frame'
    frame.src = new URL('./extension-frame.html', document.baseURI).href
    frame.onload = () => {
      if (!this.connected && !this.disposed) { this.connected = true; frame.contentWindow?.postMessage('effilife-connect', '*', [this.channel.port2]) }
    }
    this.channel.port1.onmessage = event => { this.receive(event.data) }
    this.channel.port1.start()
    container.append(frame)
    this.observer = new ResizeObserver(() => this.update())
    this.observer.observe(container)
    document.addEventListener('visibilitychange', this.visibility)
    this.motionQuery.addEventListener('change', this.motion)
    if (options.capabilities.includes('overlay.interactive')) window.addEventListener('pointermove', this.pointer, { passive: true })
    this.watchdog = setInterval(() => {
      if (!document.hidden && Date.now() - this.lastHeartbeat > 15000) this.fail('extensions.scriptTimeout')
    }, 1000)
  }
  private send(value: unknown) { if (!this.disposed) this.channel.port1.postMessage(value) }
  private state() {
    const rect = this.container.getBoundingClientRect()
    return { width: Math.max(1, rect.width), height: Math.max(1, rect.height), dpr: Math.min(2, devicePixelRatio || 1), visible: !document.hidden, reducedMotion: this.motionQuery.matches, theme: this.options.theme }
  }
  update(theme?: Record<string, string>) {
    if (theme) this.options.theme = theme
    this.send({ type: 'update', state: this.state() })
  }
  private visibility = () => { this.lastHeartbeat = Date.now(); this.update() }
  private motion = () => this.update()
  private pointer = (event: PointerEvent) => {
    const rect = this.container.getBoundingClientRect()
    this.send({ type: 'action', action: { type: 'pointer', x: event.clientX - rect.left, y: event.clientY - rect.top } })
  }
  private async receive(value: unknown) {
    if (this.disposed || !value || typeof value !== 'object') return
    const message = value as Record<string, unknown>
    if (message.type === 'connected') this.send({ type: 'init', source: workerPrelude + '\n' + this.options.source, capabilities: this.options.capabilities, state: this.state() })
    else if (message.type === 'heartbeat' || message.type === 'ready') {
      this.lastHeartbeat = Date.now()
      if (message.type === 'ready') { this.frame.dataset.ready = 'true'; this.options.ready?.() }
    } else if (message.type === 'failure') this.fail(typeof message.code === 'string' ? message.code : 'extensions.scriptFailed')
    else if (message.type === 'request') {
      if (Date.now() - this.windowStart > 1000) { this.windowStart = Date.now(); this.count = 0 }
      if (++this.count > 20) { this.fail('extensions.requestLimit'); return }
      const request = message.request as SandboxRequest
      if (!request || typeof request.id !== 'string') { this.fail('extensions.invalidRequest'); return }
      try {
        const result = await this.options.request(request)
        this.send({ type: 'response', id: request.id, result })
      } catch (failure) {
        const code = failure && typeof failure === 'object' && 'code' in failure ? String(failure.code) : 'extensions.invalidRequest'
        this.send({ type: 'response', id: request.id, error: code })
      }
    }
  }
  private fail(code: string) {
    if (this.disposed) return
    this.dispose()
    this.options.failure(code)
  }
  dispose() {
    if (this.disposed) return
    this.send({ type: 'dispose' })
    this.disposed = true
    clearInterval(this.watchdog)
    this.observer.disconnect()
    document.removeEventListener('visibilitychange', this.visibility)
    this.motionQuery.removeEventListener('change', this.motion)
    window.removeEventListener('pointermove', this.pointer)
    this.channel.port1.close()
    this.frame.remove()
  }
}

