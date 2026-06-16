/**
 * @fileoverview Gerador ESC/POS do cupom de Ordem de Serviço
 * @description Espelha o conteúdo do OSPrintCupom.vue (entrada/saída) em
 * comandos ESC/POS para impressão térmica direta (silenciosa).
 */

import { EscPosBuilder } from '@/shared/services/escpos'
import { formatCurrency } from '@/shared/utils/finance'
import {
  getClienteNome,
  getClienteDoc,
  getClientePhone,
  getPaymentDisplayName,
  formatPrintDate,
  formatPrintDoc,
} from '@/shared/utils/print.utils'
import type { Bobina } from '@/shared/services/escpos'
import type { CompanyPrintInfo } from '@/shared/components/print/print.types'
import type { OrderServiceReadDataType } from '../schemas/orderServiceQuery.schema'

export interface OsEscPosOptions {
  bobina: Bobina
  empresa: CompanyPrintInfo
}

export function osToEscPos(
  os: OrderServiceReadDataType,
  tipo: 'ENTRADA' | 'SAIDA',
  opts: OsEscPosOptions,
): Uint8Array {
  const b = new EscPosBuilder(opts.bobina)
  const { empresa } = opts

  const situacao = os.situacao_equipamento ?? null
  const isSemReparo = situacao === 'SEM_REPARO' || situacao === 'CONDENADO'

  const titulo =
    tipo === 'ENTRADA'
      ? 'COMPROVANTE DE ENTRADA'
      : situacao === 'SEM_REPARO'
        ? 'ENTREGA SEM REPARO'
        : situacao === 'CONDENADO'
          ? 'EQUIPAMENTO CONDENADO'
          : 'RECIBO E GARANTIA'

  const dataStr = tipo === 'SAIDA' ? ((os.data_finalizacao as string) || os.data_criacao) : os.data_criacao

  // Cabeçalho da empresa
  b.alinhar('centro')
    .tamanhoDuplo(true)
    .linha(empresa.nome.toUpperCase())
    .tamanhoDuplo(false)
  if (empresa.cnpj) b.linha(empresa.cnpj)
  if (empresa.enderecoLinha1) b.linha(empresa.enderecoLinha1)
  if (empresa.enderecoLinha2) b.linha(empresa.enderecoLinha2)
  if (empresa.contato) b.linha(`TEL: ${empresa.contato}`)

  b.separador().negrito(true).linha(titulo).negrito(false).separador()

  // Identificação
  b.alinhar('esq')
    .negrito(true)
    .linha(`OS: ${os.numero_os}`)
    .negrito(false)
    .linha(`Data: ${formatPrintDate(dataStr)}`)
    .separador()

  // Cliente
  b.negrito(true).linha('CLIENTE').negrito(false)
  b.linha(getClienteNome(os.cliente))
  const doc = getClienteDoc(os.cliente)
  if (doc) b.linha(`Doc: ${formatPrintDoc(doc)}`)
  const tel = getClientePhone(os.cliente)
  if (tel) b.linha(`Tel: ${tel}`)
  b.separador()

  // Equipamento
  b.negrito(true).linha('EQUIPAMENTO').negrito(false)
  const sufixoSituacao =
    tipo === 'SAIDA' && situacao
      ? ` (${situacao === 'REPARADO' ? 'Reparado' : situacao === 'SEM_REPARO' ? 'Sem Reparo' : 'Condenado'})`
      : ''
  b.linha(`${os.equipamento.tipo_equipamento}${sufixoSituacao}`)
  if (os.equipamento.marca) b.linha(`Marca: ${os.equipamento.marca}`)
  if (os.equipamento.modelo) b.linha(`Modelo: ${os.equipamento.modelo}`)
  if (os.equipamento.numero_serie) b.linha(`N/S: ${os.equipamento.numero_serie}`)
  if (os.equipamento.cor) b.linha(`Cor: ${os.equipamento.cor}`)
  b.separador()

  // Defeito relatado
  b.negrito(true).linha('DEFEITO RELATADO').negrito(false).linha(os.defeito_relatado)

  // Observações
  if (os.observacoes) {
    b.separador().negrito(true).linha('OBSERVACOES').negrito(false).linha(os.observacoes)
  }

  if (tipo === 'SAIDA') {
    // Laudo técnico
    if (os.diagnostico || os.solucao) {
      b.separador().negrito(true).linha('LAUDO TECNICO').negrito(false)
      if (os.diagnostico) b.linha(`Diag: ${os.diagnostico}`)
      if (os.solucao) b.linha(`Solucao: ${os.solucao}`)
    }

    // Itens/serviços
    if (os.itens?.length) {
      b.separador().negrito(true).linha('ITENS/SERVICOS').negrito(false)
      for (const item of os.itens) {
        b.linha(item.nome)
        b.parLados(`${item.quantidade}x ${formatCurrency(item.valor_unitario)}`, formatCurrency(item.valor_total))
      }
    }

    const subTotal = os.itens?.reduce((acc, item) => acc + item.valor_total, 0) ?? 0
    const adiantamento = os.valor_entrada ?? 0
    const adiantamentoUtilizado = Math.min(adiantamento, os.valor_total ?? 0)
    const paymentTotal = os.pagamentos?.reduce((acc, pay) => acc + pay.valor, 0) ?? 0
    const totalRecebido = adiantamentoUtilizado + paymentTotal

    // Adiantamento
    if (adiantamento > 0) {
      b.separador().negrito(true).linha('ADIANTAMENTO (ENTRADA)').negrito(false)
      b.parLados('Recebido na entrada:', formatCurrency(adiantamento))
    }

    // Pagamentos no fechamento
    if (os.pagamentos?.length) {
      b.separador().negrito(true).linha('PAGAMENTOS').negrito(false)
      for (const pgto of os.pagamentos) {
        const nome = getPaymentDisplayName(pgto.forma_pagamento?.nome || 'Pagamento')
        const parcelas = pgto.parcelas > 1 ? ` (${pgto.parcelas}x)` : ''
        b.parLados(`${nome}${parcelas}`, formatCurrency(pgto.valor))
      }
    }

    // Totais
    b.separador()
    b.parLados('Subtotal:', formatCurrency(subTotal))
    if ((os.desconto ?? 0) > 0) b.parLados('Desconto:', `-${formatCurrency(os.desconto ?? 0)}`)
    if ((os.taxa_entrega ?? 0) > 0) b.parLados('Deslocamento:', `+${formatCurrency(os.taxa_entrega ?? 0)}`)
    if ((os.acrescimo ?? 0) > 0) b.parLados('Juros:', `+${formatCurrency(os.acrescimo ?? 0)}`)
    if (adiantamento > 0) b.parLados('Adiantamento:', `-${formatCurrency(adiantamentoUtilizado)}`)
    b.negrito(true).parLados('TOTAL PAGO:', formatCurrency(totalRecebido)).negrito(false)

    // Garantia / sem reparo
    if (!isSemReparo && os.garantia) {
      b.separador().negrito(true).linha(`GARANTIA: ${os.garantia}`).negrito(false)
      b.linha('Cobre servicos prestados e pecas substituidas neste documento. Nao cobre mau uso, liquidos, quedas ou intervencao de terceiros.')
    } else if (isSemReparo) {
      b.separador().linha('Equipamento devolvido sem reparo. Sem garantia aplicavel a esta OS.')
    }
  } else {
    // ENTRADA: termos
    b.separador()
    b.linha('O cliente declara estar ciente que a empresa nao se responsabiliza por perda de dados nem por chips/cartoes deixados no aparelho. Autorizo a analise tecnica do equipamento.')
    b.separador()
    b.linha('PRAZO DE RETIRADA: Equipamentos nao retirados em 90 dias apos aviso de conclusao serao considerados abandonados, conforme Art. 1.275 do Codigo Civil Brasileiro.')
  }

  // Assinaturas
  b.pular(3)
    .alinhar('centro')
    .linha('_'.repeat(Math.min(28, b.colunas - 4)))
    .linha('Assinatura do Cliente')

  // Rodapé
  b.separador()
    .linha(new Date().toLocaleString('pt-BR'))
    .negrito(true)
    .linha('SISTEMA STARTBIG')
    .negrito(false)

  b.cortar()
  return b.build()
}
