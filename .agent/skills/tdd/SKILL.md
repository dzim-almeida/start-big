# TDD Skill — Test-Driven Development

**Versão:** 1.0
**Propósito:** Orientar desenvolvimento com testes primeiro
**Escopo:** Backend (FastAPI/pytest) + Frontend (Vue 3/Vitest)

---

## 1. Ciclo TDD

### Fluxo
```
1. RED: Escrever teste que falha (requisito claro)
   ↓
2. GREEN: Implementar código mínimo para passar
   ↓
3. REFACTOR: Melhorar código sem quebrar testes
   ↓
Repetir para próximo requisito
```

### Benefícios
- ✅ Código mais testável por design
- ✅ Menos bugs em produção
- ✅ Documentação viva (testes = exemplos)
- ✅ Confiança em refators
- ✅ Design simples (YAGNI natural)

---

## 2. Backend: TDD com FastAPI + pytest

### 2.1 Estrutura de Teste

```
backend-fastapi/
├── app/
│   ├── db/models/usuario.py
│   ├── schemas/usuario.py
│   ├── api/v1/endpoints/usuarios.py
│   └── services/usuario.py
└── test/
    ├── conftest.py              # Fixtures compartilhadas
    ├── test_schemas/
    │   └── test_usuario.py      # Validação Pydantic
    ├── test_services/
    │   └── test_usuario.py      # Lógica de negócio
    └── test_endpoints/
        └── test_usuarios.py     # Endpoints HTTP
```

### 2.2 Exemplo: RED → GREEN → REFACTOR

#### RED: Teste Falha
```python
# test/test_services/test_usuario.py
import pytest
from app.services.usuario import UsuarioService
from app.schemas.usuario import UsuarioCreate

@pytest.mark.asyncio
async def test_criar_usuario_com_validacoes():
    """Deve criar usuário com nome e email únicos."""
    service = UsuarioService()

    # Teste 1: Nome vazio deve falhar
    with pytest.raises(ValueError, match="Nome obrigatório"):
        await service.criar(UsuarioCreate(nome="", email="test@test.com"))

    # Teste 2: Email duplicado deve falhar
    usuario1 = await service.criar(UsuarioCreate(nome="João", email="joao@test.com"))
    with pytest.raises(ValueError, match="Email já existe"):
        await service.criar(UsuarioCreate(nome="Pedro", email="joao@test.com"))

    # Teste 3: Sucesso com dados válidos
    usuario2 = await service.criar(UsuarioCreate(nome="Maria", email="maria@test.com"))
    assert usuario2.nome == "Maria"
    assert usuario2.email == "maria@test.com"
```

**Resultado:** ❌ FALHA (função não existe)

#### GREEN: Implementação Mínima
```python
# app/services/usuario.py
from app.schemas.usuario import UsuarioCreate
from app.db.models.usuario import Usuario
from sqlalchemy.orm import Session

class UsuarioService:
    def __init__(self, db: Session):
        self.db = db

    async def criar(self, dados: UsuarioCreate) -> Usuario:
        """Cria usuário com validações."""
        # Validação 1: Nome obrigatório
        if not dados.nome or not dados.nome.strip():
            raise ValueError("Nome obrigatório")

        # Validação 2: Email único
        existente = self.db.query(Usuario).filter_by(email=dados.email).first()
        if existente:
            raise ValueError("Email já existe")

        # Criar
        usuario = Usuario(nome=dados.nome, email=dados.email)
        self.db.add(usuario)
        self.db.flush()
        return usuario
```

**Resultado:** ✅ PASSA

