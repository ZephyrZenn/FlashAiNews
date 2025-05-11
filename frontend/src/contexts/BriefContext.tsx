import { createContext } from "react";
import { FeedBrief } from "../types";

interface BriefContext {
  activeBrief: FeedBrief | null;
  setActiveBrief: (brief: FeedBrief) => void;
}

export const BriefContext = createContext<BriefContext>({
  activeBrief: null,
  setActiveBrief: () => {},
});
