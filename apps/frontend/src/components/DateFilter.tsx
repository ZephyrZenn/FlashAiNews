import { Calendar } from 'lucide-react';

interface DateFilterProps {
  startDate?: string;
  endDate?: string;
  onStartDateChange?: (date: string) => void;
  onEndDateChange?: (date: string) => void;
}

export const DateFilter = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: DateFilterProps) => {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Calendar size={14} className="text-cyan-400" />
        <span className="text-[10px] font-black text-cyan-400 uppercase tracking-[0.4em]">时间筛选</span>
      </div>
      <div className="flex gap-2 items-center">
        <input
          type="date"
          value={startDate || ''}
          onChange={(e) => onStartDateChange?.(e.target.value)}
          className="bg-black/60 border border-white/10 rounded-xl px-3 py-2 text-white font-mono text-sm outline-none focus:border-cyan-500 transition-all"
          placeholder="开始日期"
        />
        <span className="text-slate-500 text-xs">→</span>
        <input
          type="date"
          value={endDate || ''}
          onChange={(e) => onEndDateChange?.(e.target.value)}
          className="bg-black/60 border border-white/10 rounded-xl px-3 py-2 text-white font-mono text-sm outline-none focus:border-cyan-500 transition-all"
          placeholder="结束日期"
        />
      </div>
    </div>
  );
};

