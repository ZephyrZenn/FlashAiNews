import { useState, useMemo, useEffect } from 'react';
import { ChevronRight, X, FileText, List } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '@/api/client';
import { queryKeys } from '@/api/queryKeys';
import { useApiQuery } from '@/hooks/useApiQuery';
import { formatDate } from '@/utils/date';
import { Layout } from '@/components/Layout';
import { DateFilter } from '@/components/DateFilter';
import type { FeedBrief } from '@/types/api';

// Card colors for visual variety - matching t.tsx exactly
const cardStyles = [
  { color: 'bg-amber-50', rotation: '-rotate-1' },
  { color: 'bg-blue-50', rotation: 'rotate-1' },
  { color: 'bg-emerald-50', rotation: '-rotate-0.5' },
  { color: 'bg-rose-50', rotation: 'rotate-0.5' },
  { color: 'bg-violet-50', rotation: '-rotate-1' },
  { color: 'bg-cyan-50', rotation: 'rotate-1' },
];

const getCardStyle = (index: number) => {
  return cardStyles[index % cardStyles.length];
};

// 简单 slug 生成，供标题锚点使用
const slugify = (text: string) =>
  text
    .toLowerCase()
    .trim()
    .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
    .replace(/^-+|-+$/g, '');

// 提取大纲（h1-h3）
interface Heading {
  level: number;
  text: string;
  id: string;
}

