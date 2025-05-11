import { useContext, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getHistoryBriefs } from "../../services/FeedService";
import { FeedBrief } from "../../types";
import MenuCard from "../MenuCard";
import { BriefContext } from "../../contexts/BriefContext";
import { NoBrief } from "../../constants";

export default function BriefHistory() {
  const { setActiveBrief } = useContext(BriefContext);
  const { id } = useParams();
  const [briefs, setBriefs] = useState<FeedBrief[]>([]);
  useEffect(() => {
    const fetchBriefs = async () => {
      if (id) {
        const briefs = await getHistoryBriefs(parseInt(id));
        setBriefs(briefs);
        if (briefs.length > 0) {
          setActiveBrief(briefs[0]);
        } else {
          setActiveBrief(NoBrief);
        }
      }
    };
    fetchBriefs();
  }, [id]);
  return (
    <MenuCard>
      <div className="space-y-4">
        {/* Brief history items */}
        {briefs.length > 0 ? (
          briefs.map((brief) => (
            <div
              key={brief.id}
              className="p-4 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors duration-200"
              onClick={() => setActiveBrief(brief)}
            >
              <h3 className="text-lg font-semibold">{brief.title}</h3>
              <p className="text-sm text-gray-600 mt-1">
                Published: {new Date(brief.pubDate).toLocaleDateString()}
              </p>
            </div>
          ))
        ) : (
          <div className="p-4 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors duration-200">
            <p className="text-sm text-gray-600 mt-1">
              No briefs found for this group
            </p>
          </div>
        )}
      </div>
    </MenuCard>
  );
}
