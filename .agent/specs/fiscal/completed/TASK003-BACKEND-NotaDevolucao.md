# Especificação Técnica de Backend: NF-e de Devolução (Finalidade 4) via Focus NFe v2.0

* **Nome da Tarefa:** `feat(fiscal-backend): emissao de nfe de devolucao via focus nfe`
* **Camada:** Backend (FastAPI / SQLAlchemy / PostgreSQL / Focus NFe v2.0)
* **Objetivo:** Implementar o fluxo de emissão de NF-e (Modelo 55, Entrada `tipo_documento: 0`, Finalidade `4`) para devolução total ou parcial a partir de NF-e/NFC-e autorizada, respeitando os 4 pilares da SEFAZ/Focus NFe e prevenindo rejeições fiscais (267, 327, 539).

---

## 1. Regras Fiscais e Pilares Focus NFe v2.0

* **Endpoint Único:** A Focus NFe não possui rota dedicada a devoluções. Utilizar:
  `POST https://api.focusnfe.com.br/v2/nfe?ref={ref_unica}`.
* **Os 4 Pilares Compulsórios:**
  1. `finalidade_emissao: 4` (Devolução no XML).
  2. `notas_referenciadas: [{"chave_nfe": "<44_digitos>"}]` (Array de objetos com a chave original de 44 dígitos).
  3. `tipo_documento: 0` (Entrada) com CFOP correspondente de entrada (`1xxx` interna ou `2xxx` interestadual).
  4. `formas_pagamento: [{"forma_pagamento": "90", "valor_pagamento": 0.0}]` (Código 90 = Sem Pagamento, montante fixado em zero).

---

## 2. Modelagem de Dados (`app/db/models/documento_fiscal.py`)

### 2.1. Alterações Estruturais
* **Entidade `DocumentoFiscal`:**
  * `documento_referenciado_id`: FK para `documento_fiscal.id` (`ondelete="SET NULL"`, indexada, opcional).
  * `chave_documento_referenciado`: `String(44)` indexada, armazena a chave SEFAZ da nota devolvida.
  * `finalidade_emissao`: `Integer`, default `1` (1=Normal, 4=Devolução).
* **Entidade `DocumentoFiscalItem`:**
  * `quantidade_devolvida_acumulada`: `Integer`, default `0`, em milésimos (`1000 = 1.0 UN`), rastreia o total já devolvido do item.
* **Enum `MovimentacaoOrigem` (`app/core/enum.py`):**
  * Incluir entrada `DEVOLUCAO = "DEVOLUCAO"`.

### 2.2. Migração Alembic
* Script para adicionar colunas em lote:
  `alembic revision --autogenerate -m "add_campos_devolucao_documento_fiscal"`

---

## 3. Contratos de Entrada Pydantic (`app/schemas/emissao_fiscal.py`)

```python
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
import re

class ItemDevolucaoRequest(BaseModel):
    documento_item_id: int = Field(..., description="ID do DocumentoFiscalItem da nota original")
    quantidade: int = Field(..., gt=0, description="Quantidade a devolver em milésimos (ex: 1000 = 1.0 UN)")

class DestinatarioAvulsoRequest(BaseModel):
    cpf_ou_cnpj: str = Field(..., description="CPF (11) ou CNPJ (14) apenas números")
    nome_razao_social: str = Field(..., min_length=2, max_length=120)
    indicador_inscricao_estadual: int = Field(default=9, description="1=Contribuinte, 2=Isento, 9=Não Contribuinte")
    inscricao_estadual: Optional[str] = Field(None, max_length=20)
    logradouro: str = Field(..., min_length=2, max_length=120)
    numero: str = Field(..., min_length=1, max_length=20)
    bairro: str = Field(..., min_length=2, max_length=60)
    codigo_municipio: str = Field(..., min_length=7, max_length=7, description="Código IBGE 7 dígitos")
    municipio: str = Field(..., min_length=2, max_length=60)
    uf: str = Field(..., min_length=2, max_length=2)
    cep: str = Field(..., min_length=8, max_length=8, description="8 dígitos numéricos")

    @model_validator(mode="after")
    def sanitizar_e_validar(self):
        self.cpf_ou_cnpj = re.sub(r"\D", "", self.cpf_ou_cnpj)
        if len(self.cpf_ou_cnpj) not in (11, 14):
            raise ValueError("Documento deve ser CPF (11) ou CNPJ (14) válido.")
        self.cep = re.sub(r"\D", "", self.cep)
        if len(self.cep) != 8:
            raise ValueError("CEP deve conter 8 dígitos.")
        if self.indicador_inscricao_estadual == 1 and not self.inscricao_estadual:
            raise ValueError("Inscrição Estadual obrigatória para contribuinte (indicador=1).")
        return self

class EmissaoDevolucaoRequest(BaseModel):
    motivo: str = Field(..., min_length=15, max_length=255, description="Justificativa legal da devolução")
    devolver_estoque: bool = Field(default=True, description="Se True, dá entrada automática em estoque após autorização")
    itens: Optional[List[ItemDevolucaoRequest]] = Field(None, description="Itens parciais. Se omitido/vazio, devolve 100% dos saldos restantes.")
    destinatario_avulso: Optional[DestinatarioAvulsoRequest] = Field(None, description="Obrigatório caso a nota de origem não tenha CPF/CNPJ identificado.")
```

---

## 4. Regras de Derivação e Conversão Fiscal

