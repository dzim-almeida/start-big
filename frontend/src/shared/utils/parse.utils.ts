import type { ZodTypeAny } from 'zod';
import type z from 'zod';

/**
 * Parse seguro para respostas de API.
 * Valida com safeParse e retorna os dados validados em caso de sucesso.
 * Em caso de falha, loga o warning e retorna os dados brutos como fallback.
 *
 * Isso garante que divergências entre schema e backend não quebrem a UI,
 * enquanto os schemas são refinados progressivamente.
 */
export function safeParseResponse<T extends ZodTypeAny>(
  schema: T,
  data: unknown,
  context: string,
): z.infer<T> {
  const result = schema.safeParse(data);
  if (result.success) return result.data;

  if (import.meta.env.DEV) {
    console.warn(`[${context}] Zod validation warning:`, result.error.issues);
  }
  return data as z.infer<T>;
}
