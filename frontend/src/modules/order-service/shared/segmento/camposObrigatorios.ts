import { computed } from 'vue';

import type { SegmentField } from './segmentDefinition.type';
import { useOSFieldDefinition } from './useOSFieldDefinition.queries';
import { useTiposDeTrabalho } from './useTiposDeTrabalho';

/**
 * Exigência, NA TELA, dos campos obrigatórios do tipo de trabalho
 * (Spec 01B do lava-rápido, D6/D7).
 *
 * POR QUE NA TELA. No lava-rápido o backend aceita a placa vazia em qualquer
 * tipo — em branco, ele gera "VEI-2026-000042" (identificador
 * `gerado_se_vazio`, Spec 01A D5) — e o porte mora no JSON do objeto, que o
 * backend não confere. Sem esta guarda, um carro entraria sem placa (e viraria
 * um veículo novo a cada visita) e sem porte (e o preço por porte da Spec 02
 * não teria de onde sair).
 *
 * POR QUE SÓ ALI. Serigrafia e marcenaria também declaram campos obrigatórios
 * e já rodam em produção com o comportamento de hoje (asterisco, sem trava).
 * A guarda liga pelo contrato — `identificador.gerado_se_vazio` —, que é
 * justamente o caso em que o backend completa o vazio. Nenhum `if` por nome de
 * segmento.
 */

/** Chave da OS em que o tipo de trabalho escolhido fica gravado (igual à aba dinâmica). */
const CHAVE_TIPO = 'tipo_trabalho';

/** Os três lugares onde o valor de um campo pode morar. */
export interface ValoresDoFormulario {
  /** Colunas do objeto (marca, modelo, numero_serie...). */
  coluna: Record<string, unknown>;
  /** `dados_adicionais` do objeto (porte, carroceria...). */
  objeto: Record<string, unknown>;
  /** `dados_adicionais` da OS (pertences, tipo_trabalho...). */
  os: Record<string, unknown>;
}

/** Vazio para fins de exigência. `0` e `false` são respostas, não ausência. */
export function valorVazio(valor: unknown): boolean {
  if (valor === null || valor === undefined) return true;
  if (typeof valor === 'string') return valor.trim() === '';
  if (Array.isArray(valor)) return valor.length === 0;
  return false;
}

/**
 * Onde o valor do campo mora — o MESMO critério da `OSObjetoDinamicoTab`:
 * coluna real (a placa é `numero_serie`), senão o JSON da OS ou do objeto.
 */
function valorDoCampo(campo: SegmentField, valores: ValoresDoFormulario): unknown {
  if (campo.origem === 'coluna') return valores.coluna[campo.coluna ?? campo.nome];
  if (campo.escopo === 'os') return valores.os[campo.nome];
  return valores.objeto[campo.nome];
}

/** Rótulos dos campos obrigatórios que estão vazios, na ordem declarada. */
export function camposObrigatoriosVazios(
  campos: SegmentField[],
  valores: ValoresDoFormulario,
): string[] {
  return campos
    .filter((campo) => campo.obrigatorio && valorVazio(valorDoCampo(campo, valores)))
    .map((campo) => campo.label);
}

export function useCamposObrigatoriosDoTipo() {
  const { data } = useOSFieldDefinition();             // contrato do segmento (já em cache)
  const { tipoPadrao, camposDoTipo } = useTiposDeTrabalho();

  /** A guarda só existe onde o backend completa o identificador vazio (D6). */
  const exige = computed(() => !!data.value?.definicao?.identificador?.gerado_se_vazio);

  /**
   * O que falta preencher no formulário aberto. Vazio = pode salvar.
   *
   * @param coluna Dados do objeto que viram coluna (o `objetoFormData` do modal).
   * @param objetoDados `dados_adicionais` do objeto.
   * @param osDados `dados_adicionais` da OS (traz o tipo escolhido).
   */
  function faltando(
    coluna: object,
    objetoDados: Record<string, unknown>,
    osDados: Record<string, unknown>,
  ): string[] {
    if (!exige.value) return [];                                  // outros segmentos: como sempre
    const tipo = (osDados[CHAVE_TIPO] as string | undefined) ?? tipoPadrao.value;
    return camposObrigatoriosVazios(camposDoTipo(tipo), {
      coluna: coluna as Record<string, unknown>,
      objeto: objetoDados,
      os: osDados,
    });
  }

  return { faltando };
}
