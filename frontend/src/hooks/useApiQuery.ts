import {
  useQuery,
  type QueryKey,
  type UseQueryOptions,
  type UseQueryResult,
} from '@tanstack/react-query';

type ApiQueryOptions<TData, TQueryKey extends QueryKey> = Omit<
  UseQueryOptions<TData, Error, TData, TQueryKey>,
  'queryKey' | 'queryFn'
>;

export function useApiQuery<TData, TQueryKey extends QueryKey = QueryKey>(
  queryKey: TQueryKey,
  queryFn: () => Promise<TData>,
  options?: ApiQueryOptions<TData, TQueryKey>,
): UseQueryResult<TData, Error> {
  return useQuery<TData, Error, TData, TQueryKey>({
    queryKey,
    queryFn,
    ...(options ?? {}),
  });
}
