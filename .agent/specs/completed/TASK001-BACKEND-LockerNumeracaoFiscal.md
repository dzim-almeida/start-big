# Especificação Técnica: Backend — Locker de Confirmação de Numeração e Série Fiscal

## 1. Metadados da Tarefa
- **Identificador / Branch:** `feat(fiscal-backend): locker e validacao de confirmacao da numeracao fiscal`
- **Camada:** Backend (`FastAPI` / `SQLAlchemy 2.0` / `Alembic` / `Pydantic v2`)
- **Severidade:** Alta (Prevenção direta de Rejeição SEFAZ 204 — Duplicidade de Nota)

---

## 2. Objetivo e Justificativa
Impedir que qualquer documento fiscal (NF-e modelo 55 ou NFC-e modelo 65) seja emitido antes que o operador ou técnico de implantação confirme formalmente a série e o último número emitido no sistema.

Essa trava elimina o problema crítico de emitir a nota fiscal número 1 para empresas que já emitiam documentos em outro ERP, o que gera inconsistência contábil e rejeição imediata na SEFAZ.

---

## 3. Detalhamento Técnico da Implementação

### 3.1. Banco de Dados e Modelagem (SQLAlchemy 2.0)
- **Arquivo:** `backend-fastapi/app/db/models/empresa_fiscal_settings.py`
- **Campo a adicionar:**
```python
numeracao_confirmada: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    server_default=sa.text("false"),
    nullable=False,
    doc="Indica se o operador/implantador confirmou formalmente a série e o último número emitido"
)
```

### 3.2. Migration (Alembic)
- **Diretório:** `backend-fastapi/alembic/versions/`
- **Operações na migration:**
  1. `op.add_column('empresa_fiscal_settings', sa.Column('numeracao_confirmada', sa.Boolean(), server_default=sa.text('false'), nullable=False))`
  2. **Data Migration (Legados):** Para clientes já ativos na base, marcar como confirmado caso já tenham histórico de notas autorizadas:
  ```python
  op.execute("""
      UPDATE empresa_fiscal_settings
      SET numeracao_confirmada = true
      WHERE empresa_id IN (
          SELECT DISTINCT empresa_id 
          FROM notas_fiscais 
          WHERE status = 'AUTORIZADA'
      )
  """)
  ```

### 3.3. Schemas Pydantic (Pydantic v2)
- **Arquivo:** `backend-fastapi/app/schemas/empresa.py`
  - Em `FiscalSettingsBase`:
    ```python
    numeracao_confirmada: bool = False
    ```
  - Em `FiscalSettingsUpdate`:
    ```python
    numeracao_confirmada: Optional[bool] = None
    ```
- **Arquivo:** `backend-fastapi/app/schemas/emissao_fiscal.py`
  - Em `FiscalConfiguracao`:
    ```python
    numeracao_confirmada: bool = False
    ```

### 3.4. Serviços e Endpoints
- **Arquivo:** `backend-fastapi/app/services/empresa.py` (`update_fiscal_settings`):
  - Ao processar `FiscalSettingsUpdate`:
    - Se `data.numeracao_confirmada is True`, persistir `settings.numeracao_confirmada = True`.
    - **Regra de Auto-confirmação:** Se o payload atualizar explicitamente qualquer um dos campos (`serie_nfe`, `ultimo_numero_nfe`, `serie_nfce`, `ultimo_numero_nfce`), setar automaticamente `settings.numeracao_confirmada = True`.
- **Arquivo:** `backend-fastapi/app/api/v1/endpoints/fiscal.py`:
  - `GET /configuracao`: Mapear `numeracao_confirmada=fs.numeracao_confirmada if fs else False`.
  - `PUT /configuracao`: Garantir retorno do objeto `FiscalConfiguracao` com o estado booleano atualizado.

### 3.5. Gate de Validação Fiscal (O Locker)
- **Arquivo:** `backend-fastapi/app/services/fiscal/validators.py`:
  - Na função `verificar_emitente(db: Session, empresa_id: int)`:
    - Inspecionar `fiscal_settings.numeracao_confirmada`.
    - Se for `False`, injetar pendência cadastral impeditiva:
      ```python
      if not fiscal_settings.numeracao_confirmada:
          pendencias.append(_p(
              "configuracao",
              "numeracao_confirmada",
              "Série e numeração de notas ainda não foram confirmadas. "
              "Acesse Centro Fiscal > Configurações > Emissão Estadual e confirme a sequência inicial."
          ))
      ```
- **Arquivo:** `backend-fastapi/app/services/pendencias_globais.py`:
  - Como `obter_pendencias_globais` consome `verificar_emitente`, a falta de confirmação passará a ser exibida automaticamente no painel de pendências fiscais globais do dashboard.

---

## 4. Critérios de Aceite e Validações

1. **Bloqueio Efetivo (Gate):** 
   - Ao chamar a emissão fiscal com `numeracao_confirmada == False`, a requisição deve ser interrompida com HTTP 422 ou erro de validação cadastral.
   - Nenhuma reserva sequencial (`ultimo_numero`) deve ser consumida ou incrementada.
   - Nenhuma chamada para a SEFAZ ou serviço de mensageria fiscal deve ser disparada.
2. **Destravamento via API:**
   - Enviar `PUT /api/v1/fiscal/configuracao` com `numeracao_confirmada: true` (ou atualizando as séries/números) atualiza o banco para `True`.
3. **Liberação de Emissão:**
   - Com `numeracao_confirmada == True`, o gate `verificar_emitente` valida a etapa com sucesso e o fluxo segue normal.
