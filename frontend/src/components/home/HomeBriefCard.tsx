import { useEffect } from "react";

import Markdown from "react-markdown";
import MainCard from "../MainCard";
import { useState } from "react";
import { FeedBrief } from "../../types";
import { getHomeFeeds } from "../../services/FeedService";
import { GeneratingBrief } from "../../constants";

export default function HomeBriefCard() {
  const [brief, setBrief] = useState<FeedBrief>(GeneratingBrief);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const fetchTodayFeed = async () => {
      const data = await getHomeFeeds();
      if (data === null) {
        setLoading(false);
        const checkInterval = setInterval(async () => {
          try {
            const newData = await getHomeFeeds();
            if (newData !== null) {
              setBrief(newData);
              clearInterval(checkInterval);
            }
          } catch (err) {
            console.error("Error checking brief status:", err);
            clearInterval(checkInterval);
            setError(
              "Failed to check content status. Please refresh the page."
            );
          }
        }, 5000);

        // Cleanup interval on component unmount
        return () => clearInterval(checkInterval);
      }
      setBrief(data);
      setLoading(false);
    };
    fetchTodayFeed();
  }, []);
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
        <Markdown>{brief.content || ""}</Markdown>
      </div>

      {/* Card footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        Published Date:{" "}
        {brief.pubDate ? new Date(brief.pubDate).toLocaleDateString() : "N/A"}
        <br />
        Group: {brief.group?.title}
      </div>
    </MainCard>
  );
}
