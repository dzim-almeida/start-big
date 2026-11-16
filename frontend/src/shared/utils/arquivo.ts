import { isTauri } from '@tauri-apps/api/core';

/** `cancelado`: o usuário fechou a janela "Salvar como" sem escolher local. */
export type ResultadoSalvarArquivo =
  | { cancelado: true }
  | { cancelado: false; caminho: string | null };

/**
 * Falha ao GRAVAR (não ao obter o conteúdo): a janela não abriu ou o Windows
 * recusou o arquivo. A mensagem já vem pronta para o usuário — quem chama
 * separa este caso do "não consegui buscar o documento".
 */
export class ErroAoSalvar extends Error {
  constructor(mensagem: string) {
    super(mensagem);
    this.name = 'ErroAoSalvar';
  }
}

const FILTROS: Record<string, string> = {
  pdf: 'PDF',
  xml: 'XML',
  zip: 'Arquivo ZIP',
  csv: 'Planilha CSV',
};

/**
 * Pergunta ao usuário onde salvar (janela "Salvar como" do Windows). Devolve
 * o caminho escolhido ou null se cancelou.
 *
 * Se a janela não abrir, é erro — não gravamos escondido na pasta de dados do
 * app: o usuário nunca achava o arquivo lá.
 */
async function perguntarOndeSalvar(nome: string): Promise<string | null> {
  try {
    const { save } = await import('@tauri-apps/plugin-dialog');
    const { downloadDir, join } = await import('@tauri-apps/api/path');
    const extensao = nome.split('.').pop()?.toLowerCase() ?? '';
    let sugestao = nome;
    try {
      sugestao = await join(await downloadDir(), nome);
    } catch {
      /* sem pasta Downloads — o Windows sugere a última usada */
    }
    return await save({
      defaultPath: sugestao,
      filters: FILTROS[extensao] ? [{ name: FILTROS[extensao], extensions: [extensao] }] : undefined,
    });
  } catch {
    throw new ErroAoSalvar('A janela "Salvar como" do Windows não abriu. Feche e abra o sistema e tente de novo.');
  }
}

/**
 * Entrega um arquivo ao usuário:
 * - No app (Tauri/WebView bloqueia download por blob): abre o "Salvar como"
 *   do Windows, grava onde o usuário escolher e tenta abrir no programa
 *   padrão. A janela libera a gravação naquele caminho (o plugin-dialog põe o
 *   arquivo escolhido no escopo do plugin-fs).
 * - No navegador (dev): download por blob; caminho null.
 *
 * Lança `ErroAoSalvar` quando não consegue gravar.
 */
export async function salvarArquivo(nome: string, conteudo: Blob): Promise<ResultadoSalvarArquivo> {
  if (isTauri()) {
    const caminho = await perguntarOndeSalvar(nome);
    if (caminho === null) return { cancelado: true };

    try {
      const { writeFile } = await import('@tauri-apps/plugin-fs');
      await writeFile(caminho, new Uint8Array(await conteudo.arrayBuffer()));
    } catch {
      throw new ErroAoSalvar(
        'O Windows não deixou gravar o arquivo. Se ele estiver aberto em outro programa, '
        + 'feche-o ou salve com outro nome.',
      );
    }

    try {
      const { openPath } = await import('@tauri-apps/plugin-opener');
      await openPath(caminho);
    } catch {
      /* sem permissão de abrir — o arquivo já está salvo no caminho devolvido */
    }
    return { cancelado: false, caminho };
  }

  const url = URL.createObjectURL(conteudo);
  const a = document.createElement('a');
  a.href = url;
  a.download = nome;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 0);
  return { cancelado: false, caminho: null };
}
