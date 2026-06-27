export type FieldDiff = { old: string; new: string }

/**
 * O contrato `fields` do backend é genérico (`dict[str, Any]`). O add-on envia
 * `{ campo: { old, new } }`. Tolerante: aceita também `{ campo: "valor" }`
 * (só o sugerido) para clientes que não calculam o lado atual.
 */
export function normalizeFieldDiff(value: unknown): FieldDiff {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    const obj = value as Record<string, unknown>
    return {
      old: typeof obj.old === 'string' ? obj.old : '',
      new: typeof obj.new === 'string' ? obj.new : '',
    }
  }
  return { old: '', new: typeof value === 'string' ? value : '' }
}
