import { describe, expect, it } from 'vitest'
import { buildChangedFields, mapChangeType } from './payload'

describe('buildChangedFields', () => {
  it('emits only changed fields as {old,new}', () => {
    const original = { Front: 'a', Back: 'b' }
    const edited = { Front: 'a2', Back: 'b' }
    expect(buildChangedFields(original, edited)).toEqual({
      Front: { old: 'a', new: 'a2' },
    })
  })

  it('treats a missing original side as empty', () => {
    expect(buildChangedFields({}, { Extra: 'novo' })).toEqual({
      Extra: { old: '', new: 'novo' },
    })
  })

  it('returns empty object when nothing changed', () => {
    expect(buildChangedFields({ Front: 'a' }, { Front: 'a' })).toEqual({})
  })
})

describe('mapChangeType', () => {
  it('maps known PT labels to enum values', () => {
    expect(mapChangeType('Ortografia/Gramática')).toBe('spelling/grammar')
    expect(mapChangeType('Erro de conteúdo')).toBe('content_error')
  })

  it('falls back to "other" for unknown labels', () => {
    expect(mapChangeType('algo desconhecido')).toBe('other')
  })
})