#### REFACTOR: Melhorar Qualidade
```python
# app/services/usuario.py (melhorado)
from app.schemas.usuario import UsuarioCreate
from app.db.crud.usuario import UsuarioCRUD
from app.helpers.exceptions import EmailJaExisteError, DadosInvalidosError

class UsuarioService:
    def __init__(self, crud: UsuarioCRUD):
        self.crud = crud

    async def criar(self, dados: UsuarioCreate) -> Usuario:
        """Cria usuário com validações."""
        self._validar_nome(dados.nome)
        self._validar_email_unico(dados.email)

        usuario = self.crud.criar(dados)
        return usuario

    @staticmethod
    def _validar_nome(nome: str) -> None:
        if not nome or not nome.strip():
            raise DadosInvalidosError("Nome obrigatório")

    async def _validar_email_unico(self, email: str) -> None:
        if self.crud.obter_por_email(email):
            raise EmailJaExisteError("Email já existe")
```

**Benefício:** Mais legível, separação de responsabilidades, fácil testar cada validação isoladamente.

### 2.3 Testes de Endpoint

```python
# test/test_endpoints/test_usuarios.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_criar_usuario_endpoint():
    """POST /usuarios deve criar e retornar 201."""
    response = client.post(
        "/api/v1/usuarios",
        json={"nome": "João", "email": "joao@test.com"}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["data"]["nome"] == "João"

def test_criar_usuario_email_duplicado():
    """POST com email duplicado deve retornar 409."""
    # Criar primeiro
    client.post(
        "/api/v1/usuarios",
        json={"nome": "João", "email": "joao@test.com"}
    )

    # Tentar criar duplicado
    response = client.post(
        "/api/v1/usuarios",
        json={"nome": "Pedro", "email": "joao@test.com"}
    )

    assert response.status_code == 409
    assert response.json()["status"] == "error"
    assert response.json()["error_code"] == "EMAIL_JA_EXISTE"
```

### 2.4 Fixture Reutilizável

```python
# test/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.session import SessionLocal

@pytest.fixture
def db_test():
    """Banco de testes (SQLite em memória)."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()

    yield session

    session.close()
    engine.dispose()

@pytest.fixture
def usuario_teste(db_test):
    """Usuário pré-criado para testes."""
    from app.db.models.usuario import Usuario
    usuario = Usuario(nome="Teste", email="teste@test.com")
    db_test.add(usuario)
    db_test.commit()
    return usuario
```

### 2.5 Checklist Backend TDD

- [ ] **RED**: Teste específico (não genérico) falha?
- [ ] **GREEN**: Implementação simples passa?
- [ ] **REFACTOR**: Código melhorou sem quebrar testes?
- [ ] **Cobertura**: Casos normais + edge cases + erros?
- [ ] **Nomenclatura**: `test_xxx_quando_yyy_entao_zzz`?
- [ ] **Fixtures**: Reutilizadas (não hardcoded)?
- [ ] **Velocidade**: Teste roda em < 1s?

---

## 3. Frontend: TDD com Vue 3 + Vitest

### 3.1 Estrutura de Teste

```
frontend/src/
├── modules/os/
│   ├── views/
│   ├── components/
│   ├── composables/useOSForm.ts
│   └── __tests__/
│       ├── useOSForm.spec.ts        # Teste do composable
│       └── OSFormModal.spec.ts      # Teste do componente
└── shared/
    └── composables/useToast.ts
        └── __tests__/useToast.spec.ts
```

### 3.2 Exemplo: Teste de Composable

#### RED: Teste Falha
```typescript
// modules/os/composables/__tests__/useOSForm.spec.ts
import { describe, it, expect } from 'vitest';
import { useOSForm } from '../useOSForm';

describe('useOSForm', () => {
  it('deve validar número da OS (obrigatório)', () => {
    const { form } = useOSForm();

    // Submeter sem número
    const erro = form.validar({ numero: '' });
    expect(erro).toBeDefined();
    expect(erro.numero).toContain('obrigatório');
  });

  it('deve validar valor total (positivo)', () => {
    const { form } = useOSForm();

    // Valor negativo
    let erro = form.validar({ valor_total: -100 });
    expect(erro.valor_total).toContain('positivo');

    // Valor zero
    erro = form.validar({ valor_total: 0 });
    expect(erro.valor_total).toContain('positivo');

    // Valor válido
    erro = form.validar({ valor_total: 10000 });
    expect(erro).toBeNull();
  });

  it('deve converter valor de reais para centavos ao salvar', () => {
    const { form, prepararParaSalvar } = useOSForm();

    form.valores.valor_total = 100.50;  // Reais
    const dados = prepararParaSalvar(form.valores);

    expect(dados.valor_total).toBe(10050);  // Centavos
  });
});
```

