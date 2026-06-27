import { describe, expect, it } from 'vitest'
import { normalizeFieldDiff } from './diff'

describe('normalizeFieldDiff', () => {
  it('reads {old,new} objects', () => {
    expect(normalizeFieldDiff({ old: 'a', new: 'b' })).toEqual({ old: 'a', new: 'b' })
  })

  it('treats a bare string as suggested-only', () => {
    expect(normalizeFieldDiff('b')).toEqual({ old: '', new: 'b' })
  })

  it('defaults missing or non-string sides to empty', () => {
    expect(normalizeFieldDiff({ new: 'b' })).toEqual({ old: '', new: 'b' })
    expect(normalizeFieldDiff(null)).toEqual({ old: '', new: '' })
    expect(normalizeFieldDiff(42)).toEqual({ old: '', new: '' })
  })
})