4. **Cobertura de Testes:**
   - Arquivo: `backend-fastapi/test/services/fiscal/test_gate_numeracao_confirmada.py`
   - Testar:
     - Bloqueio com retorno da pendência quando `numeracao_confirmada=False`.
     - Liberação imediata após update para `True`.
     - Comportamento da auto-confirmação ao alterar `ultimo_numero_nfe`.

---

# Prompt
"
Você é um desenvolvedor sênior Python especialista em FastAPI, SQLAlchemy 2.0 e Alembic.

Implemente a especificação técnica abaixo à risca, respeitando rigorosamente os caminhos de arquivos indicados, as convenções de tipagem e sem refatorar lógicas adjacentes não solicitadas.

---

### TAREFA
feat(fiscal-backend): locker e validacao de confirmacao da numeracao fiscal

### CONTEXTO E OBJETIVO
Impedir que documentos fiscais (NF-e mod. 55 e NFC-e mod. 65) sejam emitidos antes que o emitente confirme formalmente a série e o último número emitido no sistema, prevenindo a Rejeição SEFAZ 204 (Duplicidade de Nota) em empresas migradas de outros ERPs.

---

### DETALHAMENTO DA IMPLEMENTAÇÃO

1. Modelagem (SQLAlchemy 2.0)
- Arquivo: `backend-fastapi/app/db/models/empresa_fiscal_settings.py`
- Adicionar o campo:
  ```python
  numeracao_confirmada: Mapped[bool] = mapped_column(
      Boolean,
      default=False,
      server_default=sa.text("false"),
      nullable=False,
      doc="Indica se o operador/implantador confirmou formalmente a série e o último número emitido"
  )
  ```

2. Migration (Alembic)
- Criar migration adicionando a coluna `numeracao_confirmada` com default `False`.
- Incluir data migration para clientes legados: marcar como `True` qualquer empresa que já possua notas fiscais com status de autorizada no banco:
  ```sql
  UPDATE empresa_fiscal_settings 
  SET numeracao_confirmada = true 
  WHERE empresa_id IN (SELECT DISTINCT empresa_id FROM notas_fiscais WHERE status = 'AUTORIZADA');
  ```

3. Schemas (Pydantic v2)
- Arquivo: `backend-fastapi/app/schemas/empresa.py`
  - Em `FiscalSettingsBase`: adicionar `numeracao_confirmada: bool = False`
  - Em `FiscalSettingsUpdate`: adicionar `numeracao_confirmada: Optional[bool] = None`
- Arquivo: `backend-fastapi/app/schemas/emissao_fiscal.py`
  - Em `FiscalConfiguracao`: adicionar `numeracao_confirmada: bool = False`

4. Serviços e Endpoints
- Arquivo: `backend-fastapi/app/services/empresa.py` (`update_fiscal_settings`):
  - Se `numeracao_confirmada` for enviado explicitamente como `True`, persistir o valor.
  - Regra de auto-confirmação: se o payload atualizar explicitamente qualquer um dos campos (`serie_nfe`, `ultimo_numero_nfe`, `serie_nfce` ou `ultimo_numero_nfce`), setar automaticamente `settings.numeracao_confirmada = True`.
- Arquivo: `backend-fastapi/app/api/v1/endpoints/fiscal.py`:
  - `GET /configuracao`: mapear `numeracao_confirmada=fs.numeracao_confirmada if fs else False`.
  - `PUT /configuracao`: retornar o objeto `FiscalConfiguracao` atualizado contendo o valor booleano do campo.

5. Gate de Validação Fiscal
- Arquivo: `backend-fastapi/app/services/fiscal/validators.py`:
  - Na função `verificar_emitente(db: Session, empresa_id: int)`:
    Inspecionar `fiscal_settings.numeracao_confirmada`.
    Se for `False`, adicionar a pendência impeditiva:
    ```python
    if not fiscal_settings.numeracao_confirmada:
        pendencias.append(_p(
            "configuracao",
            "numeracao_confirmada",
            "Série e numeração de notas ainda não foram confirmadas. "
            "Acesse Centro Fiscal > Configurações > Emissão Estadual e confirme a sequência inicial."
        ))
    ```

6. Testes Unitários
- Arquivo: `backend-fastapi/test/services/fiscal/test_gate_numeracao_confirmada.py`
  - Cobrir:
    1. Bloqueio da emissão com status de pendência quando `numeracao_confirmada=False`.
    2. Liberação da validação quando `numeracao_confirmada=True`.
    3. Auto-confirmação para `True` ao atualizar séries/números via serviço.

---

### RESTRIÇÕES
- Não altere assinaturas de métodos não citados na especificação.
- Mantenha o padrão de tipagem estrita com type hints em todas as funções editadas.
- Forneça os arquivos completos ou trechos com diffs claros para fácil aplicação.
"
---

## Desvios aplicados na implementação (2026-09-17)
Ver `.agent/docs/progress/TASK001-BACKEND.md`. Resumo:
- Backfill usa `documento_fiscal` (não `notas_fiscais`) e não filtra por `empresa_id` (a tabela não tem a coluna).
- `server_default=text("0")` (SQLite).
- Migration manual idempotente (`s2t3u4v5w6x7`), não `autogenerate`.
- Auto-confirmação prevalece sobre `numeracao_confirmada=False` no mesmo payload.
- Testes: `test/services/fiscal/test_gate_numeracao_confirmada.py`, `test/api/v1/fiscal/test_configuracao_numeracao.py`, `test/db/test_migracao_numeracao_confirmada.py`.
