# Especificação Técnica de Frontend: NF-e de Devolução (Finalidade 4)

* **Nome da Tarefa:** `feat(fiscal-frontend): modal e acoes de emissao de devolucao no centro fiscal`
* **Camada:** Frontend (Vue 3 / TypeScript / TanStack Vue Query / Tailwind CSS)
* **Objetivo:** Implementar o fluxo de emissão de NF-e de Devolução a partir do Centro Fiscal para notas autorizadas, provendo controle de saldo por item, resolução cadastral para documentos anônimos, tratamento da janela de cancelamento SEFAZ e sincronização reativa de cache.

---

## 1. Regras de Negócio e Comportamento de UX

### 1.1. Janela Legal SEFAZ vs. Devolução (`FiscalDocumentoDetailsDrawer.vue`)
* **Regra de Tempo:**
  * **NFC-e (Modelo 65):** Janela de cancelamento de **30 minutos** calculada a partir de `data_autorizacao` (fallback: `data_emissao`).
  * **NF-e (Modelo 55):** Janela de cancelamento de **24 horas (1440 minutos)**.
* **Estados de Ação no Drawer:**
  1. **Nota 100% Devolvida:** Se todos os itens já tiverem `quantidade_devolvida_acumulada >= quantidade`, ocultar ações de devolução e exibir badge informativo.
  2. **Dentro do Prazo Legal:** Exibir botão secundário `Cancelar Nota` (abre fluxo de cancelamento) e botão neutro `Devolver Itens` (abre modal de devolução).
  3. **Fora do Prazo Legal (Expirado):** Ocultar/desabilitar botão de cancelamento, exibir alerta contextual informando a expiração do prazo legal SEFAZ e destacar `Emitir NF-e de Devolução` como ação principal.

---

### 1.2. Máquina de Estados do Modal (`FiscalEmitirDevolucaoModal.vue`)
* **Modo de Devolução:**
  * `TOTAL` (padrão): Considera 100% do saldo remanescente (`quantidade - quantidade_devolvida_acumulada`) de todos os itens disponíveis.
  * `PARCIAL`: Habilita seleção manual por checkbox e ajuste de quantidade via input numérico por linha.
* **Controle de Quantidade e Saldo:**
  * Quantidades transitam no backend em milésimos inteiros (`1000 = 1.0 UN`).
  * No modo `PARCIAL`, cada linha deve validar: `1 <= quantidade_input <= saldo_remanescente`. Não permitir valores negativos, nulos ou que excedam o saldo faturado.
* **Resolução de Destinatário (Remetente da Devolução):**
  * Se o documento de origem possuir `destinatario_dados` com CPF ou CNPJ: exibir resumo somente-leitura dos dados.
  * Se o documento for anônimo (ex: NFC-e sem CPF): exibir seção de formulário obrigatória para identificação avulsa. O preenchimento do CEP deve disparar lookup automático (ViaCEP) preenchendo logradouro, bairro, município, UF e código IBGE de 7 dígitos.
* **Critérios de Habilitação do Botão de Envio:**
  * Justificativa preenchida com no mínimo 15 e no máximo 255 caracteres.
  * Pelo menos um item selecionado com quantidade a devolver maior que zero.
  * Se remetente avulso for exigido: CPF/CNPJ válido (11 ou 14 dígitos), CEP com 8 dígitos, código IBGE com 7 dígitos e endereço completo preenchidos.
  * Mutação não pode estar em estado de loading (`isPending`).

---

## 2. Contratos de Tipagem (`app/modules/fiscal/types/fiscal.types.ts`)

