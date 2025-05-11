interface CommonResult<T> {
    success: boolean;
    message: string;
    data: T;
}

interface FeedBrief {
  id: number;
  title: string;
  content: string;
  pubDate: Date;
  groupId: number;
}

interface FeedGroup {
  id: number;
  title: string;
  desc: string;
  feeds: Feed[];
}

interface Feed {
  id: number;
  title: string;
  url: string;
  description: string;
}

interface BriefWithGroup {
  brief: FeedBrief;
  group: FeedGroup;
}

export type { FeedBrief, FeedGroup, Feed, CommonResult, BriefWithGroup };
