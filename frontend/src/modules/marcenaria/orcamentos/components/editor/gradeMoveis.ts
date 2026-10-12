/**
 * Colunas da tabela "Ambientes e móveis" do editor: o cabeçalho (BlocoAmbientes),
 * a linha do ambiente (AmbienteCard) e a do móvel (MovelLinha) usam a MESMA
 * grade, senão "Preço" desalinha do valor (já aconteceu quando a coluna de
 * ações mudava de largura conforme o orçamento era editável ou não).
 *
 * Sem custos (vendedor sem permissão, D16) a coluna "Custo" não existe.
 * As classes ficam escritas por inteiro para o Tailwind encontrá-las. As três
 * linhas usam também o MESMO recuo lateral (px-4): padding diferente desloca as
 * colunas; o recuo do nome do móvel fica dentro da primeira célula.
 */
export const GRADE_MOVEIS_COM_CUSTO =
  'md:grid md:grid-cols-[minmax(0,2.2fr)_minmax(0,1.6fr)_3rem_minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)_6.5rem] md:gap-x-4';
export const GRADE_MOVEIS_SEM_CUSTO =
  'md:grid md:grid-cols-[minmax(0,2.2fr)_minmax(0,1.6fr)_3rem_minmax(0,1.2fr)_minmax(0,1fr)_6.5rem] md:gap-x-4';

export const gradeMoveis = (comCustos: boolean) => (comCustos ? GRADE_MOVEIS_COM_CUSTO : GRADE_MOVEIS_SEM_CUSTO);
