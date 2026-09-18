# SPEC-002: Emissão de Carta de Correção Eletrônica (CC-e) para NF-e

## 1. Visão Geral e Contexto
* **Identificador da Feature:** `feat(fiscal): emissao-carta-correcao`
* **Objetivo:** Permitir ao lojista corrigir, junto à SEFAZ, erros **não fiscais** de uma NF-e (modelo 55) já autorizada — texto de observação, descrição de item, dados de transporte, endereço do destinatário etc. — sem precisar cancelar a nota nem emitir uma nova. Hoje o único caminho é o cancelamento, que fora da janela de 24 h é impossível e, dentro dela, obriga a reemitir tudo.
* **Complexidade:** Média. A CC-e é um **evento** vinculado à nota (como o cancelamento), não uma nova emissão: não consome numeração, não gera itens, não mexe em estoque. O trabalho é o registro do evento, a chamada à emissora e a exibição do histórico.
* **Referência da emissora:** [Focus NFe — Emitir Carta de Correção](https://doc.focusnfe.com.br/reference/emitir_carta_correcao).
* **Spec vizinha:** a devolução (finalidade 4) é assunto da **TASK003** (`TASK003-BACKEND-NotaDevolucao.md` / `TASK003-FRONTEND-NotaDevolucao.md`). A CC-e **não** substitui a devolução: quando o erro é de valor, quantidade ou imposto, a via continua sendo cancelar (no prazo) ou devolver.

---

## 2. Regras de Negócio e Fiscais (SEFAZ)

1. **Só NF-e (modelo 55).**
   A legislação **não prevê CC-e para NFC-e (modelo 65)**. Um cupom com erro só admite cancelamento no prazo (30 min) ou devolução. O endpoint deve recusar `tipo_documento == "NFCE"` com 422 antes de chamar a emissora.
2. **Só documento `AUTORIZADA`.**
   A Focus devolve `nfe_nao_autorizada` (HTTP 400) para nota que não está autorizada. Cancelada, rejeitada ou em processamento não recebe carta.
3. **O que PODE ser corrigido** (Ajuste SINIEF 07/05, cláusula 14ª-A):
   * Erros de digitação em texto livre (`informacoes_adicionais`, descrição de item, dados adicionais do produto).
   * Dados de transporte (transportadora, placa, volumes, peso).
   * Endereço do destinatário (rua, número, complemento, bairro — desde que **não** troque a pessoa).
   * CFOP, desde que não altere o valor do imposto (ex.: 5102 → 5405 é vedado; erro de digitação equivalente é aceito).
   * Data de saída, quando ainda não escriturada.
4. **O que NÃO PODE ser corrigido** (a Focus lista literalmente):
   * "As variáveis que determinam o valor do imposto (base de cálculo, alíquota, diferença de preço, quantidade, valor da operação)".
   * Dados cadastrais que impliquem **mudança do remetente ou do destinatário** (CNPJ/CPF, IE, razão social).
   * **Data de emissão** ou de saída já registrada.
   * Numeração, série, chave de acesso.
   Para esses casos o operador é orientado a cancelar (dentro do prazo) ou emitir NF-e de devolução (TASK003).
5. **Limite de 20 cartas por nota.** A partir da 21ª a SEFAZ recusa. O ERP deve contar e bloquear localmente antes de gastar uma chamada.
6. **A última carta substitui as anteriores.** A SEFAZ considera vigente **somente a CC-e mais recente**; ela precisa **consolidar** todas as correções ainda válidas. Consequência de UX: ao abrir uma nova carta, o campo deve vir **pré-preenchido com o texto da última carta autorizada**, para o operador acrescentar, e não substituir sem querer.
7. **Prazo.** A Focus não impõe prazo na doc. A regra da SEFAZ (manual de eventos) é **até 720 h (30 dias)** da autorização — a documentação da Focus **não menciona** esse limite, então o ERP **não bloqueia localmente** por prazo: deixa a SEFAZ decidir e exibe a mensagem dela. (Diferente do cancelamento, onde o prazo é curto e a recusa tardia custa dinheiro devolvido ao cliente.)
8. **Texto da correção.** Mínimo **15** e máximo **1000** caracteres (limite da Focus/SEFAZ; o cancelamento usa 255, **não reaproveitar** `CancelamentoRequest`). Sem acentuação obrigatória; a Focus aceita UTF-8.
9. **Não altera o documento original.** Chave, número, protocolo, valor e itens do `DocumentoFiscal` ficam intocados. A carta é um registro **anexo** à nota, com XML e PDF próprios.

---

## 3. Contrato da Emissora (Focus NFe v2)

A API StartBig é **intermediária** da Focus (ver `client_startbig.py::_primeiro`). O ERP fala com `https://api.startbig.com.br/erp/fiscal/nfe/...`; a plataforma repassa à Focus. O contrato abaixo é o da Focus, que a intermediária deve **espelhar ou normalizar** (ver § 7 — Dependências).

### 3.1. Requisição
| | |
|---|---|
| Método | `POST` |
| Rota Focus | `/v2/nfe/{referencia}/carta_correcao` |
| Produção | `https://api.focusnfe.com.br/v2` |
| Homologação | `https://homologacao.focusnfe.com.br/v2` |
| Auth | HTTP Basic (token como usuário, senha vazia) — a intermediária troca pelo Bearer da licença |
| `referencia` | o `ref_api` gravado no `DocumentoFiscal` na emissão |

Corpo:
```json
{
  "correcao": "Corrigido o complemento do endereço do destinatário: sala 302, e não 203.",
  "data_evento": "2026-09-17T14:30:00-03:00"
}
```
| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `correcao` | string | **sim** | 15 a 1000 caracteres |
| `data_evento` | datetime ISO 8601 | não | Padrão: data/hora atual da Focus. **O ERP não envia** — o relógio da máquina da loja não é confiável (ver memória `c19-fuso-horario-relatorios`), e a SEFAZ rejeita evento com data futura. |

### 3.2. Resposta (HTTP 200)
```json
{
  "status": "autorizado",
  "status_sefaz": "135",
  "mensagem_sefaz": "Evento registrado e vinculado a NF-e",
  "numero_carta_correcao": 1,
  "caminho_xml_carta_correcao": "/arquivos/.../cce_<chave>_01.xml",
  "caminho_pdf_carta_correcao": "/arquivos/.../cce_<chave>_01.pdf"
}
```
| Campo | Uso no ERP |
|---|---|
| `status` | `autorizado` → `AUTORIZADA`; `erro_autorizacao` → `REJEITADA` |
| `status_sefaz` | `codigo_status_sefaz` (135 = evento vinculado; 136 = vinculado com ressalva — **também é sucesso**) |
| `mensagem_sefaz` | `mensagem_sefaz` |
| `numero_carta_correcao` | `sequencia` (1..20) — a SEFAZ numera; o ERP **não** inventa |
| `caminho_xml_carta_correcao` | `url_xml` → baixar e guardar local (`arquivos.guardar_xml`) |
| `caminho_pdf_carta_correcao` | `url_pdf` → baixar e guardar local (`arquivos.guardar_pdf`) |

Os caminhos são **relativos** ao host da Focus, como os da NF-e — `baixar_xml`/`baixar_pdf` do client já tratam isso.

### 3.3. Erros
| HTTP | `codigo` | Significado | Tratamento no ERP |
|---|---|---|---|
| 400 | `requisicao_invalida` | JSON malformado / campo faltando | 502 com a mensagem (bug nosso — logar payload via `_registrar_payload`) |
| 400 | `nfe_nao_autorizada` | Nota não está autorizada na Focus | 422 — o ERP já checa antes, mas o estado pode ter divergido: sugerir "Consultar na SEFAZ" |
| 400 | `formato_invalido` | `correcao` fora de 15–1000 ou `data_evento` inválida | 422 (o Pydantic barra antes; se chegar aqui é divergência de regra) |
| 401 | — | Token da licença inválido | 502 "licença não autenticada" (mesmo caminho da emissão) |
| 404 | `nao_encontrado` | `ref` desconhecida na Focus | 422 "referência não encontrada na emissora" |
| 415 | — | `Content-Type` errado | não deve acontecer (client fixa `application/json`) |

Rejeições **da SEFAZ** (não da Focus) chegam com HTTP 200 e `status = "erro_autorizacao"`, com o código em `status_sefaz`. As mais prováveis: **573** (duplicidade de evento), **574** (sequência de evento inválida), **594** (evento já registrado), **236/999** (CC-e fora do prazo ou texto vedado). Todas viram registro `REJEITADA` com a mensagem, sem exceção HTTP.

---

## 4. Especificação do Backend

### 4.1. Modelo e Banco de Dados — nova tabela `carta_correcao_fiscal`
Segue o precedente de `InutilizacaoFiscal` (`app/db/models/inutilizacao_fiscal.py`): evento com registro **próprio**, não coluna no `DocumentoFiscal`. Uma nota pode ter até 20 cartas, e cada uma tem XML, PDF e protocolo.

* **Arquivo:** `backend-fastapi/app/db/models/carta_correcao_fiscal.py`
```python
class CartaCorrecaoFiscal(Base):
    __tablename__ = "carta_correcao_fiscal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    documento_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documento_fiscal.id"), nullable=False, index=True,
        doc="NF-e que recebeu a carta",
    )
    sequencia: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        doc="numero_carta_correcao devolvido pela SEFAZ (1..20). Nulo enquanto não autorizada.",
    )
    correcao: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, default="PROCESSANDO", index=True,
        doc="PROCESSANDO | AUTORIZADA | REJEITADA | ERRO",
    )
    protocolo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    codigo_status_sefaz: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mensagem_sefaz: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url_xml: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url_pdf: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    caminho_xml_local: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    caminho_pdf_local: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ambiente_emissao: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, doc="Quem pediu a carta")
    data_evento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, doc="UTC, como o resto do banco")
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    documento: Mapped["DocumentoFiscal"] = relationship(back_populates="cartas_correcao")
```
* Em `DocumentoFiscal`: `cartas_correcao: Mapped[list["CartaCorrecaoFiscal"]] = relationship(back_populates="documento", order_by="CartaCorrecaoFiscal.sequencia")`.
* Registrar o modelo em `app/db/base.py` (senão o `create_all()` do startup não o cria).

**Migration Alembic:** `backend-fastapi/alembic/versions/<rev>_tabela_carta_correcao_fiscal.py`, modelada em `n7o8p9q0r1s2_tabela_inutilizacao_fiscal.py`: decide por `insp.has_table("carta_correcao_fiscal")` e **retorna** se já existe — porque `create_all()` roda **antes** de `aplicar_migracoes()` (ver `CLAUDE.md` § Atualização de cliente). Tabela nova, sem backfill.

### 4.2. Schemas Pydantic
* **Arquivo:** `backend-fastapi/app/schemas/emissao_fiscal.py`
```python
class CartaCorrecaoRequest(BaseModel):
    """Request para registrar CC-e numa NF-e autorizada.

    Não reaproveita CancelamentoRequest: o limite é OUTRO (1000, não 255),
    e a carta precisa caber a consolidação de todas as anteriores.
    """
    correcao: str

    @field_validator("correcao")
    @classmethod
    def validar_correcao(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 15:
            raise ValueError("A correção deve ter no mínimo 15 caracteres (exigência SEFAZ).")
        if len(v) > 1000:
            raise ValueError("A correção deve ter no máximo 1000 caracteres.")
        return v


class CartaCorrecaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int
    sequencia: Optional[int]
    correcao: str
    status: str
    protocolo: Optional[str]
    codigo_status_sefaz: Optional[int]
    mensagem_sefaz: Optional[str]
    url_xml: Optional[str]
    url_pdf: Optional[str]
    xml_local: bool          # derivado de caminho_xml_local, como no DocumentoFiscalRead
    pdf_local: bool
    data_evento: Optional[datetime]
    data_criacao: datetime
```
* Em `DocumentoFiscalRead` (`app/schemas/documento_fiscal.py`): acrescentar `total_cartas_correcao: int = 0` e `ultima_carta_correcao: Optional[str] = None` para o drawer mostrar o selo e pré-preencher o texto **sem** uma segunda requisição.

### 4.3. Client HTTP — protocolo, real e mock
* **`app/services/fiscal/http/client.py`** — novo método no `FiscalClientProtocol`:
  ```python
  def emitir_carta_correcao(self, ref: str, correcao: str) -> EmissaoResultado:
      """Registra CC-e na NF-e `ref`. Só modelo 55 — não recebe tipo_documento."""
      ...
  ```
  Acrescentar ao `EmissaoResultado` a chave opcional `numero_carta_correcao: Optional[int]`.
* **`client_startbig.py`** — `emitir_carta_correcao`:
  * URL: `f"{self.base_url}/erp/fiscal/nfe/carta-correcao"` (rota da intermediária — ver § 7).
  * Body: `{"ref": ref, "correcao": correcao}` — **sem** `data_evento`.
  * Chamar `_registrar_payload("carta_correcao", ref, body)` antes do POST.
  * Timeout 20 s (mesmo do cancelamento).
  * `_parse_response` já resolve `status_sefaz` → `codigo_sefaz` e `mensagem_sefaz`. Estender `_primeiro` para:
    * `url_xml` ← `url_xml`, `caminho_xml_carta_correcao`, `caminho_xml_nota_fiscal`
    * `url_pdf` ← `url_pdf`, `caminho_pdf_carta_correcao`, `caminho_danfe`
    * `numero_carta_correcao` ← `numero_carta_correcao`, `sequencia`
  * 4xx da plataforma → `_recusa_local` (mesma lógica: sem `codigo_sefaz` = **não transmitido**, não é rejeição).
* **`client_mock.py`** — devolve `{"status": "autorizado", "codigo_sefaz": 135, "numero_carta_correcao": <contador por ref>, "mensagem_sefaz": "Evento registrado e vinculado a NF-e (HOMOLOGAÇÃO)", "url_xml": None, "url_pdf": None}`. O contador por `ref` importa para testar o limite de 20 sem plataforma.

### 4.4. Serviço
* **Arquivo novo:** `backend-fastapi/app/services/fiscal/carta_correcao.py` (não inchar `emissao.py`; segue `inutilizacao.py`).
```python
LIMITE_CARTAS_POR_NOTA = 20

def emitir_carta_correcao(db, documento_id, empresa_id, correcao, usuario_id) -> CartaCorrecaoFiscal
def listar_cartas_correcao(db, documento_id, empresa_id) -> list[CartaCorrecaoFiscal]
def _aplicar_resultado_carta(registro, resultado) -> None
```
* **Fluxo de `emitir_carta_correcao`:**
  1. `crud.get_documento_fiscal` → 404 se não existir ou `empresa_id` divergir.
  2. `doc.tipo_documento != "NFE"` → 422 `{"codigo": "CCE_SOMENTE_NFE", "mensagem": "Carta de correção só existe para NF-e. Para um cupom NFC-e, cancele no prazo ou emita devolução."}`.
  3. `doc.status != "AUTORIZADA"` → 422 "Apenas NF-e autorizada recebe carta de correção."
  4. `not doc.ref_api` → 422 "Documento não possui referência de API." (mesma checagem do cancelamento).
  5. Contar cartas `AUTORIZADA` do documento; `>= 20` → 422 `{"codigo": "CCE_LIMITE_ATINGIDO"}`.
  6. Se existe carta `PROCESSANDO` para o documento → 409 (evita duas cartas concorrentes numa mesma nota; a SEFAZ devolveria 573/574).
  7. Gravar `CartaCorrecaoFiscal(status="PROCESSANDO", correcao=..., ambiente_emissao=fs.ambiente_emissao, usuario_id=...)` e `flush()` — registro existe **antes** da chamada, para a falha de rede não perder o pedido (mesmo princípio da emissão).
  8. `client = get_fiscal_client(fs.ambiente_emissao, crud.get_licenca_token(db))`; `resultado = client.emitir_carta_correcao(doc.ref_api, correcao)`.
  9. `_aplicar_resultado_carta`: `autorizado` → `AUTORIZADA`, `sequencia`, `protocolo`, `codigo_status_sefaz`, `mensagem_sefaz`, `url_xml`, `url_pdf`, `data_evento = now(UTC)`; `erro_autorizacao` → `REJEITADA`; `RESULTADO_NAO_TRANSMITIDO` → `ERRO` com a mensagem da plataforma.
  10. Se autorizada: `arquivos.guardar_xml` / `guardar_pdf` com sufixo `_cce_{sequencia:02d}` no nome (em `caminho_do_documento`, o nome-base é a chave da nota; sem sufixo a carta sobrescreveria o XML da nota). Falha no download **não** derruba a operação — fica para `sincronizar_pendentes`.
  11. `NotImplementedError` do client → 501; outra exceção → 502, como em `cancelar_documento`.
  12. Retornar o registro. **Não** chamar `espelhar_na_nota_da_venda` — a nota não mudou.
* **Reconciliação:** estender `arquivos.sincronizar_pendentes` para também baixar XML/PDF de `CartaCorrecaoFiscal` autorizadas sem arquivo local.
* **Exportação:** `exportacao_xml.py` deve incluir os XML das cartas no ZIP do período — a contabilidade precisa do evento junto da nota.

### 4.5. Endpoints
* **Arquivo:** `backend-fastapi/app/api/v1/endpoints/fiscal.py`, bloco novo `# CARTA DE CORREÇÃO` logo após `# CANCELAMENTO`.

| Método | Rota | Resposta | Descrição |
|---|---|---|---|
| `POST` | `/api/v1/fiscal/documentos/{documento_id}/carta-correcao` | `CartaCorrecaoRead` | Registra a CC-e (via `_handle_db_transaction`, como o cancelamento) |
| `GET` | `/api/v1/fiscal/documentos/{documento_id}/cartas-correcao` | `list[CartaCorrecaoRead]` | Histórico, ordenado por `sequencia` |
| `GET` | `/api/v1/fiscal/cartas-correcao/{carta_id}/pdf` | `application/pdf` | Serve o local; se não houver, baixa da emissora (mesmo padrão do PDF da nota) |
| `GET` | `/api/v1/fiscal/cartas-correcao/{carta_id}/xml` | `application/xml` | Idem |

Todos com `Depends(get_current_active_user)` e `empresa_id` do token.

### 4.6. Testes (`backend-fastapi/test/`)
* `test_carta_correcao.py` com o mock:
  * NFC-e → 422 `CCE_SOMENTE_NFE`, **sem** chamar o client.
  * Documento `CANCELADA` → 422.
  * `correcao` de 14 chars → 422 do Pydantic; 1001 → 422.
  * 20 autorizadas → 21ª recusada localmente.
  * Sucesso grava `sequencia`, `status = AUTORIZADA` e **não** altera `DocumentoFiscal.status`, `chave_acesso` nem `protocolo_autorizacao`.
  * `erro_autorizacao` grava `REJEITADA` e a mensagem, sem exceção.
  * 4xx da plataforma grava `ERRO`, não `REJEITADA`.

---

## 5. Especificação do Frontend

### 5.1. Tipos e serviço
* **`frontend/src/modules/fiscal/types/fiscal.types.ts`:** `CartaCorrecaoRead` (Zod + `z.infer`), campos iguais ao schema do backend; `DocumentoFiscalRead` ganha `total_cartas_correcao` e `ultima_carta_correcao`.
* **`frontend/src/modules/fiscal/services/fiscal.service.ts`:**
  * `emitirCartaCorrecao(id: number, correcao: string): Promise<CartaCorrecaoRead>` → `POST /documentos/${id}/carta-correcao`
  * `listarCartasCorrecao(id: number): Promise<CartaCorrecaoRead[]>` → `GET /documentos/${id}/cartas-correcao`
  * `baixarPdfCartaCorrecao(cartaId)` / `baixarXmlCartaCorrecao(cartaId)` → `Blob`
  * Padrão `safeParse` + `console.warn` + fallback, como os demais.
* **`frontend/src/modules/fiscal/constants/fiscal.constants.ts`:** `fiscalKeys.cartasCorrecao: (id: number) => ['fiscal', 'cartas-correcao', id] as const`.

### 5.2. Composables (TanStack Query)
* **`useFiscalCartaCorrecaoMutation.ts`** — espelho de `useFiscalCancelarMutation.ts`:
  * `mutationFn: ({ id, correcao }) => fiscalService.emitirCartaCorrecao(id, correcao)`
  * `onSuccess(carta)`: se `carta.status === 'AUTORIZADA'` → `toast.success('Carta de correção nº ${carta.sequencia} registrada na SEFAZ.')`; se `REJEITADA` → `toast.error(carta.mensagem_sefaz)` (a mutation **não** falha, a SEFAZ é que recusou). Invalidar `fiscalKeys.cartasCorrecao(id)`, `fiscalKeys.documento(id)` e `fiscalKeys.documentos()`. **Não** invalidar `resumo()` — os contadores não mudam.
  * `onError`: `toast.error(getErrorMessage(...))`.
* **`useFiscalCartasCorrecaoQuery.ts`** — `useQuery({ queryKey: fiscalKeys.cartasCorrecao(id), enabled: tipo === 'NFE' && status === 'AUTORIZADA' })`, `staleTime` 1 min.

### 5.3. Drawer de detalhes — ponto de acesso
* **Arquivo:** `frontend/src/modules/fiscal/components/detalhes/FiscalDocumentoDetailsDrawer.vue`, bloco "Ações do Documento Autorizado" (`v-if="documento.status === 'AUTORIZADA'"`).
* Novo botão `col-span-2`, **acima** de "Cancelar NF-e na SEFAZ", visível só quando `documento.tipo_documento === 'NFE'`:
  * Ícone `FilePenLine` (lucide), estilo âmbar (`border-amber-200 bg-amber-50/50 text-amber-800`) — é ação corretiva, não destrutiva; não pode parecer o cancelamento.
  * Texto: **"Carta de Correção"**; se `total_cartas_correcao > 0`, sufixo `(${n}/20)`.
  * `disabled` quando `total_cartas_correcao >= 20`, com `title="Limite de 20 cartas atingido"`.
* Para NFC-e não exibir nada — nem botão desabilitado — para não sugerir que existe.

### 5.4. Form inline de correção
Mesmo padrão do "Form Inline de Cancelamento" (`Transition name="fade"`, `v-if="formCartaOpen"`), **não** um modal separado, para manter o drawer coerente:
1. Aviso fixo em amarelo, uma linha: *"Corrige apenas texto, endereço, transporte e observações. Valores, impostos, quantidades e o destinatário **não** podem ser alterados — para isso, cancele no prazo ou emita devolução."*
2. `textarea` `v-model="textoCorrecao"`, `rows="5"`, `maxlength="1000"`, contador `${textoCorrecao.length}/1000` no canto.
   * **Pré-preenchido com `documento.ultima_carta_correcao`** quando existir, com legenda: *"A SEFAZ considera apenas a última carta. Mantenha as correções anteriores e acrescente a nova."*
3. Botões: "Fechar" e **"Registrar na SEFAZ"** (`disabled` se `< 15` chars ou `isEnviando`; texto "Registrando…" durante).
4. Ao sucesso: fechar o form, limpar o texto, e a lista da § 5.5 se atualiza pela invalidação.

### 5.5. Histórico de cartas no drawer
Na aba principal, abaixo das ações, seção **"Cartas de Correção"** (só quando `total_cartas_correcao > 0` ou a query devolveu itens):
* Uma linha por carta: `nº ${sequencia}` · data (formatada com o util de fuso local) · badge de status (reusar `STATUS_COLORS` de `fiscal.constants.ts`) · texto truncado em 2 linhas com "ver mais".
* Ações por linha: **PDF** e **XML** (download local via `baixarPdfCartaCorrecao`/`baixarXmlCartaCorrecao`, mesmo fluxo de `salvarDanfeLocal`), selo verde "guardado neste computador" quando `pdf_local`.
* Carta `REJEITADA`: mostrar `mensagem_sefaz` em vermelho, sem botões de arquivo.

### 5.6. Linha do tempo
Em `FiscalHistoricoQuery`/linha do tempo do drawer (aba de tentativas), acrescentar um ponto âmbar por carta autorizada: *"Carta de correção nº N registrada"*. Não é obrigatório para o aceite, mas evita que a aba minta "nada aconteceu desde a autorização".

---

## 6. Critérios de Aceite

1. **Contrato:** o JSON enviado à plataforma contém `ref` e `correcao` (15–1000 chars) e **não** contém `data_evento`; a resposta da Focus é mapeada para `sequencia`, `protocolo`, `codigo_status_sefaz`, `mensagem_sefaz`, `url_xml`, `url_pdf`.
2. **Somente NF-e:** um documento `NFCE` recebe 422 `CCE_SOMENTE_NFE` sem que o client seja chamado; no drawer o botão não aparece.
3. **Somente autorizada:** `CANCELADA`, `REJEITADA`, `PROCESSANDO` → 422.
4. **Imutabilidade da nota:** após a carta, `DocumentoFiscal` (status, chave, número, protocolo, valor_total, itens) está byte a byte igual; `venda_nota_fiscal` não é tocada.
5. **Limite:** a 21ª carta é recusada localmente com `CCE_LIMITE_ATINGIDO`; o botão fica desabilitado em `20/20`.
6. **Consolidação:** ao abrir o form com uma carta anterior, o `textarea` já vem com o texto dela.
7. **Rejeição SEFAZ ≠ erro:** `erro_autorizacao` gera registro `REJEITADA` com a mensagem, HTTP 200 no endpoint, e o toast mostra a mensagem da SEFAZ. 4xx da plataforma gera `ERRO`, nunca `REJEITADA`.
8. **Arquivos:** carta autorizada tem XML e PDF guardados localmente com sufixo `_cce_NN`, sem sobrescrever os da nota; ambos aparecem no ZIP de exportação do período.
9. **Mock:** com `FISCAL_MOCK_ENABLED`, o fluxo inteiro funciona sem plataforma, inclusive o limite de 20.

---

## 7. Dependências Externas e Riscos

| Item | Situação | Ação |
|---|---|---|
| **Rota na API StartBig (intermediária)** | `/erp/fiscal/nfe/carta-correcao` **não existe** hoje — só `/emitir`, `/consultar`, `/cancelar`, `/inutilizar`. | Abrir tarefa na API Web: rota que recebe `{ref, correcao}`, chama `POST /v2/nfe/{ref}/carta_correcao` na Focus e devolve o JSON **com os nomes da Focus** (`numero_carta_correcao`, `caminho_xml_carta_correcao`, `caminho_pdf_carta_correcao`, `status_sefaz`). Se a intermediária normalizar nomes, `_primeiro` já cobre as duas grafias. **Bloqueante para o teste em homologação; não bloqueia o desenvolvimento com mock.** |
| **Módulo/cota da plataforma** | A plataforma tem cota por família (`nfe`/`nfce`). Não se sabe se a carta consome cota de emissão. | Confirmar com a API Web; se consumir, exibir no card de plataforma (`useFiscalPlataformaQuery`). |
| **Prazo de 720 h** | Não está na doc da Focus; é regra SEFAZ. | Não bloquear localmente. Se a SEFAZ passar a recusar com código fixo, registrar a mensagem e reavaliar. |
| **PyArmor / sidecar** | Mexe no backend. | `npm run build:sidecar` antes de qualquer instalador (`check:sidecar` falha se esquecer). |
| **Conflito com TASK003** | Ambas tocam `fiscal.py`, `fiscal.service.ts`, o drawer e `client.py`. | Desenvolver a CC-e **primeiro** (menor) ou em branch separada; rebase antes de abrir o PR da devolução. |

---

## Desvios aplicados na implementação (2026-09-17)
Ver `.agent/docs/progress/TASK002.md` e `ADR-001`. Resumo:
- Endpoints devolvem `CartaCorrecaoRead` direto (padrão do módulo fiscal).
- Linha do tempo (§ 5.6) não implementada — a seção "Cartas de Correção" cobre.
- `ERRO` entrou em `STATUS_COLORS/LABELS`.
- Testes: `test/services/fiscal/test_carta_correcao.py`, `test/api/v1/fiscal/test_carta_correcao_api.py`, `composables/__tests__/cartaCorrecao.spec.ts`.
