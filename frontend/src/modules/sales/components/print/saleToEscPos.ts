/**
 * @fileoverview Gerador ESC/POS do cupom de venda
 * @description Espelha o conteúdo do SalePrintCupom.vue em comandos ESC/POS
 * para impressão térmica direta (silenciosa).
 */

import { EscPosBuilder } from '@/shared/services/escpos'
import { formatCurrency } from '@/shared/utils/finance'
import {
  getClienteNome,
  getClienteDoc,
  getClientePhone,
  formatPrintDate,
  formatPrintDoc,
} from '@/shared/utils/print.utils'
import type { Bobina } from '@/shared/services/escpos'
import type { CompanyPrintInfo } from '@/shared/components/print/print.types'
import type { SaleRead } from '../../schemas/sale.schema'

export interface SaleEscPosOptions {
  bobina: Bobina
  empresa: CompanyPrintInfo
  resolverPagamento?: (id: number) => string
  abrirGaveta?: boolean
}

export function saleToEscPos(sale: SaleRead, opts: SaleEscPosOptions): Uint8Array {
  const b = new EscPosBuilder(opts.bobina)
  const { empresa } = opts

  // Cabeçalho da empresa
  b.alinhar('centro')
    .tamanhoDuplo(true)
    .linha(empresa.nome.toUpperCase())
    .tamanhoDuplo(false)
  if (empresa.cnpj) b.linha(empresa.cnpj)
  if (empresa.enderecoLinha1) b.linha(empresa.enderecoLinha1)
  if (empresa.enderecoLinha2) b.linha(empresa.enderecoLinha2)
  if (empresa.contato) b.linha(`TEL: ${empresa.contato}`)

  b.separador()
    .negrito(true)
    .linha('COMPROVANTE DE VENDA')
    .negrito(false)
    .separador()

  // Identificação
  const numero = String(sale.numero_venda ?? sale.id ?? 0).padStart(6, '0')
  b.alinhar('esq')
    .negrito(true)
    .linha(`VENDA: ${numero}`)
    .negrito(false)
    .linha(`Data: ${formatPrintDate(sale.criado_em)}`)
    .separador()

  // Cliente
  b.negrito(true).linha('CLIENTE').negrito(false)
  b.linha(getClienteNome(sale.cliente as any))
  const doc = getClienteDoc(sale.cliente as any)
  if (doc) b.linha(`Doc: ${formatPrintDoc(doc)}`)
  const tel = getClientePhone(sale.cliente as any)
  if (tel) b.linha(`Tel: ${tel}`)
  b.separador()

  // Itens
  if (sale.produtos?.length) {
    b.negrito(true).linha('ITENS').negrito(false)
    for (const item of sale.produtos) {
      b.linha(item.nome)
      b.parLados(`${item.quantidade}x ${formatCurrency(item.valor_unitario)}`, formatCurrency(item.total))
      if (item.desconto > 0) b.parLados('Desc:', `-${formatCurrency(item.desconto)}`)
    }
    b.separador()
  }

  // Pagamentos
  if (sale.pagamentos?.length) {
    b.negrito(true).linha('PAGAMENTOS').negrito(false)
    for (const pgto of sale.pagamentos) {
      const nome = opts.resolverPagamento?.(pgto.forma_pagamento_id) ?? 'Pagamento'
      const parcelas = pgto.parcelado && pgto.qtd_parcelas ? ` (${pgto.qtd_parcelas}x)` : ''
      b.parLados(`${nome}${parcelas}`, formatCurrency(pgto.valor))
    }
    b.separador()
  }

  // Totais
  const totalPago = sale.pagamentos?.reduce((acc, pg) => acc + pg.valor, 0) ?? 0
  b.parLados('Subtotal:', formatCurrency(sale.subtotal))
  if (sale.descontos > 0) b.parLados('Desconto:', `-${formatCurrency(sale.descontos)}`)
  if (sale.entrega > 0) b.parLados('Entrega:', `+${formatCurrency(sale.entrega)}`)
  b.negrito(true).parLados('TOTAL:', formatCurrency(sale.total)).negrito(false)
  b.parLados('Total Pago:', formatCurrency(totalPago))
  if (sale.troco > 0) b.parLados('Troco:', formatCurrency(sale.troco))

  // Observações
  if (sale.observacao) {
    b.separador().negrito(true).linha('OBSERVACOES').negrito(false).linha(sale.observacao)
  }

  // Assinaturas — as duas, como na via em papel (lá são blocos empilhados, não
  // colunas, então cabem na bobina). Antes só existia a do cliente, e sem o
  // nome embaixo da linha: mesma venda, dois comprovantes diferentes.
  const linhaAssinatura = '_'.repeat(Math.min(28, b.colunas - 4))
  b.pular(2)
    .alinhar('centro')
    .linha(linhaAssinatura)
    .negrito(true)
    .linha('Vendedor')
    .negrito(false)
    .pular(2)
    .linha(linhaAssinatura)
    .negrito(true)
    .linha('Assinatura do Cliente')
    .negrito(false)
  if (sale.cliente) b.linha(getClienteNome(sale.cliente))

  // Rodapé
  b.separador()
    .linha(new Date().toLocaleString('pt-BR'))
    .negrito(true)
    .linha('SISTEMA STARTBIG')
    .negrito(false)

  if (opts.abrirGaveta) b.pulsoGaveta()
  b.cortar()
  return b.build()
}
