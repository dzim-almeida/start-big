export const SALE_STATUS = [
    {value: 'RASCUNHO', label: 'Rascunho'},
    {value: 'CONCLUIDA', label: 'Concluída'},
    {value: 'CANCELADA', label: 'Cancelada'},
]

export const PRODUCT_TYPES = [
    {value: 'CADASTRADO', label: 'Cadastrado'},
    {value: 'AVULSO', label: 'Avulso'},
] as const;

export const PAYMENT_METHODS = [
    {value: 'DINHEIRO', label: 'Dinheiro'},
    {value: 'CARTAO_CREDITO', label: 'Cartão de Crédito'},
    {value: 'CARTAO_DEBITO', label: 'Cartão de Débito'},
    {value: 'PIX', label: 'Pix'},
    {value: 'BOLETO', label: 'Boleto'},
] as const;