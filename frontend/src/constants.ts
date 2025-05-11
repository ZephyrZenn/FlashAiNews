import { FeedBrief } from "./types";

const BASE_URL = "http://localhost:8000";

const GeneratingBrief: FeedBrief = {
    id: 0,
    title: "Today Brief is generating...",
    content: "Please wait for a moment...",
    pubDate: new Date(),
  groupId: 0,
};

const NoBrief: FeedBrief = {
  id: 0,
  title: "There is no brief for this group",
  content: "Please select another group",
  pubDate: new Date(),
  groupId: 0,
};

export { BASE_URL, GeneratingBrief, NoBrief };