const extractHeadings = (content: string): Heading[] => {
  const headings: Heading[] = [];
  const lines = content.split('\n');
  lines.forEach((line) => {
    const match = line.match(/^(#{1,6})\s+(.+)$/);
    if (match) {
      const level = match[1].length;
      const text = match[2].trim();
      const id = `${match[1].length}-${slugify(text) || Math.random().toString(36).slice(2)}`;
      headings.push({ level, text, id });
    }
  });
  return headings;
};

// Key points: 优先用二级标题，按空间限制数量
const extractKeyPoints = (content: string, maxItems = 4): string[] => {
  const h2Titles = extractHeadings(content)
    .filter((h) => h.level === 2)
    .map((h) => h.text);

  if (h2Titles.length > 0) {
    return h2Titles.slice(0, maxItems);
  }

  // 若无二级标题，退回原有逻辑
  const cleaned = content
    .replace(/^#+\s+.+$/gm, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\[(.+?)\]\(.+?\)/g, '$1')
    .trim();

  const points: string[] = [];
  const paragraphs = cleaned.split(/\n\s*\n/).filter((p) => p.trim().length > 0);

  if (paragraphs.length >= 2) {
    for (const para of paragraphs) {
      const firstSentence = para
        .split(/[。.！!？?]/)[0]
        .replace(/\s+/g, ' ')
        .trim();
      if (firstSentence.length >= 20 && firstSentence.length <= 180) {
        points.push(firstSentence);
      } else if (firstSentence.length > 180) {
        points.push(firstSentence.slice(0, 177) + '...');
      }
      if (points.length >= maxItems) break;
    }
  }

  if (points.length < maxItems) {
    const sentences = cleaned
      .replace(/\n/g, ' ')
      .split(/[。.！!？?]/)
      .map((s) => s.trim())
      .filter((s) => s.length >= 20 && s.length <= 180);
    const needed = maxItems - points.length;
    points.push(...sentences.slice(0, needed));
  }

  return points.length > 0 ? points : ['暂无内容预览'];
};

const getTodayString = () => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};

const SummaryPage = () => {
  const [selectedBrief, setSelectedBrief] = useState<FeedBrief | null>(null);
  // 移动端默认隐藏大纲，桌面端默认显示
  const [showOutline, setShowOutline] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth >= 768; // md breakpoint
    }
    return true;
  });
  const today = getTodayString();
  const [startDate, setStartDate] = useState<string>(today);
  const [endDate, setEndDate] = useState<string>(today);

  // 当进入详情页时，根据屏幕尺寸设置大纲显示状态
  useEffect(() => {
    if (selectedBrief) {
      const isMobile = window.innerWidth < 768; // md breakpoint
      setShowOutline(!isMobile);
    }
  }, [selectedBrief]);

  // 使用新的getBriefs API，默认获取当日
  const { data: briefs, isLoading } = useApiQuery<FeedBrief[]>(
    queryKeys.briefs(startDate, endDate),
    () => api.getBriefs(startDate, endDate)
  );

  // 计算要显示的简报列表
  const displayBriefs = useMemo(() => briefs || [], [briefs]);

  // Detail view - exactly matching t.tsx selectedSummary view
  if (selectedBrief) {
    const cardStyle = getCardStyle(selectedBrief.id);
    const headings = extractHeadings(selectedBrief.content);
    return (
      <Layout showBackButton onBackClick={() => setSelectedBrief(null)}>
        <div className="h-full p-2 md:p-4 flex items-center justify-center bg-slate-100/30">
          <div className={`w-full max-w-7xl h-full flex flex-col bg-white shadow-2xl rounded-sm overflow-hidden relative ${cardStyle.color}`}>
            <div className="p-4 md:p-12 pb-4 md:pb-6 border-b border-black/5 mx-2 md:mx-12 shrink-0">
              <div className="flex justify-between items-start">
                {/* Group tags */}
                <div className="flex flex-wrap gap-2">
                  {selectedBrief.groups && selectedBrief.groups.length > 0 ? (
                    selectedBrief.groups.map((group) => (
                      <span
                        key={group.id}
                        className="px-4 py-2 bg-white/60 backdrop-blur-sm border border-black/10 text-slate-700 rounded-xl text-sm font-bold shadow-sm"
                      >
                        {group.title}
                      </span>
                    ))
                  ) : (
                    <span className="px-4 py-2 bg-white/60 backdrop-blur-sm border border-black/10 text-slate-400 rounded-xl text-sm">
                      未分组
                    </span>
                  )}
                </div>
                {/* Close button */}
                <X
                  className="cursor-pointer text-slate-300 hover:text-slate-800 transition-colors shrink-0 ml-4"
                  onClick={() => setSelectedBrief(null)}
                />
              </div>
            </div>
            <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">
              {/* 主内容区域 */}
              <div className="flex-1 overflow-y-auto px-4 md:px-12 py-6 md:py-10 text-sm md:text-md leading-[2.0] text-slate-700 font-medium custom-scrollbar prose prose-slate max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ node, ...props }) => {
                      const text = String(props.children ?? '');
                      const id = `h1-${slugify(text)}`;
                      return <h1 id={id} {...props} />;
                    },
                    h2: ({ node, ...props }) => {
                      const text = String(props.children ?? '');
                      const id = `h2-${slugify(text)}`;
                      return <h2 id={id} {...props} />;
                    },
                    h3: ({ node, ...props }) => {
                      const text = String(props.children ?? '');
                      const id = `h3-${slugify(text)}`;
                      return <h3 id={id} {...props} />;
                    },
                  }}
                >
                  {selectedBrief.content}
                </ReactMarkdown>
              </div>

              {/* 大纲侧边栏 - 只在展开时渲染 */}
              {headings.length > 0 && showOutline && (
                <div className="w-full md:w-64 border-t md:border-t-0 md:border-l border-black/5 bg-white/70 backdrop-blur-sm shrink-0 max-h-[40vh] md:max-h-none">
                  <div className="sticky top-0 p-4 md:p-6 max-h-full overflow-y-auto custom-scrollbar">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                        <List size={14} />
                        文章大纲
                      </h3>
                      <button
                        onClick={() => setShowOutline(false)}
                        className="text-slate-400 hover:text-slate-700 transition-colors text-xs"
                      >
                        隐藏
                      </button>
                    </div>
                    <nav className="space-y-1">
                      {headings.map((heading, index) => (
                        <a
                          key={index}
                          href={`#${heading.id}`}
                          className={`block py-1.5 px-3 rounded-md text-xs transition-colors hover:bg-slate-100 ${
                            heading.level === 1
                              ? 'font-bold text-slate-800'
                              : heading.level === 2
                              ? 'font-semibold text-slate-700 ml-2'
                              : 'text-slate-600 ml-4'
                          }`}
                          style={{ marginLeft: `${(heading.level - 1) * 0.75}rem` }}
                          onClick={(e) => {
                            e.preventDefault();
                            const el = document.getElementById(
                              `${heading.level === 1 ? 'h1' : heading.level === 2 ? 'h2' : 'h3'}-${slugify(heading.text)}`
                            );
                            if (el) {
                              el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            }
                          }}
                        >
                          {heading.text}
                        </a>
                      ))}
                    </nav>
                  </div>
                </div>
              )}
              
              {/* 显示按钮 - 浮动在右侧边缘，不占据布局空间 */}
              {headings.length > 0 && !showOutline && (
                <button
                  onClick={() => setShowOutline(true)}
                  className="absolute right-0 bottom-4 md:bottom-auto md:top-1/2 md:-translate-y-1/2 -translate-x-4 w-12 h-12 md:w-10 md:h-20 bg-white/90 backdrop-blur-sm border border-black/10 rounded-l-lg md:rounded-l-lg shadow-lg flex flex-col items-center justify-center gap-1 text-slate-400 hover:text-slate-700 hover:bg-white transition-all z-10 min-w-[44px] min-h-[44px]"
                  title="显示大纲"
                >
                  <List size={18} />
                  <span className="text-[10px] font-medium hidden md:inline">显示</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center">
          <div className="text-slate-400 text-sm">加载中...</div>
        </div>
      </Layout>
    );
  }

  // Empty state
  if (!displayBriefs || displayBriefs.length === 0) {
    const emptyMessage = startDate || endDate 
      ? '所选时间段内未找到摘要'
      : '暂无今日摘要';
    const emptyDetail = startDate || endDate
      ? '请调整时间范围或返回查看今日摘要。'
      : '系统尚未生成今日的 AI 摘要。您可以前往「AI 实时总结」手动生成，或等待定时任务自动执行。';
    
    return (
      <Layout>
        <div className="h-full p-4 md:p-12 custom-scrollbar overflow-y-auto">
          <div className="max-w-7xl mx-auto">
            {/* Date filter */}
            <div className="mb-6 md:mb-8 p-4 md:p-6 bg-white rounded-[2rem] border border-slate-100 shadow-sm">
              <DateFilter
                startDate={startDate}
                endDate={endDate}
                onStartDateChange={setStartDate}
                onEndDateChange={setEndDate}
              />
            </div>
            
            {/* Empty state */}
            <div className="flex flex-col items-center justify-center text-center pt-6 md:pt-12">
              <div className="relative mb-6 md:mb-8">
                <div className="absolute inset-0 bg-indigo-500/20 blur-[40px] rounded-full" />
                <div className="relative p-6 md:p-8 bg-white border border-slate-100 rounded-[2.5rem] shadow-xl">
                  <FileText size={40} className="md:w-12 md:h-12 text-indigo-600" />
                </div>
              </div>
              <h2 className="text-2xl md:text-3xl font-black text-slate-800 mb-3 px-4">{emptyMessage}</h2>
              <p className="text-slate-400 max-w-md leading-relaxed px-4 text-sm md:text-base">
                {emptyDetail}
              </p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  // Grid view - exactly matching t.tsx stream view
  return (
    <Layout>
      <div className="h-full overflow-y-auto p-4 md:p-12 custom-scrollbar">
        <div className="max-w-7xl mx-auto">
          {/* Date filter */}
          <div className="mb-6 md:mb-8 p-4 md:p-6 bg-white rounded-[2rem] border border-slate-100 shadow-sm">
            <DateFilter
              startDate={startDate}
              endDate={endDate}
              onStartDateChange={setStartDate}
              onEndDateChange={setEndDate}
            />
          </div>

          {/* Grid view */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 md:gap-x-12 gap-y-8 md:gap-y-16">
            {displayBriefs.map((brief, index) => {
              const cardStyle = getCardStyle(index);
              const keyPoints = extractKeyPoints(brief.content);
              const groupTitle = brief.groups?.[0]?.title || '分组';
              
              return (
                <div
                  key={brief.id}
                  onClick={() => setSelectedBrief(brief)}
                  className={`group relative p-6 md:p-8 cursor-pointer transition-all duration-500 hover:scale-[1.03] ${cardStyle.color} ${cardStyle.rotation} rounded-sm shadow-sm hover:shadow-2xl min-h-[280px] md:h-[340px] flex flex-col border border-black/5`}
                >
                  {/* Paper clip effect */}
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-24 h-8 bg-white/40 backdrop-blur-[6px] -rotate-1 border border-white/40 z-0" />
                  
                  {/* Header */}
                  <div className="flex justify-between items-center mb-4 md:mb-6 text-[10px] font-black uppercase tracking-widest opacity-40">
                    <span className="truncate">{groupTitle}</span>
                    <span className="text-[9px] md:text-[10px]">{formatDate(brief.pubDate)}</span>
                  </div>
                  
                  {/* Key points */}
                  <ul className="space-y-3 md:space-y-4 mb-6 md:mb-8 text-sm md:text-[15px] leading-relaxed text-slate-800 font-medium flex-1 overflow-hidden">
                    {keyPoints.map((point, i) => (
                      <li key={i} className="flex gap-3">
                        <span className="shrink-0 mt-2 w-1 h-1 rounded-full bg-slate-400" />
                        <span className="line-clamp-2">{point}</span>
                      </li>
                    ))}
                  </ul>
                  
                  {/* Footer */}
                  <div className="mt-auto border-t border-black/5 text-[10px] font-black opacity-30 flex justify-end items-center uppercase tracking-widest">
                    <ChevronRight size={14} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default SummaryPage;
