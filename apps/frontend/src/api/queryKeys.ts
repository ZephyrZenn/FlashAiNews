export const queryKeys = {
  groups: ['groups'] as const,
  groupDetail: (groupId: number) => ['groups', groupId] as const,
  feeds: ['feeds'] as const,
  latestBrief: ['briefs', 'latest'] as const,
  defaultBriefs: ['briefs', 'default'] as const,
  todayBrief: (groupId: number) => ['briefs', 'today', groupId] as const,
  historyBrief: (groupId: number) => ['briefs', 'history', groupId] as const,
  setting: ['setting'] as const,
  schedules: ['schedules'] as const,
  schedule: (scheduleId: string) => ['schedules', scheduleId] as const,
};
