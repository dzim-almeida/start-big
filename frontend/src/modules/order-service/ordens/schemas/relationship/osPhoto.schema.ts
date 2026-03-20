import z from "zod";

export const OsImageReadSchema = z.object({
    id: z.number().int().positive(),
    ordem_servico_id: z.number().int().positive(),
    nome_arquivo: z.string(),
    url: z.string(),
    data_criacao: z.string(),
})

export type OsImageReadDataType = z.infer<typeof OsImageReadSchema>