```typescript
export interface ItemDevolucaoPayload {
  documento_item_id: number;
  quantidade: number; // Inteiro em milésimos (ex: 1000 = 1.0 UN)
}

export interface DestinatarioAvulsoPayload {
  cpf_ou_cnpj: string; // Apenas dígitos (11 ou 14)
  nome_razao_social: string;
  indicador_inscricao_estadual: 1 | 2 | 9; // 1=Contribuinte, 2=Isento, 9=Não Contribuinte
  inscricao_estadual?: string | null;
  logradouro: string;
  numero: string;
  bairro: string;
  codigo_municipio: string; // 7 dígitos IBGE
  municipio: string;
  uf: string; // Sigla com 2 caracteres
  cep: string; // 8 dígitos
}

export interface EmissaoDevolucaoPayload {
  motivo: string;
  devolver_estoque: boolean;
  itens?: ItemDevolucaoPayload[] | null; // null/omitido quando devolução total
  destinatario_avulso?: DestinatarioAvulsoPayload | null;
}

export interface DocumentoFiscalItem {
  id: number;
  documento_fiscal_id: number;
  codigo_produto: string;
  descricao: string;
  codigo_ncm: string;
  cfop: string;
  unidade_comercial: string;
  quantidade: number; // Em milésimos
  quantidade_devolvida_acumulada?: number; // Em milésimos
  valor_unitario: number;
  valor_bruto: number;
}

export interface DocumentoFiscalHistoricoItem {
  id: number;
  empresa_id: number;
  tipo_documento: 'NFE' | 'NFCE';
  modelo: number; // 55 ou 65
  numero_documento: number;
  serie: number;
  chave_acesso?: string | null;
  status: 'PROCESSANDO' | 'AUTORIZADA' | 'REJEITADA' | 'CANCELADA';
  data_emissao: string;
  data_autorizacao?: string | null;
  valor_total: number;
  finalidade_emissao?: number;
  documento_referenciado_id?: number | null;
  destinatario_dados?: {
    cpf?: string;
    cnpj?: string;
    nome_razao_social?: string;
    logradouro?: string;
    numero?: string;
    bairro?: string;
    codigo_municipio?: string;
    municipio?: string;
    uf?: string;
    cep?: string;
    indicador_inscricao_estadual?: number;
    inscricao_estadual?: string;
  } | null;
  itens?: DocumentoFiscalItem[];
}
```

---

## 3. Serviços e Integração HTTP (`app/modules/fiscal/services/fiscal.service.ts`)

* Implementar método `emitirDevolucao(documentoId: number, payload: EmissaoDevolucaoPayload)`:
  * Dispara `POST /fiscal/documentos/{documentoId}/devolucao`.
  * Retorna o `DocumentoFiscalHistoricoItem` gerado.
* Implementar método auxiliar de resolução de CEP `buscarCep(cep: string)` consumindo a API ViaCEP (`https://viacep.com.br/ws/{cep}/json/`) retornando logradouro, bairro, localidade, uf e ibge.

---

## 4. Gerenciamento de Estado Reativo (TanStack Vue Query)

* **Composable:** `app/modules/fiscal/composables/useFiscalDevolucaoMutation.ts`
* **Contrato da Mutação:**
  * `mutationFn`: invoca `fiscalService.emitirDevolucao`.
  * `onSuccess`:
    * Notifica sucesso via Toast (distinguindo se autorizada imediatamente ou em processamento).
    * Invalida as queries de listagem e resumo: `fiscalKeys.documentos()`, `fiscalKeys.resumo()`.
    * Invalida a query do documento de origem referenciado para atualizar o saldo disponível dos itens em tela.
  * `onError`: extrai mensagem detalhada retornada pelo backend (`error.response.data.detail`) e exibe Toast de erro.

---

## 5. Especificação dos Componentes

### 5.1. `FiscalDocumentoDetailsDrawer.vue` (Ajustes de Ação)
* **Lógica Computada:**
  * `isTotalmenteDevolvida`: verifica se todos os itens da nota possuem `quantidade_devolvida_acumulada >= quantidade`.
  * `prazoCancelamentoExpirado`: compara a diferença entre a data atual e a data de autorização contra os limites (30 minutos se `NFCE`, 1440 minutos se `NFE`).
