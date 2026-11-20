import { useQuery } from '@tanstack/vue-query'
import { getAvisosBackup } from '../../services/backup.service'
import { REFETCH_CONFIG } from '@/core/config/queryIntervals'

export const BACKUP_AVISOS_KEY = 'backup-avisos'

/**
 * Avisos da tela de backup (LIC-08). Uma "query" do TanStack Query busca o dado,
 * guarda em cache e busca de novo de tempos em tempos (o ciclo de envio roda a
 * cada hora, então um aviso pode aparecer ou sumir enquanto a tela está aberta).
 */
export function useAvisosBackupQuery() {
  return useQuery({
    queryKey: [BACKUP_AVISOS_KEY],
    queryFn: getAvisosBackup,
    staleTime: REFETCH_CONFIG,
    refetchInterval: REFETCH_CONFIG,
  })
}