### 4.1. Conversão de CFOP (`app/services/fiscal/derivacao/cfop.py`)
* **Mapa de Transformação Saída -> Entrada:**
  * Operação Interna: `5101 -> 1201`, `5102 -> 1202`, `5405 -> 1411`.
  * Operação Interestadual: `6101 -> 2201`, `6102 -> 2202`, `6403/6404 -> 2411`.
* **Regra de Fallback Contextual:**
  * Se o CFOP original não constar no mapa: aplicar fallback para `"2202"` se `is_interestadual` for True, caso contrário `"1202"`. Evita a Rejeição SEFAZ 327.

### 4.2. Recálculo Proporcional de Itens (`payload_builder.py`)
* Para cada item devolvido:
  * `fator_proporcao = Decimal(qtd_mil_devolver) / Decimal(item_origem.quantidade)`
  * `quantidade_comercial = Decimal(qtd_mil_devolver) / 1000`
  * `valor_bruto = round_abnt(quantidade_comercial * valor_unitario_original)`
  * **Espelhamento Tributário:** Bases de cálculo e valores nominais de ICMS, PIS e COFINS devem ser multiplicados por `fator_proporcao` com precisão decimal (`ROUND_HALF_UP`), mantendo CST/CSOSN e alíquotas originais.

---

## 5. Orquestração do Fluxo de Emissão (`app/services/fiscal/emissao.py`)

A função principal `emitir_devolucao(...)` deve seguir a seguinte esteira transacional:

1. **Validação de Pré-requisitos:**
   * Garantir que a nota de origem exista e esteja com `status == "AUTORIZADA"`.
   * Validar chave de acesso de origem (`len == 44` e numérica). Falha gera HTTP 422 (Prevenção Rejeição 267).
2. **Cálculo e Bloqueio de Saldos Remanescentes:**
   * `saldo_item = item.quantidade - item.quantidade_devolvida_acumulada`.
   * Se devolução parcial: validar se cada item pertence à nota e se `qtd_solicitada <= saldo_item`. Lançar HTTP 422 se exceder.
   * Se devolução total: coletar todos os itens com `saldo_item > 0`. Lançar HTTP 422 se a nota já estiver 100% devolvida.
3. **Resolução de Destinatário:**
   * Se a nota original tiver destinatário cadastrado: extrair dados fiscais.
   * Se anônima: exigir presença de `dados.destinatario_avulso`. Lançar HTTP 422 se ausente.
4. **Reserva Atômica de Numeração e Idempotência:**
   * Bloquear transacionalmente e incrementar o contador sequencial de NF-e da empresa (`numero_documento`).
   * Gerar referência única: `ref_api = f"devolucao-{doc_origem.id}-{uuid.uuid4().hex[:8]}"` (Prevenção Rejeição 539).
5. **Snapshot e Persistência Inicial:**
   * Montar o payload da Focus NFe (com `finalidade_emissao: 4`, `tipo_documento: 0`, `forma_pagamento: "90"`, `valor_pagamento: 0.0`).
   * Salvar entidade `DocumentoFiscal` com `status="PROCESSANDO"`, chave referenciada e snapshot do JSON montado.
   * Executar `db.commit()` antes da chamada HTTP externa para assegurar a reserva do número em caso de timeout de rede.
6. **Disparo e Tratamento Assíncrono:**
   * Executar chamada à API da Focus NFe (`client.emitir_nfe(ref, payload)`).
   * Atualizar `status`, `chave_acesso` e `protocolo`.
   * **Controle de Estoque e Saldos:**
     * Se retorno imediato `AUTORIZADA`: incrementar `quantidade_devolvida_acumulada` nos itens originais e disparar entrada no estoque (caso `devolver_estoque=True`).
     * Se retorno `PROCESSANDO`: manter registro em processamento. O incremento de saldo e a entrada em estoque ficam delegados ao webhook/worker de consulta de autorização.

---

## 6. Critérios de Aceite e Testes (Pytest)

Criar `test/services/fiscal/test_emissao_devolucao.py` com cenários:
1. **Conformidade do Payload:** Validação de `modelo: 55`, `tipo_documento: 0`, `finalidade_emissao: 4`, forma 90 zerada e array `notas_referenciadas`.
2. **Conversão de CFOP e Interestadualidade:** Vendas `5102 -> 1202`, `5405 -> 1411` e interestadual `6102 -> 2202`.
3. **Trava de Quantidade Excedente:** Rejeição com HTTP 422 ao tentar devolver saldo superior ao remanescente da venda.
4. **Devoluções Parciais Consecutivas:** Sucesso em duas devoluções de 50% e bloqueio com HTTP 422 na terceira tentativa (saldo zerado).
5. **NFC-e Anônima:** HTTP 422 na ausência de `destinatario_avulso`; sucesso após fornecimento dos dados completos.
6. **Idempotência e Reserva:** Numeração consumida e commitada mesmo se houver falha de rede na comunicação com a SEFAZ.
---

## Desvios aplicados na implementação (2026-09-17)
Ver `.agent/docs/progress/TASK003-BACKEND.md` e `ADR-002`. Resumo:
- Serviço em `app/services/fiscal/devolucao.py` (não em `emissao.py`).
- Tributos pelo tax_engine sobre o snapshot congelado (não `fator_proporcao`).
- Coluna extra `DocumentoFiscal.devolver_estoque`; migration manual idempotente (SQLite, não PostgreSQL/autogenerate).
- Testes: `test/services/fiscal/test_emissao_devolucao.py` (33), `test/api/v1/fiscal/test_devolucao_api.py`, `test/db/test_migracao_campos_devolucao.py`.
