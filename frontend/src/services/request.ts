import { Feed } from "../types";

interface ModifyFeedGroupRequest {
  title: string;
  desc: string;
  feedIds: number[];
}

interface ImportOpmlRequest {
  url?: string;
  content?: string;
}

export type ModifyFeedRequest = Omit<Feed, "id">;

export type { ImportOpmlRequest, ModifyFeedGroupRequest };
