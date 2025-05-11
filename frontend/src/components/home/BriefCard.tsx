import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import { getFeedBrief, getHomeFeeds } from "../../services/FeedService";
import { FeedBrief, FeedGroup } from "../../types";
import MainCard from "../MainCard";

interface BriefCardProps {
  briefId?: number;
}

const GeneratingBrief: FeedBrief = {
  id: 0,
  title: "Today Brief is generating...",
  content: "Please wait for a moment...",
  pubDate: new Date(),
  groupId: 0,
};

const BriefCard: React.FC<BriefCardProps> = ({ briefId }) => {
  const [brief, setBrief] = useState<FeedBrief>(GeneratingBrief);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const isHome = briefId === undefined;
  const [group, setGroup] = useState<FeedGroup | null>(null);
  useEffect(() => {
    const fetchTodayFeed = async () => {
      const data = await getHomeFeeds();
      if (data === null) {
        setLoading(false);
        const checkInterval = setInterval(async () => {
          try {
            const newData = await getHomeFeeds();
            if (newData !== null) {
              setBrief(newData.brief);
              setGroup(newData.group);
              clearInterval(checkInterval);
            }
          } catch (err) {
            console.error("Error checking brief status:", err);
            clearInterval(checkInterval);
            setError(
              "Failed to check content status. Please refresh the page."
            );
          }
        }, 3000);

        // Cleanup interval on component unmount
        return () => clearInterval(checkInterval);
      }
      setBrief(data.brief);
      setGroup(data.group);
    };

    const fetchBrief = async () => {
      if (briefId === undefined) {
        return;
      }
      const data = await getFeedBrief(briefId);
      if (data === null) {
        setLoading(false);
        setError("Failed to load content. Please try again later.");
        return;
      }
      setBrief(data);
    };

    if (isHome) {
      fetchTodayFeed();
    } else {
      fetchBrief();
    }
    setLoading(false);
  }, [briefId, isHome]);
  if (loading) {
    // Loading state
    return (
      <div className="mx-auto w-full h-full flex items-center justify-center p-6">
        <div className="text-gray-500">Loading content...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto w-full h-full flex items-center justify-center p-6">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <MainCard>
      {/* Card title */}
      {brief?.title && (
        <div className="mb-4">
          <h3 className="text-xl font-bold">{brief.title}</h3>
          <div className="mt-2 h-px bg-gradient-to-r from-gray-200 via-gray-400 to-gray-200"></div>
        </div>
      )}

      {/* Card content */}
      <div className="mb-4">
        <Markdown>{brief?.content || ""}</Markdown>
      </div>

      {/* Card footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        Published Date:{" "}
        {brief?.pubDate ? new Date(brief.pubDate).toLocaleDateString() : "N/A"}
        {isHome && (
          <>
            <br />
            Group: {group?.title}
          </>
        )}
      </div>
    </MainCard>
  );
};
export default BriefCard;
