import axios from 'axios';
import type {
  ApiResponse,
  FeedBrief,
  FeedBriefListResponse,
  FeedBriefResponse,
  FeedGroup,
  FeedGroupDetailResponse,
  FeedGroupListResponse,
  FeedListResponse,
  Feed,
  ImportFeedsPayload,
  ModifyFeedPayload,
  ModifyGroupPayload,
  ModifySettingPayload,
  Setting,
  SettingResponse,
} from '@/types/api';

const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api';

const client = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const unwrap = async <T>(promise: Promise<{ data: ApiResponse<T> }>) => {
  const { data } = await promise;
  if (!data.success) {
    throw new Error(data.message || 'Request failed');
  }
  return data.data;
};

export const api = {
  // Briefs
  getLatestBrief: () => unwrap<FeedBrief | null>(client.get<FeedBriefResponse>('/')),
  getDefaultBriefs: () => unwrap<FeedBrief[]>(
    client.get<FeedBriefListResponse>('/briefs/default'),
  ),
  getTodayBriefByGroup: (groupId: number) =>
    unwrap<FeedBrief | null>(client.get<FeedBriefResponse>(`/briefs/${groupId}/today`)),
  getHistoryBriefByGroup: (groupId: number) =>
    unwrap<FeedBrief[]>(client.get<FeedBriefListResponse>(`/briefs/${groupId}/history`)),
  generateTodayBrief: () =>
    unwrap<null>(client.post<ApiResponse<null>>('/briefs/generate')),

  // Groups
  getGroups: () => unwrap<FeedGroup[]>(client.get<FeedGroupListResponse>('/groups/')),
  getGroupDetail: (groupId: number) =>
    unwrap<FeedGroup>(client.get<FeedGroupDetailResponse>(`/groups/${groupId}`)),
  createGroup: (payload: ModifyGroupPayload) =>
    unwrap<number>(client.post<ApiResponse<number>>('/groups/', payload)),
  updateGroup: (groupId: number, payload: ModifyGroupPayload) =>
    unwrap<void>(client.put<ApiResponse<void>>(`/groups/${groupId}`, payload)),
  deleteGroup: (groupId: number) =>
    unwrap<void>(client.delete<ApiResponse<void>>(`/groups/${groupId}`)),

  // Feeds
  getFeeds: () => unwrap<Feed[]>(client.get<FeedListResponse>('/feeds/')),
  createFeed: (payload: ModifyFeedPayload) =>
    unwrap<void>(client.post<ApiResponse<void>>('/feeds/', payload)),
  updateFeed: (feedId: number, payload: ModifyFeedPayload) =>
    unwrap<void>(client.put<ApiResponse<void>>(`/feeds/${feedId}`, payload)),
  deleteFeed: (feedId: number) => unwrap<void>(client.delete<ApiResponse<void>>(`/feeds/${feedId}`)),
  importFeeds: (payload: ImportFeedsPayload) =>
    unwrap<void>(client.post<ApiResponse<void>>('/feeds/import', payload)),

  // Settings
  getSetting: () => unwrap<Setting>(client.get<SettingResponse>('/setting/')),
  updateSetting: (payload: ModifySettingPayload) =>
    unwrap<void>(client.post<ApiResponse<void>>('/setting/', payload)),
  updateBriefTime: (briefTime: string) =>
    unwrap<void>(client.post<ApiResponse<void>>('/setting/brief-time', { briefTime })),
};

export type { Feed, FeedGroup, FeedBrief, Setting };
export { baseURL };
