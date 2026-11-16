/**
 * A consulta de CNPJ mudou para `@/shared/services/cnpj.service` em 06/10/2026,
 * porque o cadastro de cliente PJ passou a usá-la também. Este arquivo só
 * reexporta, para quem ainda importa daqui.
 */
export { buscarDadosCNPJ } from '@/shared/services/cnpj.service';
export type { DadosCnpj as CNPJApiData } from '@/shared/services/cnpj.service';
