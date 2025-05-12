import { createContext } from "react";
import { GeneratingBrief } from "../constants";
import { FeedBrief } from "../types";

interface BriefContext {
  activeBrief: FeedBrief;
  setActiveBrief: (brief: FeedBrief) => void;
}

export const BriefContext = createContext<BriefContext>({
  activeBrief: GeneratingBrief,
  setActiveBrief: () => {},
});
