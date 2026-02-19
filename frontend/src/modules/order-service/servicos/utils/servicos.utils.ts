export function toCents(value?: number): number | undefined {
  if (value === null || value === undefined) return undefined;
  return Math.round(value * 100);
}
