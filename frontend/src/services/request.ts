interface ModifyFeedGroupRequest {
  title: string;
  desc: string;
  feedIds: number[];
}

interface ImportOpmlRequest {
  url?: string;
  content?: string;
}

export type { ModifyFeedGroupRequest, ImportOpmlRequest };