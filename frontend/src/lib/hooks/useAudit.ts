'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAudit,
  getAuditReport,
  createAudit,
  listAudits,
  deleteAudit,
  type CreateAuditRequest,
  type ListAuditsParams,
} from '@/lib/api';

export function useAudit(id: string) {
  return useQuery({
    queryKey: ['audit', id],
    queryFn: () => getAudit(id),
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll while processing
      if (data?.status === 'queued' || data?.status === 'processing') {
        return 5000; // 5 seconds
      }
      return false;
    },
  });
}

export function useAuditReport(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['audit', id, 'report'],
    queryFn: () => getAuditReport(id),
    enabled,
  });
}

export function useAudits(params?: ListAuditsParams) {
  return useQuery({
    queryKey: ['audits', params],
    queryFn: () => listAudits(params),
  });
}

export function useCreateAudit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAuditRequest) => createAudit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits'] });
    },
  });
}

export function useDeleteAudit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteAudit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits'] });
    },
  });
}
