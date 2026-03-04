import z from 'zod';

export const EmployeeReadSchema = z.object({
  id: z.number().int().positive(),
  nome: z.string().max(255, 'O nome do funcionário deve ter no máximo 255 caracteres'),
});

export type EmployeeReadSchemaDataType = z.infer<typeof EmployeeReadSchema>;
