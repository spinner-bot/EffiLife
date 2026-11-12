import { describe, it, expect } from 'vitest'
import { runInNewContext } from 'node:vm'
import { themes } from '../../src/ui/themes'
import { appearanceFor } from '../../src/ui/surface-effects'
import { assertAppearance, defaultAppearance } from '../../src/domain/appearance'
import { emptyWorkspace } from '../../src/domain/initial'
import { assertWorkspace } from '../../src/domain/validation'
import { execute } from '../../src/domain/engine'
import { builtinDecoration } from '../../src/extensions/builtin-decoration'
import { payloadBytes } from '../../src/extensions/manifest'

describe('material contracts and theme animation settings', () => {
  it('provides independent valid defaults for all themes and different parameter schemas', () => {
    for (const theme of themes.values()) {
      expect(theme.appearance, theme.slug).toBeDefined()
      expect(() => assertAppearance(theme.appearance, 'invalid')).not.toThrow()
      const draft = appearanceFor(theme); draft.animation.speed = 2
      expect(theme.appearance!.animation.speed).not.toBe(2)
    }
    expect(Object.keys(themes.get(1)!.appearance!.parameters)).toEqual(['radius', 'shadow'])
    expect(Object.keys(themes.get(6)!.appearance!.parameters)).toEqual(['opacity', 'blur', 'saturation'])
    expect(Object.keys(themes.get(8)!.appearance!.parameters)).toEqual(['opacity', 'blur', 'tint'])
  })
  it('rejects invalid effects and unbounded imported parameters, and recovery removes overrides', () => {
    const state = emptyWorkspace('3.1.0'), options = defaultAppearance()
    state.preferences.appearance = { '1': options }
    options.parameters.shadow = Infinity
    expect(() => assertWorkspace(state)).toThrow('storage.invalidWorkspace')
    options.parameters.shadow = .2; options.effect = 'unknown'
    expect(() => assertWorkspace(state)).toThrow('storage.invalidWorkspace')
    options.effect = 'solid'; options.animation.speed = 500
    expect(() => assertWorkspace(state)).toThrow('storage.invalidWorkspace')
    options.animation.speed = 1
    const recovered = execute(state, { operationId: 'recover', command: { type: 'recoverAppearance' } }, { now: new Date().toISOString(), id: () => 'id' }).workspace
    expect(recovered.preferences.appearance).toBeUndefined()
    expect(() => assertWorkspace(recovered)).not.toThrow()
  })
  it('scales actual renderer time and omits the sandbox when animation is disabled', async () => {
    const theme = { ...themes.get(1)!, decoration: { gradient: null, renderer: '(ctx,w,h,time) => ctx.fillRect(time,0,w,h)', particles: null } }
    const options = defaultAppearance(); options.animation.speed = .5
    const entry = (await builtinDecoration(theme, options))!
    const source = new TextDecoder().decode(payloadBytes(entry.payload, 'scripts/decoration.js'))
    let frame: (value: unknown) => void = () => {}
    runInNewContext(source, { EffiLife: { onFrame: (callback: typeof frame) => { frame = callback } } }, { timeout: 100 })
    const positions: number[] = []
    frame({ ctx: { fillRect: (x: number) => positions.push(x) }, width: 10, height: 10, time: 100 })
    expect(positions).toEqual([50])
    options.animation.enabled = false
    expect(await builtinDecoration(theme, options)).toBeUndefined()
  })
})
