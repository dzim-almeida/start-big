import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';

import { DADOS_EXEMPLO, etiquetasDosVolumes, formatarChave, valoresDoDanfe, valoresDoEnvio, type DadosEnvio } from '../envio';
import { PRESETS_DANFE, PRESETS_VOLUME } from '../presets';
import { problemasDaPagina } from '../modelo';
import { problemasDosElementos } from '../editor/operacoes';
import EtiquetaView from '../components/EtiquetaView.vue';

const detalhes = { volumes: 3, pesoKg: 12.5, observacao: 'Frágil' };

describe('valores do envio', () => {
  it('monta remetente, destinatário e pedido já formatados', () => {
    const v = valoresDoEnvio(DADOS_EXEMPLO, detalhes);
    expect(v['destinatario.nome']).toBe('Cliente de Exemplo');
    expect(v['destinatario.documento']).toBe('CPF 529.982.247-25');
    expect(v['destinatario.endereco']).toBe('Rua do Cliente, 250 — Casa B');
    expect(v['destinatario.cep']).toBe('63500-123');
    expect(v['remetente.documento']).toBe('CNPJ 11.222.333/0001-81');
    expect(v['envio.origem']).toBe('Venda 41');
    expect(v['envio.peso']).toBe('12,5 kg');
    expect(v['nfe.homologacao']).toContain('SEM VALOR FISCAL');
  });

  it('sem NF-e não imprime linha de nota', () => {
    const venda: DadosEnvio = { ...DADOS_EXEMPLO, nfe: null };
    expect(valoresDoEnvio(venda, detalhes)['nfe.numero']).toBe('');
  });

  it('um jogo por volume, com o contador certo', () => {
    const etiquetas = etiquetasDosVolumes(valoresDoEnvio(DADOS_EXEMPLO, detalhes), 3);
    expect(etiquetas.map((e) => e['volume.contador'])).toEqual(['1/3', '2/3', '3/3']);
    expect(etiquetas[2]['volume.rotulo']).toBe('VOLUME 3 DE 3');
  });

  it('o DANFE usa o destinatário da NOTA, não o cadastro atual', () => {
    const cadastroMudou: DadosEnvio = {
      ...DADOS_EXEMPLO,
      destinatario: { ...DADOS_EXEMPLO.destinatario!, nome: 'Nome Novo do Cadastro' },
    };
    const v = valoresDoDanfe(cadastroMudou);
    expect(v['destinatario.nome']).toBe('CLIENTE DE EXEMPLO');
    expect(v['nfe.chave_formatada']).toBe(formatarChave(DADOS_EXEMPLO.nfe!.chave_acesso));
  });

  it('chave em grupos de 4', () => {
    expect(formatarChave('12345678')).toBe('1234 5678');
  });
});

describe('layouts do envio', () => {
  it.each([...PRESETS_VOLUME, ...PRESETS_DANFE].map((p) => [p.nome, p] as const))('%s cabe no papel', (_, preset) => {
    const { pagina, elementos } = preset.definicao;
    expect(problemasDaPagina(pagina)).toEqual([]);
    expect(problemasDosElementos(elementos, pagina)).toEqual([]);
  });

  it.each(PRESETS_DANFE.map((p) => [p.nome, p] as const))('%s: todo texto com pelo menos 6 pt (NT 2020.004)', (_, preset) => {
    for (const el of preset.definicao.elementos) {
      if (el.tipo === 'texto') expect(el.fonte_pt).toBeGreaterThanOrEqual(6);
    }
  });

  it('o DANFE desenha o código de barras da chave (44 dígitos em Code 128)', () => {
    const wrapper = mount(EtiquetaView, {
      props: { definicao: PRESETS_DANFE[0].definicao, valores: valoresDoDanfe(DADOS_EXEMPLO) },
    });
    expect(wrapper.text()).toContain('DANFE SIMPLIFICADO - ETIQUETA');
    expect(wrapper.text()).toContain('TIPO DE OPERAÇÃO: 1 - SAÍDA');
    expect(wrapper.find('svg').findAll('rect').length).toBeGreaterThan(20);
  });
});