**Resultado:** ❌ FALHA

#### GREEN: Implementação
```typescript
// modules/os/composables/useOSForm.ts
import { ref } from 'vue';
import { schemaOS, type OSCreate } from '../schemas/os.schema';

export function useOSForm() {
  const valores = ref<Partial<OSCreate>>({});

  const validar = (dados: any) => {
    const resultado = schemaOS.safeParse(dados);
    if (!resultado.success) {
      const erros: Record<string, string> = {};
      resultado.error.errors.forEach(err => {
        const caminho = err.path.join('.');
        erros[caminho] = err.message;
      });
      return erros;
    }
    return null;
  };

  const prepararParaSalvar = (dados: any) => {
    return {
      ...dados,
      valor_total: Math.round(dados.valor_total * 100),  // Real → centavos
    };
  };

  return { valores, validar, prepararParaSalvar };
}
```

#### REFACTOR: Schema Separado
```typescript
// modules/os/schemas/os.schema.ts
import { z } from 'zod';

export const schemaOS = z.object({
  numero: z.string().min(1, 'Número obrigatório'),
  valor_total: z.number().positive('Valor deve ser positivo'),
  cliente_id: z.number().int().positive(),
});

export type OSCreate = z.infer<typeof schemaOS>;
```

### 3.3 Teste de Componente

```typescript
// modules/os/components/__tests__/OSFormModal.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import OSFormModal from '../OSFormModal.vue';

describe('OSFormModal', () => {
  it('deve abrir modal e exibir formulário', () => {
    const wrapper = mount(OSFormModal, {
      props: { isOpen: true },
    });

    expect(wrapper.find('[data-testid="form"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="btn-salvar"]').exists()).toBe(true);
  });

  it('deve emitir evento ao salvar', async () => {
    const wrapper = mount(OSFormModal, {
      props: { isOpen: true },
    });

    // Preencher formulário
    await wrapper.find('input[name="numero"]').setValue('OS-001');
    await wrapper.find('input[name="valor_total"]').setValue('100.50');

    // Clicar em salvar
    await wrapper.find('[data-testid="btn-salvar"]').trigger('click');

    // Verificar emissão
    expect(wrapper.emitted('save')).toBeDefined();
    const [dados] = wrapper.emitted('save')?.[0] as any[];
    expect(dados.numero).toBe('OS-001');
  });

  it('deve exibir validação ao submeter inválido', async () => {
    const wrapper = mount(OSFormModal, { props: { isOpen: true } });

    // Submeter sem preencher
    await wrapper.find('[data-testid="btn-salvar"]').trigger('click');

    // Verificar mensagem de erro
    expect(wrapper.text()).toContain('Número obrigatório');
  });
});
```

### 3.4 Test Data Builders (Mock Factories)

```typescript
// modules/os/__tests__/builders.ts
export function criarOS(sobrescrita?: Partial<OS>): OS {
  return {
    numero: 'OS-001',
    cliente_id: 1,
    valor_total: 10000,
    status: 'aberta',
    ...sobrescrita,
  };
}

export function criarOSItem(sobrescrita?: Partial<OSItem>): OSItem {
  return {
    id: 1,
    os_id: 1,
    descricao: 'Conserto',
    valor: 5000,
    ...sobrescrita,
  };
}
```

### 3.5 Checklist Frontend TDD

