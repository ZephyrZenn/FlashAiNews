export const queryKeys = {
  groups: ['groups'] as const,
  groupDetail: (groupId: number) => ['groups', groupId] as const,
  feeds: ['feeds'] as const,
  latestBrief: ['briefs', 'latest'] as const,
  briefs: (startDate?: string, endDate?: string) => ['briefs', startDate, endDate] as const,
  defaultBriefs: ['briefs', 'default'] as const,
  settings: ['setting'] as const,
  schedules: ['schedules'] as const,
  schedule: (scheduleId: string) => ['schedules', scheduleId] as const,
};
