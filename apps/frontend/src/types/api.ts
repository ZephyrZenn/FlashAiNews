export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface Feed {
  id: number;
  title: string;
  url: string;
  desc: string;
}

export interface FeedGroup {
  id: number;
  title: string;
  desc: string;
  feeds: Feed[];
}

export interface FeedBrief {
  id: number;
  groupId: number;
  content: string;
  pubDate: string;
  group?: FeedGroup;
}

export interface ModelSetting {
  name?: string;
  model: string;
  provider: string;
  apiKey: string;
  baseUrl: string;
}

export interface Setting {
  model: ModelSetting;
}

export type FeedGroupListResponse = ApiResponse<FeedGroup[]>;
export type FeedGroupDetailResponse = ApiResponse<FeedGroup>;
export type FeedListResponse = ApiResponse<Feed[]>;
export type FeedBriefResponse = ApiResponse<FeedBrief | null>;
export type FeedBriefListResponse = ApiResponse<FeedBrief[]>;
export type SettingResponse = ApiResponse<Setting>;

export interface ModifyGroupPayload {
  title: string;
  desc: string;
  feedIds: number[];
}

export interface ModifyFeedPayload {
  title: string;
  desc: string;
  url: string;
}

export interface ImportFeedsPayload {
  url?: string;
  content?: string;
}

export interface ModifySettingPayload {
  model?: {
    model: string;
    provider: string;
    apiKey: string;
    baseUrl?: string;
  };
}

export interface Schedule {
  id: string;
  time: string; // HH:MM format
  focus: string;
  groupIds: number[];
  enabled: boolean;
}

export interface CreateSchedulePayload {
  time: string; // HH:MM format
  focus: string;
  groupIds: number[];
}

export interface UpdateSchedulePayload {
  time?: string; // HH:MM format
  focus?: string;
  groupIds?: number[];
  enabled?: boolean;
}

export type ScheduleListResponse = ApiResponse<Schedule[]>;
export type ScheduleResponse = ApiResponse<Schedule>;
