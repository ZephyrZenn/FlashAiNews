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
  group?: FeedGroup;
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

export type { FeedBrief, FeedGroup, Feed, CommonResult };
