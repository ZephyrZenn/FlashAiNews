import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import { getFeedBrief } from "../services/FeedService";
import { FeedBrief } from "../types";

interface BriefCardProps {
  briefId?: number; // 使用可选参数
}

const BriefCard: React.FC<BriefCardProps> = ({ briefId }) => {
  const [brief, setBrief] = useState<FeedBrief | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getFeedBrief(briefId);

        setBrief(data);
      } catch (err) {
        console.error("Error fetching feed:", err);
        setError("Failed to load content. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [briefId]); // 只在 briefId 变化时重新获取数据
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
    <div className="mx-auto w-full h-full min-h-[250px] p-6">
      {/* Card with layered shadow effect */}
      <div className="relative">
        {/* Bottom shadow layer */}
        <div className="absolute -bottom-2 -right-2 w-full h-full bg-gray-300 rounded-xl"></div>

        {/* Middle shadow layer */}
        <div className="absolute -bottom-1 -right-1 w-full h-full bg-gray-200 rounded-xl"></div>

        {/* Main card */}
        <div className="relative bg-neutral-50 text-gray-900 rounded-xl p-6 shadow-lg border border-gray-100">
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
          <div className="mt-6 pt-4 border-t border-gray-100">
            Published Date:{" "}
            {brief?.pubDate
              ? new Date(brief.pubDate).toLocaleDateString()
              : "N/A"}
          </div>
        </div>
      </div>
    </div>
  );
};
export default BriefCard;
