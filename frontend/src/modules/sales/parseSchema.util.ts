import { ZodSchema } from 'zod';

export function parseSchema<T>(schema: ZodSchema<T>, data: unknown, context?: string): T {
  const result = schema.safeParse(data);

  if (!result.success) {
    console.error(
      `[Schema Validation Error] Context: ${context ?? 'Unknown'}`,
      result.error.flatten(),
    );

    throw new Error(`Invalid API response schema${context ? ` in ${context}` : ''}`);
  }

  return result.data;
}