- [ ] **RED**: Teste descreve comportamento esperado?
- [ ] **GREEN**: Componente/composable passa?
- [ ] **REFACTOR**: Lógica movida para composable (reutilizável)?
- [ ] **Cobertura**: Entrada válida + inválida + erros?
- [ ] **Nomenclatura**: `test_xxx_quando_yyy_entao_zzz`?
- [ ] **Mocks**: Axios/queries mockados corretamente?
- [ ] **Velocidade**: Teste roda em < 100ms?
- [ ] **data-testid**: Adicionados para queries seguras?

---

## 4. Padrões Específicos do Projeto

### Backend: Teste de Fiscal Engine

```python
# test/test_services/test_fiscal_engine.py
import pytest
from app.services.fiscal.tax_engine.engine import TaxEngine
from app.services.fiscal.tax_engine.payload import TaxPayload

def test_calcular_icms_tributado():
    """Deve calcular ICMS CST 00 com alíquota de 18% (São Paulo)."""
    engine = TaxEngine()

    item = TaxPayload(
        valor_produto=10000,  # R$ 100,00
        cst="00",
        aliquota_icms=18,
    )

    resultado = engine.calcular_icms(item)

    assert resultado.icms == 1800  # 18% = R$ 18,00
    assert resultado.cst == "00"

def test_calcular_pis_cofins_com_exclusao():
    """PIS/COFINS excluem ICMS (STF Tema 69)."""
    # ...
```

### Frontend: Teste de Form Context

```typescript
// modules/os/composables/__tests__/useOSForm.spec.ts
import { describe, it, expect } from 'vitest';
import { defineComponent, h } from 'vue';
import { mount } from '@vue/test-utils';
import { useOSFormProvider, useOSForm } from '../useOSForm.context';

describe('useOSForm Context', () => {
  it('deve compartilhar estado via provide/inject', () => {
    const Provider = defineComponent({
      setup() {
        useOSFormProvider();
        return () => h('div');
      },
    });

    const Consumer = defineComponent({
      setup() {
        const { valores } = useOSForm();
        return () => h('div', valores.value.numero);
      },
    });

    const wrapper = mount({
      components: { Provider, Consumer },
      template: '<Provider><Consumer /></Provider>',
    });

    expect(wrapper.text()).toBeDefined();
  });
});
```

---

## 5. Rodando Testes

### Backend
```bash
# Todos os testes
pytest test/ -v

# Cobertura
pytest test/ --cov=app --cov-report=html

# Teste específico
pytest test/test_services/test_usuario.py::test_criar_usuario_com_validacoes -v

# Watch mode
pytest-watch test/
```

### Frontend
```bash
# Todos os testes
npm run test

# Watch mode
npm run test -- --watch

# Cobertura
npm run test -- --coverage

# Teste específico
npm run test -- OSFormModal.spec.ts
```

---

## 6. Boas Práticas TDD

### ✅ Faça
- Teste **um** comportamento por teste
- Nome deixa claro: `test_criar_usuario_com_email_duplicado_deve_falhar`
- Arrange → Act → Assert (AAA pattern)
- Fixtures para setup comum
- Mock apenas dependências externas
- Rodar testes antes de commitar

### ❌ Não Faça
- Teste que testa tudo (10+ assertions)
- Nome genérico: `test_usuario`
- Lógica complexa dentro de teste
- Hardcoded data (usar builders)
- Mock a própria classe (circular)
- Ignorar testes falhando (`@skip`)

---

## 7. CI/CD: Garantir Testes em Produção

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: cd backend-fastapi && pip install -r requirements.txt
      - run: cd backend-fastapi && pytest test/ -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install
      - run: cd frontend && npm run test
```

---

## 8. Cobertura de Testes Esperada

| Camada | Mínimo | Ideal |
|--------|--------|-------|
| Backend Services | 70% | 85%+ |
| Backend CRUD | 60% | 80%+ |
| Backend Endpoints | 50% | 75%+ |
| Frontend Composables | 70% | 85%+ |
| Frontend Components (lógica) | 60% | 80%+ |
| Frontend Utils | 80% | 95%+ |

---

**Última atualização:** 2026-09-16
**Ver também:** `code-quality.md` para padrões de implementação
