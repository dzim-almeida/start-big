import z from "zod";

export const GenderTypeEnum = z.enum([
    'MASCULINO',
    'FEMININO',
    'OUTRO'
])