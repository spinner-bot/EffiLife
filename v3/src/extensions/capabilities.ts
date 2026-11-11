export const capabilities = {
  'appearance.tokens': { level: 0, writes: false },
  'resources.register': { level: 0, writes: false },
  'appearance.css': { level: 1, writes: false },
  'overlay.canvas': { level: 2, writes: false },
  'overlay.interactive': { level: 2, writes: false },
  'app.layout': { level: 3, writes: false },
  'app.navigation': { level: 3, writes: false },
  'app.settings.read': { level: 3, writes: false },
  'app.settings.write': { level: 3, writes: true },
  'app.data.read': { level: 3, writes: false },
  'app.data.write': { level: 3, writes: true },
  'app.theme': { level: 3, writes: true },
  'app.events': { level: 3, writes: false },
} as const
export type Capability = keyof typeof capabilities
export function isCapability(value: unknown): value is Capability {
  return typeof value === 'string' && Object.hasOwn(capabilities, value)
}
export function defaultGrants(requested: readonly Capability[]): Capability[] {
  return requested.filter(value => capabilities[value].level === 0)
}
export function effectiveCapabilities(requested: readonly Capability[], grants: readonly string[], policy: readonly Capability[] = Object.keys(capabilities) as Capability[]): Capability[] {
  return requested.filter(value => grants.includes(value) && policy.includes(value))
}

