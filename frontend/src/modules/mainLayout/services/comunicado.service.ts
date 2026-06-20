import api from '@/api/axios'

export interface ComunicadoAutor {
  id: number
  nome: string
}

export interface Comunicado {
  id: number
  titulo: string
  mensagem: string
  criado_em: string
  autor: ComunicadoAutor | null
  lido: boolean
}

export async function getComunicados(): Promise<Comunicado[]> {
  const { data } = await api.get<Comunicado[]>('/comunicados/')
  return data
}

export async function criarComunicado(titulo: string, mensagem: string): Promise<Comunicado> {
  const { data } = await api.post<Comunicado>('/comunicados/', { titulo, mensagem })
  return data
}

export async function marcarComunicadoLido(id: number): Promise<void> {
  await api.put(`/comunicados/${id}/ler`)
}
