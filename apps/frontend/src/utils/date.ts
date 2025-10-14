import dayjs from 'dayjs';

export const formatDateTime = (iso: string) => dayjs(iso).format('MMM D, YYYY HH:mm');
export const formatDate = (iso: string) => dayjs(iso).format('MMM D, YYYY');
