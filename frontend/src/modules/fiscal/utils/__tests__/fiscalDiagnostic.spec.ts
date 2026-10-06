import { describe, expect, it } from 'vitest';
import { analisarDiagnosticoFiscal } from '../fiscalDiagnostic';
import { lerChaveDaMensagem } from '../fiscalDiagnosticCodigos';
import type { DocumentoFiscalRead } from '../../types/fiscal.types';

/** As três rejeições da primeira NF-e real em produção (06/10/2026). */
function doc(cStat: number | null, mensagem: string): DocumentoFiscalRead {
  return { codigo_status_sefaz: cStat, mensagem_sefaz: mensagem, motivo_rejeicao: null } as unknown as DocumentoFiscalRead;
}

const MSG_481 = 'Rejeição: Código Regime Tributário do emitente diverge do cadastro na SEFAZ';
const MSG_539 =
  'Rejeição: Duplicidade de NF-e com diferença na Chave de Acesso ' +
  '[chNFe:35260958348941000109550020000000041750446210][nRec:351025570568140]';
const MSG_305 = 'Rejeição: Destinatário bloqueado na UF';

describe('diagnóstico pelo cStat', () => {
  it('481 aponta o regime tributário, não o certificado', () => {
    const d = analisarDiagnosticoFiscal(doc(481, MSG_481));
    expect(d.titulo).toMatch(/Regime Tributário/);
    expect(d.comoResolver).toMatch(/4 - MEI/);
    expect(d.comoResolver).not.toMatch(/certificado/i);
    expect(d.acaoPrincipal?.tipo).toBe('CONFIG_FISCAL');
  });

  it('539 diz qual número já foi usado e quando, e manda ao Centro Fiscal', () => {
    const d = analisarDiagnosticoFiscal(doc(539, MSG_539));
    expect(d.categoria).toBe('DUPLICIDADE');
    expect(d.explicacao).toContain('nº 4 da série 2');
    expect(d.explicacao).toContain('09/2026');
    expect(d.comoResolver).not.toMatch(/CSOSN/);
    expect(d.acaoPrincipal?.tipo).toBe('CENTRO_FISCAL');
  });

  it('305 diz que o cliente está bloqueado, não "revise os dados da venda"', () => {
    const d = analisarDiagnosticoFiscal(doc(305, MSG_305));
    expect(d.categoria).toBe('CLIENTE');
    expect(d.titulo).toMatch(/Bloqueado/);
    expect(d.comoResolver).toMatch(/CCC|SINTEGRA/);
  });

  it('207 e 209 são do EMITENTE, não do cliente', () => {
    expect(analisarDiagnosticoFiscal(doc(207, 'Rejeição: CNPJ do emitente inválido')).titulo).toMatch(/Sua Empresa/);
    expect(analisarDiagnosticoFiscal(doc(209, 'Rejeição: IE do emitente inválida')).titulo).toMatch(/Sua Empresa/);
  });

  it('204 manda consultar, não reemitir', () => {
    expect(analisarDiagnosticoFiscal(doc(204, 'Rejeição: Duplicidade de NF-e')).acaoPrincipal?.tipo).toBe('RECONSULTAR');
  });
});

describe('palavras-chave continuam valendo para o que não tem código na tabela', () => {
  it('sem cStat, erro de configuração da plataforma ainda cai em configuração', () => {
    const d = analisarDiagnosticoFiscal(doc(null, 'Empresa não possui configuração fiscal ativa.'));
    expect(d.categoria).toBe('CONFIGURACAO');
  });

  it('com cStat desconhecido, "emitente" na mensagem NÃO vira problema de certificado', () => {
    const d = analisarDiagnosticoFiscal(doc(999, 'Rejeição: algo sobre o emitente'));
    expect(d.categoria).toBe('GENERICO');
  });

  it('NCM continua no bloco de produto', () => {
    expect(analisarDiagnosticoFiscal(doc(778, 'Rejeição: Informado NCM inexistente')).categoria).toBe('PRODUTO');
  });
});

describe('lerChaveDaMensagem', () => {
  it('lê série, número e mês da chave devolvida pela SEFAZ', () => {
    expect(lerChaveDaMensagem(MSG_539)).toMatchObject({ serie: 2, numero: 4, mes: '09', ano: '2026' });
  });

  it('sem chave na mensagem, devolve null', () => {
    expect(lerChaveDaMensagem('Rejeição: qualquer')).toBeNull();
    expect(lerChaveDaMensagem(null)).toBeNull();
  });
});