* **Renderização:**
  * Se `isTotalmenteDevolvida`: exibe aviso estático de esgotamento de saldo.
  * Se `prazoCancelamentoExpirado`: renderiza banner informativo de expiração e botão prioritário para disparar a abertura do modal de devolução.
  * Caso contrário: renderiza botão de cancelamento e botão de devolução lado a lado.

---

### 5.2. `FiscalEmitirDevolucaoModal.vue` (Modal de Emissão)
* **Props:**
  * `isOpen: boolean`
  * `documento: DocumentoFiscalHistoricoItem`
* **Emits:**
  * `(e: 'close'): void`
  * `(e: 'sucesso', novoDocumentoId: number): void`
* **Estrutura de Estado e Dados:**
  * `modoDevolucao`: ref com valores `'TOTAL' | 'PARCIAL'` (default `'TOTAL'`).
  * `itensLocais`: lista reativa derivada de `documento.itens` com:
    * `saldoDisponivelMil = max(0, quantidade - quantidade_devolvida_acumulada)`.
    * `qtdDevolverMil`: inicializado com o saldo disponível.
    * `selecionado`: boolean.
  * `destAvulso`: objeto contendo os campos de `DestinatarioAvulsoPayload`.
  * `motivo`: string vinculada ao textarea.
  * `devolverEstoque`: boolean (default `true`).
* **Cálculos Reativos:**
  * `temDestinatarioOrigem`: valida se `documento.destinatario_dados` possui CPF ou CNPJ.
  * `valorTotalEstimado`: soma proporcional (`(qtdDevolverMil / 1000) * valor_unitario`) dos itens selecionados.
  * `formularioValido`: invariante booleana cobrindo tamanho do motivo (>= 15), seleção de itens válidos e validação cadastral do destinatário avulso se exigido.
* **Submissão (`handleSubmit`):**
  * Se `modoDevolucao === 'PARCIAL'`, mapeia apenas os itens marcados para o array `itens`. Se `TOTAL`, envia `itens: null` para devolução global pelo backend.
  * Sanitiza CPF/CNPJ e CEP removendo caracteres não numéricos antes do disparo.
  * Aciona a mutação, emite evento de sucesso e fecha o modal.

---

## 6. Critérios de Aceite

1. **Expiração do Cancelamento SEFAZ:** Notas autorizadas há mais de 30 min (NFC-e) ou 24h (NF-e) devem bloquear o cancelamento e exibir o fluxo de devolução como alternativa.
2. **Respeito aos Saldos Restantes:** Na devolução parcial, o operador não pode informar quantidade superior ao saldo restante do item (`quantidade - quantidade_devolvida_acumulada`).
3. **NFC-e Anônima:** Se a nota referenciada não possuir cliente identificado, os campos de endereço e documento tornam-se de preenchimento obrigatório e integrados ao ViaCEP.
4. **Validação Mínima de Motivo:** O envio não pode ser acionado com justificativa inferior a 15 caracteres.
5. **Invalidação de Cache:** A autorização da devolução deve atualizar imediatamente o status no Centro Fiscal sem necessidade de reload de página.
6. **Integridade de Tipos:** Validação sem erros com `vue-tsc --noEmit`.
---

## Desvios aplicados na implementação (2026-09-17)
Ver `.agent/docs/progress/TASK003-FRONTEND.md`. Resumo:
- ViaCEP reaproveitado de `shared/services/cep.service.ts` (tipo ganhou `ibge`).
- Tipos existentes (`DocumentoFiscalRead`, `DocumentoItemResumo`) estendidos em vez de novos.
- Lógica pura em `composables/useDevolucaoItens.ts` com 10 testes Vitest.
- Pista de destinatário = `destinatario_id`, com fallback pelo código `DESTINATARIO_OBRIGATORIO` do backend.
