import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from './client'
import type {
  Asset360,
  OperationsIntelligenceResponse,
  KnowledgeSearchResponse,
  OperationsSummary,
  PriorityAssets,
  Reliability,
} from './types'

export const useReliability = () =>
  useQuery({ queryKey: ['reliability'], queryFn: () => api.get<Reliability>('/api/reliability') })

export const useOperationsSummary = () =>
  useQuery({ queryKey: ['ops-summary'], queryFn: () => api.get<OperationsSummary>('/api/operations/summary') })

export const usePriorityAssets = (limit: number) =>
  useQuery({
    queryKey: ['assets', limit],
    queryFn: () => api.get<PriorityAssets>(`/api/assets?limit=${limit}`),
  })

export const useAsset360 = (assetId: string | undefined) =>
  useQuery({
    queryKey: ['asset', assetId],
    queryFn: () => api.get<Asset360>(`/api/assets/${encodeURIComponent(assetId!)}`),
    enabled: !!assetId,
  })

export interface SearchParams {
  query: string
  asset_id?: string | null
  document_type?: string | null
  num_results?: number
}

export const useKnowledgeSearch = (params: SearchParams | null) =>
  useQuery({
    queryKey: ['search', params],
    queryFn: () => api.post<KnowledgeSearchResponse>('/api/knowledge/search', params),
    enabled: !!params && params.query.trim().length >= 2,
  })

export const useDocumentTypes = () =>
  useQuery({
    queryKey: ['doc-types'],
    queryFn: () => api.get<{ document_types: string[] }>('/api/meta/document-types'),
    staleTime: Infinity,
  })

export const useOperationsIntelligence = () =>
  useMutation({
    mutationFn: (req: { question: string; asset_id?: string | null }) =>
      api.post<OperationsIntelligenceResponse>('/api/operations-intelligence', req),
  })
