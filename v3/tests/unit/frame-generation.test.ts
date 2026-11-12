import { expect, it } from 'vitest'
import { frameFixture } from '../helpers/frame-fixture'

it.each([['LF', '\n'], ['CRLF', '\r\n'], ['CR', '\r']] as const)('checks and regenerates a %s checkout without changing its script hash', (_, eol) => {
  const fixture = frameFixture(eol)
  try {
    const source = fixture.read('public/extension-frame.js')
    const checked = fixture.run('--check')
    expect(fixture.read('public/extension-frame.js')).toBe(source)
    expect(fixture.run()).toBe(checked)
    expect(fixture.read('public/extension-frame.html')).not.toContain('\r')
    expect(fixture.read('apps/desktop/src-tauri/tauri.conf.json')).not.toContain('\r')
    expect(fixture.run('--check')).toBe(checked)
  } finally { fixture.dispose() }
})

it.each(['public/extension-frame.js', 'public/extension-frame.css'])('still rejects substantive changes to %s in a CRLF checkout', path => {
  const fixture = frameFixture('\r\n')
  try {
    fixture.run()
    fixture.write(path, fixture.read(path) + '\r\n/* changed source */\r\n')
    expect(() => fixture.run('--check')).toThrow(/sync:frame/)
    fixture.run()
    expect(() => fixture.run('--check')).not.toThrow()
  } finally { fixture.dispose() }
})
