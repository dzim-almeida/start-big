# Code Quality Skill — DRY, YAGNI, CLEAN CODE

**Versão:** 1.0
**Propósito:** Garantir qualidade arquitetural e legibilidade de código
**Escopo:** Frontend (Vue 3/TypeScript) + Backend (FastAPI/Python)

---

## 1. DRY (Don't Repeat Yourself)

### Checklist
- [ ] Lógica repetida? → Extrair para função/composable
- [ ] Código duplicado em 3+ lugares? → Abstração necessária
- [ ] Constante hardcoded 2+ vezes? → Mover para `constants/`
- [ ] Validação repetida? → Schema compartilhado (Zod/Pydantic)
- [ ] Tipo duplicado? → `types/` ou `schemas/`

### Padrões DRY no Projeto

#### Frontend: Composables
```typescript
// ❌ Ruim: lógica duplicada em dois componentes
// ComponentA.vue
const { data, loading } = ref({});
const fetchData = async () => { /* 20 linhas */ };

// ❌ ComponentB.vue — mesmo código

// ✅ Bom: Extrair para composable
// composables/useXxxData.ts
export function useXxxData() {
  const data = ref({});
  const loading = ref(false);
  const fetchData = async () => { /* lógica centralizada */ };
  return { data, loading, fetchData };
}

// ComponentA.vue e ComponentB.vue usam o mesmo composable
const { data, loading, fetchData } = useXxxData();
```

#### Backend: Serviços Reutilizáveis
```python
# ❌ Ruim: Query complexa em dois endpoints
@router.get("/vendas")
async def listar_vendas(db: Session):
    # 15 linhas de filtro + ordenação

@router.get("/relatorio/vendas")
async def relatorio_vendas(db: Session):
    # 15 linhas — MESMA LÓGICA

# ✅ Bom: Serviço compartilhado
# services/venda.py
class VendaService:
    @staticmethod
    def aplicar_filtros_padrao(query: Query, filtros: dict):
        """Lógica reutilizável"""
        return query.filter(...).order_by(...)

# endpoints/vendas.py
vendas = VendaService.aplicar_filtros_padrao(db.query(Venda), filtros)
```

#### Frontend: Constantes
```typescript
// ❌ Ruim
useQuery({
  queryKey: ["os", "all"],
  // ... usado em 5 componentes diferentes
});

// ✅ Bom: Centralizar em constants/
// constants/core.constant.ts
export const queryKeys = {
  os: {
    all: ["os", "all"],
    byId: (id: string) => ["os", id],
  },
};

// Em qualquer componente:
const { data } = useQuery({ queryKey: queryKeys.os.all });
```

### Quando Aceitar Repetição
- **Padrão boilerplate legítimo** (ex: Redux thunk simples, componentes de form)
- **Refator mais caro que duração do código** (ex: script one-off)
- **Complexidade de abstração > benefício** (ex: 3 linhas de lógica)

---

## 2. YAGNI (You Aren't Gonna Need It)

### Checklist
- [ ] Parâmetro nunca usado? → Remover
- [ ] Branch condicional morto? → Deletar
- [ ] Feature hipotética? → Não implementar
- [ ] Configurabilidade além do atual? → Não adicionar
- [ ] Over-engineering detectado? → Simplificar

### Padrões YAGNI no Projeto

#### ❌ Não Faça
```typescript
// Feature "para o futuro"
function formatarValor(valor: number, tipo?: 'real' | 'usd' | 'eur') {
  // Implementa suporte a 3 moedas, mas sistema só usa Real
  // Ninguém pediu por USD/EUR
}

// Parâmetro não utilizado
function criarOS(dados: OSCreate, incluirHistorico: boolean = false) {
  // incluirHistorico nunca é consultado
  const os = await db.create(...);
}

// Configurabilidade desnecessária
class LogService {
  constructor(
    private format?: 'json' | 'text' | 'csv',  // Só precisa JSON
    private timezone?: string,  // Já tem global
    private buffering?: boolean  // Sistema é pequeno
  ) {}
}
```

#### ✅ Faça
```typescript
// Apenas o que é pedido
function formatarValor(valor: number): string {
  return `R$ ${(valor / 100).toFixed(2)}`;
}

// Sem parâmetros mortos
function criarOS(dados: OSCreate): Promise<OS> {
  return db.create(...);
}

// Simples e direto
class LogService {
  log(mensagem: string): void {
    console.log(JSON.stringify({ timestamp: new Date(), msg: mensagem }));
  }
}
```

