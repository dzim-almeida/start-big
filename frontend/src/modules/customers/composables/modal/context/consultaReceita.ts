import { ref } from 'vue';

import type { AddressFormData } from '@/modules/customers/schemas/customer.schema';
import { getAllCustomers } from '@/modules/customers/services/customerGet.service';
import { ConsultaCnpjErro, buscarDadosCNPJ } from '@/shared/services/cnpj.service';
import { formatCEP, formatTelefone } from '@/shared/utils/document.utils';

import { DEFAULT_ADDRESS } from '../constants/modal.constant';
import type { CustomerPJFormReturn } from '../form/useCustomerPJ.form';

/**
 * Consulta do CNPJ do cliente PJ na Receita (Spec 02 da marcenaria).
 *
 * Saiu de dentro do `useCustomerFormProvider` para poder ser testada sozinha.
 * O PREENCHIMENTO é o mesmo de antes, linha por linha (R15-CNPJ): razão social,
 * fantasia, regime (MEI/Simples, quando a Receita afirma), contato só se vazio
 * e o PRIMEIRO endereço. O que esta versão acrescenta:
 *   1. avisa cliente DUPLICADO antes de consultar a Receita (D4);
 *   2. diz POR QUE falhou: "não encontrado" × "indisponível" (D1, D6);
 *   3. descarta resposta ATRASADA se o CNPJ do campo mudou no meio (D7).
 */

/** Aviso que fica fixo abaixo do campo CNPJ (só o de duplicidade precisa ficar visível, D6). */
export type AvisoCnpj = { tipo: 'duplicado'; nomeCliente: string } | null;

/** O que a consulta precisa do mundo de fora (injetado para poder testar). */
export interface DependenciasConsultaReceita {
  /** Formulário PJ: lê os valores atuais e grava o que veio da Receita. */
  pjForm: Pick<CustomerPJFormReturn, 'values' | 'setValues'>;
  /** Id do cliente aberto em edição (ele nunca é "duplicado" de si mesmo). */
  idEmEdicao: () => number | undefined;
  /** Toasts do sistema (useToast). */
  toast: {
    success: (mensagem: string, descricao?: string) => void;
    error: (mensagem: string, descricao?: string) => void;
  };
}

/** Só os dígitos de um CNPJ (com ou sem máscara). */
const soDigitos = (valor: string | null | undefined) => (valor ?? '').replace(/\D/g, '');

export function criarConsultaReceita({ pjForm, idEmEdicao, toast }: DependenciasConsultaReceita) {
  const isConsultingCNPJ = ref(false);         // consulta em andamento (a tela mostra "Consultando...")
  const avisoCnpj = ref<AvisoCnpj>(null);      // aviso fixo de duplicidade
  let consultaAtual = '';                      // CNPJ da consulta em andamento (D7)

  /** Dígitos do CNPJ que está no campo AGORA (pode ter mudado durante a consulta). */
  const cnpjAtual = () => soDigitos(pjForm.values.cnpj);

  /** Some com o aviso: o usuário mudou o CNPJ, ou o modal fechou. */
  function limparAvisoCnpj() {
    avisoCnpj.value = null;
  }

  /** Grava no formulário o que veio da Receita. IGUAL ao código de antes (D9). */
  function preencher(dados: Awaited<ReturnType<typeof buscarDadosCNPJ>>) {
    const atual = pjForm.values;
    const [primeiro, ...demais] = (atual.enderecos?.length ? atual.enderecos : [{ ...DEFAULT_ADDRESS }]) as AddressFormData[];

    pjForm.setValues({
      razao_social: dados.razao_social || atual.razao_social,
      // Fantasia é obrigatória no formulário; muita empresa não tem na Receita.
      nome_fantasia: dados.nome_fantasia || atual.nome_fantasia || dados.razao_social,
      regime_tributario: dados.regime_tributario || atual.regime_tributario,
      email: atual.email || dados.email,
      telefone: atual.telefone || (dados.telefone ? formatTelefone(dados.telefone) : ''),
      enderecos: [
        {
          ...primeiro,
          cep: dados.cep ? formatCEP(dados.cep) : primeiro.cep,
          logradouro: dados.logradouro || primeiro.logradouro,
          numero: dados.numero || primeiro.numero,
          complemento: dados.complemento || primeiro.complemento,
          bairro: dados.bairro || primeiro.bairro,
          cidade: dados.cidade || primeiro.cidade,
          estado: dados.estado || primeiro.estado,
        },
        ...demais,
      ],
    }, false);
  }

  async function consultarReceita(cnpjDigitos: string) {
    if (isConsultingCNPJ.value) return;        // regra de sempre: uma consulta por vez
    isConsultingCNPJ.value = true;
    consultaAtual = cnpjDigitos;               // marca qual CNPJ está sendo consultado
    avisoCnpj.value = null;                    // começa limpo
    try {
      // 1) Duplicidade (D4). Falha da busca não impede seguir (D5): o backend
      //    continua barrando o duplicado com 409 ao salvar.
      const pagina = await getAllCustomers({ search: cnpjDigitos, limit: 5 }).catch(() => null);
      if (cnpjAtual() !== consultaAtual) return;                 // o usuário mudou o CNPJ: descarta (D7)
      const outro = pagina?.items.find(
        (c) => 'cnpj' in c                                       // só cliente PJ tem CNPJ
          && soDigitos(c.cnpj) === cnpjDigitos                   // CNPJ EXATO, não "contém"
          && c.id !== idEmEdicao(),                              // nunca o próprio cliente
      );
      if (outro && 'razao_social' in outro) {
        avisoCnpj.value = { tipo: 'duplicado', nomeCliente: outro.razao_social ?? '' };
        return;                                                  // não consulta nem preenche
      }

      // 2) Receita.
      const dados = await buscarDadosCNPJ(cnpjDigitos);
      if (cnpjAtual() !== consultaAtual) return;                 // resposta atrasada (D7)
      preencher(dados);
      toast.success('Dados da Receita Federal preenchidos. Confira e informe a Inscrição Estadual, se o cliente tiver.');
    } catch (erro) {
      if (cnpjAtual() !== consultaAtual) return;                 // erro de uma consulta velha: ignora
      // Erro que não é da consulta (bug, por exemplo) conta como indisponível:
      // nunca afirmar "não encontrado" sem a Receita ter dito isso.
      const motivo = erro instanceof ConsultaCnpjErro ? erro.motivo : 'INDISPONIVEL';
      if (motivo === 'NAO_ENCONTRADO') {
        toast.error('CNPJ não encontrado na Receita Federal.');  // texto de sempre
      } else {
        toast.error('Não foi possível consultar a Receita agora.', 'Preencha manualmente ou tente de novo.');
      }
    } finally {
      isConsultingCNPJ.value = false;
    }
  }

  return { isConsultingCNPJ, avisoCnpj, consultarReceita, limparAvisoCnpj };
}
