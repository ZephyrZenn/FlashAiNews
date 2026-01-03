import dayjs from 'dayjs';

export const formatDateTime = (iso: string) => dayjs(iso).format('MMM D, YYYY HH:mm');
export const formatDate = (iso: string) => dayjs(iso).format('MMM D, YYYY');

export type DatePreset = 'today' | 'week' | 'month' | '3months' | 'all';

export interface DateRange {
  start?: string;
  end?: string;
}

export function isDateInRange(date: string, startDate?: string, endDate?: string): boolean {
  const dateObj = dayjs(date);
  if (startDate && endDate) {
    return dateObj.isAfter(dayjs(startDate).startOf('day')) && dateObj.isBefore(dayjs(endDate).endOf('day'));
  }
  if (startDate) {
    return dateObj.isAfter(dayjs(startDate).startOf('day')) || dateObj.isSame(dayjs(startDate).startOf('day'));
  }
  if (endDate) {
    return dateObj.isBefore(dayjs(endDate).endOf('day')) || dateObj.isSame(dayjs(endDate).endOf('day'));
  }
  return true;
}

export function getDateRangePreset(preset: DatePreset): DateRange {
  const now = dayjs();
  switch (preset) {
    case 'today':
      return {
        start: now.startOf('day').toISOString(),
        end: now.endOf('day').toISOString(),
      };
    case 'week':
      return {
        start: now.startOf('week').toISOString(),
        end: now.endOf('day').toISOString(),
      };
    case 'month':
      return {
        start: now.startOf('month').toISOString(),
        end: now.endOf('day').toISOString(),
      };
    case '3months':
      return {
        start: now.subtract(3, 'month').startOf('day').toISOString(),
        end: now.endOf('day').toISOString(),
      };
    case 'all':
    default:
      return {};
  }
}