### Quando Estender
- **Requisito no backlog/spec** (não hipotético)
- **Padrão já estabelecido no projeto** (ex: adicionar enum a lista existente)
- **Compatibilidade quebrada sem extensão** (ex: suportar novos CST ficais)

---

## 3. CLEAN CODE

### 3.1 Nomes Significativos

| ❌ Ruim | ✅ Bom | Motivo |
|---------|--------|--------|
| `let x = 10` | `let diasPrazo = 10` | Auto-explicativo |
| `function proc()` | `function processarPagamento()` | Deixa claro o propósito |
| `let temp` | `let saldoTemporario` | Contexto + intenção |
| `getMoney(id)` | `obterValorTotalOS(osId)` | Português + especifico |
| `funcs` | `validadores` | Descreve conteúdo |

### 3.2 Funções Pequenas e Focadas

#### Tamanho
- **Ideal**: 1-15 linhas
- **Máximo aceitável**: 25 linhas
- **Se > 25**: quebrar em subfunções

#### Exemplo Backend
```python
# ❌ Função de 50+ linhas (tudo junto)
def processar_venda(venda_id: int, db: Session):
    venda = db.query(Venda).filter_by(id=venda_id).first()
    # Validações (10 linhas)
    # Calcular impostos (15 linhas)
    # Atualizar estoque (10 linhas)
    # Registrar transação (5 linhas)
    # Gerar nota fiscal (10 linhas)

# ✅ Funções pequenas e compostas
def processar_venda(venda_id: int, db: Session) -> Venda:
    """Orquestra processamento de venda."""
    venda = _obter_venda(venda_id, db)
    _validar_venda(venda)
    _calcular_e_aplicar_impostos(venda)
    _atualizar_estoque(venda)
    _registrar_transacao(venda, db)
    _gerar_nota_fiscal(venda)
    db.commit()
    return venda

def _validar_venda(venda: Venda) -> None:
    """Valida invariantes de venda."""
    if not venda.cliente_id:
        raise ValueError("Venda sem cliente")
    if not venda.itens:
        raise ValueError("Venda sem itens")

def _calcular_e_aplicar_impostos(venda: Venda) -> None:
    """Calcula e aplica impostos à venda."""
    # Lógica fiscal
```

### 3.3 Nível de Abstração Único

```python
# ❌ Mistura abstrações
def processar_pagamento(pagamento_id: int):
    pagto = db.query(Pagamento).filter_by(id=pagamento_id).first()  # SQL low-level
    if pagto.tipo == "cheque":
        # Lógica de validação de cheque
        dias_uteis = calcular_dias_uteis(pagto.data_cheque)  # Business logic
    msg = f"Pagamento de {pagto.valor} processado"  # String building
    print(msg)  # I/O

# ✅ Cada função em nível apropriado
def processar_pagamento(pagamento_id: int) -> Resultado:
    """Nível alto: negócio"""
    pagto = obter_pagamento(pagamento_id)  # Chamada simples
    resultado = validar_e_processar_pagamento(pagto)  # Regra de negócio
    notificar_resultado(resultado)  # Efeito colateral encapsulado
    return resultado

def validar_e_processar_pagamento(pagto: Pagamento) -> Resultado:
    """Nível negócio"""
    if pagto.tipo == "cheque":
        validar_cheque(pagto)
    return Resultado.sucesso(pagto.valor)

def validar_cheque(cheque: Pagamento) -> None:
    """Nível específico: cheque"""
    dias_uteis = calcular_dias_uteis(cheque.data_cheque)
```

### 3.4 Tratamento de Erros

#### ✅ Padrão Esperado
```typescript
// Frontend: Deixar TanStack Query tratar
const { mutate } = useMutation({
  mutationFn: atualizarOS,
  onError: (err) => useToast().error(getErrorMessage(err)),
});

// Backend: Validar no schema, lançar exceção, deixar middleware tratar
class OSCreate(BaseModel):
    numero: str = Field(..., min_length=1)

@router.post("/os")
async def criar_os(dados: OSCreate) -> dict:
    """Pydantic já validou; ValueError/ValueError não é capturado aqui."""
    if not cliente_existe(dados.cliente_id):
        raise ValueError("Cliente não existe")
    # Retorna direto — endpoint exception handler retorna 400
    return {"status": "success", "data": os}
```

