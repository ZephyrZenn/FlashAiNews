import { useMutation, type UseMutationOptions, type UseMutationResult } from '@tanstack/react-query';

export function useApiMutation<TData, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: UseMutationOptions<TData, Error, TVariables>,
): UseMutationResult<TData, Error, TVariables> {
  return useMutation<TData, Error, TVariables>({
    mutationFn,
    ...options,
  });
}
