/**
 * Funções puras do lava-rápido (comanda e pátio). Sem Vue: testáveis sozinhas.
 */

/** Placa como o balcão digita → como se grava: maiúscula, sem espaço nem hífen. */
export function normalizarPlaca(texto: string): string {
  return texto.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 10);
}

/** Só os dígitos do telefone, com o 55 do Brasil na frente (para o wa.me). */
export function telefoneWhatsApp(telefone: string | null | undefined): string | null {
  const digitos = (telefone ?? '').replace(/\D/g, '');
  if (digitos.length < 10) return null;                         // sem DDD não dá para chamar
  return digitos.startsWith('55') && digitos.length >= 12 ? digitos : `55${digitos}`;
}

/** Mensagem padrão do "Pronto" (SPEC-00 O8). */
export function mensagemPronto(cliente: string | null, veiculo: string | null, placa: string | null): string {
  const nome = (cliente ?? '').split(' ')[0];
  const oQue = [veiculo, placa ? `placa ${placa}` : null].filter(Boolean).join(', ');
  return `Olá${nome ? `, ${nome}` : ''}! Seu ${oQue || 'veículo'} está pronto para retirada. Obrigado!`;
}

/** Link `wa.me` pronto para abrir; `null` sem telefone utilizável. */
export function linkWhatsApp(telefone: string | null | undefined, mensagem: string): string | null {
  const numero = telefoneWhatsApp(telefone);
  return numero ? `https://wa.me/${numero}?text=${encodeURIComponent(mensagem)}` : null;
}

/**
 * Previsão de entrega: agora + soma das durações dos serviços (SPEC-00 O4).
 * `null` quando nenhum serviço tem duração — melhor sem previsão que uma errada.
 */
export function previsaoDeEntrega(agora: Date, duracoesMinutos: Array<number | null | undefined>): Date | null {
  const total = duracoesMinutos.reduce<number>((soma, d) => soma + (d && d > 0 ? d : 0), 0);
  if (total <= 0) return null;
  return new Date(agora.getTime() + total * 60_000);
}

/** "há 25 min", "há 1 h 10 min" — quanto tempo o veículo está no pátio. */
export function tempoNoPatio(entradaIsoUtc: string, agora: Date = new Date()): string {
  // O backend manda UTC sem "Z"; sem ele o navegador leria como hora local.
  const iso = /[zZ]|[+-]\d{2}:?\d{2}$/.test(entradaIsoUtc) ? entradaIsoUtc : `${entradaIsoUtc}Z`;
  const minutos = Math.max(0, Math.floor((agora.getTime() - new Date(iso).getTime()) / 60_000));
  if (minutos < 60) return `há ${minutos} min`;
  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;
  return resto ? `há ${horas} h ${resto} min` : `há ${horas} h`;
}

/** Hora local "14:40" de um instante UTC do backend. */
export function horaLocal(isoUtc: string | null | undefined): string {
  if (!isoUtc) return '';
  const iso = /[zZ]|[+-]\d{2}:?\d{2}$/.test(isoUtc) ? isoUtc : `${isoUtc}Z`;
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

/** Centavos → "R$ 40,00". */
export function reais(centavos: number): string {
  return (centavos / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}
