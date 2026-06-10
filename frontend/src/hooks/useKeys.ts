import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { keysApi } from '@/api/endpoints/keys';
import type { CreateKeyPayload } from '@/api/types/api.types';

export const useKeys = () => {
  return useQuery({
    queryKey: ['keys'],
    queryFn: () => keysApi.list().then((res) => res.data),
  });
};

export const useAddKey = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateKeyPayload) => keysApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['keys'] }),
  });
};

export const useDeleteKey = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => keysApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['keys'] }),
  });
};