#### ❌ Não Faça
```typescript
// Tratamento genérico demais
try {
  await fetch("/api/os");
} catch (err) {
  console.log("Erro");  // Não ajuda
}

// Engolir exceção
try {
  validar_dados(x);
} catch (e) {
  pass  # Silenciosamente falha
}
```

### 3.5 Comentários (Quando Usar)

| ✅ Comentário Útil | ❌ Comentário Ruim |
|------------------|-----------------|
| `# Rateio proporcional com ajuste no item de maior valor` (por quê) | `# Itera itens` (óbvio do código) |
| `# CST 00 = tributado; 40/41 = não; 60 = diferença` (regra complexa) | `# x = x + 1` (óbvio) |
| `# RFC 1234: exceção por cliente ABC até 2026-12` (rastreável) | `# TODO: melhorar depois` (vago) |
| `# Compatibilidade: v1.0 usava "tipo_venda", agora "tipo"` (contexto) | `# Função maluca` (não ajuda) |

### 3.6 Valores Padrão Explícitos

```typescript
// ❌ Ruim: passe `undefined` para obter padrão
function criarOSItem(tipo: string, opcional?: boolean) {
  const ativo = opcional ?? true;  // Confuso
}

// ✅ Bom: padrão explícito
function criarOSItem(
  tipo: string,
  ativo: boolean = true  // Claro qual é o padrão
) {
  // ...
}

// Melhor ainda: constantes
const DEFAULT_OS_ITEM_ATIVO = true;
function criarOSItem(tipo: string, ativo = DEFAULT_OS_ITEM_ATIVO) {}
```

---

## 4. Checklist de Qualidade para Code Review

### Antes de Enviar
- [ ] **DRY**: Não há lógica duplicada em 3+ lugares?
- [ ] **YAGNI**: Cada parâmetro/feature é realmente usado?
- [ ] **Nomes**: Variáveis/funções são auto-explicativas?
- [ ] **Tamanho**: Funções > 25 linhas? Se sim, quebrar
- [ ] **Abstração**: Código mescla muitos níveis?
- [ ] **Comentários**: Explicam "por quê", não "o quê"?
- [ ] **Erros**: Tratados ou propagados corretamente?

### Estrutura Esperada

#### Frontend
```
modules/<feature>/
├── views/              # Páginas (podem ser maiores)
├── components/         # Componentes (10-40 linhas)
├── composables/        # Lógica reutilizável (10-30 linhas)
├── services/           # Chamadas API (sem lógica)
└── types/schemas/      # Tipos compartilhados
```

#### Backend
```
app/
├── api/v1/endpoints/   # Rotas HTTP (5-15 linhas, delegam)
├── services/           # Lógica de negócio (15-50 linhas)
├── db/crud/            # Acesso a dados (10-20 linhas)
└── db/models/          # Definição de tabelas (simples)
```

---

## 5. Decisões Arquiteturais vs. Implementação

### Não é YAGNI
- Padrão consistente no projeto (ex: todos services têm `xxx_service.py`)
- Escalabilidade conhecida (ex: Pinia store para estado de app)
- Contrato obrigatório (ex: `{ "status", "data" }` em respostas)

### É YAGNI
- "E se um dia precisar de X?"
- Parâmetro que ninguém passa
- Classe base para 1 subclasse
- "Deixarei mais flexível para o futuro"

---

## 6. Exceções Documentadas

### Quando Violar DRY
```python
# Tolerado: setup de teste idêntico em N testes
# Motivo: Fixtures compartilhadas são mais caras que duplicação
@pytest.mark.asyncio
async def test_criar_os():
    cliente = await criar_cliente_teste(db)  # 3 linhas (dup em 10 testes)
    # ...

@pytest.mark.asyncio
async def test_atualizar_os():
    cliente = await criar_cliente_teste(db)  # Aceitável
    # ...
```

### Quando Aceitar Código Maior
```typescript
// Tolerado: componente de form com muitos campos
// Motivo: Reutilizar é mais complexo (VeeValidate + provide/inject)
// Limite: 60-80 linhas, máximo
<template>
  <!-- 15 campos = 40+ linhas (aceitável) -->
</template>

<script setup>
  // 30 linhas de form setup
</script>
```

---

## 7. Ferramentas de Validação

### Frontend
```bash
npm run lint              # ESLint detecta código unused
npx vue-tsc --noEmit     # Type checking
```

### Backend
```bash
pytest test/ -v          # Testes detectam código morto
pylint app/              # Static analysis (opcional)
```

---

**Última atualização:** 2026-09-16
**Próximo:** Ler `tdd.md` para padrões de teste
