import { useEffect } from "react";

import { useState } from "react";
import Markdown from "react-markdown";
import { GeneratingBrief } from "../../constants";
import { getHomeFeeds } from "../../services/FeedService";
import { FeedBrief } from "../../types";
import MainCard from "../MainCard";

export default function HomeBriefCard() {
  const [brief, setBrief] = useState<FeedBrief>(GeneratingBrief);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let checkInterval: NodeJS.Timeout | null = null;

    const fetchTodayFeed = async () => {
      try {
        const data = await getHomeFeeds();
        if (data === null) {
          setLoading(false);
          // Store interval ID so we can clear it later
          checkInterval = setInterval(async () => {
            try {
              const newData = await getHomeFeeds();
              if (newData !== null) {
                setBrief(newData);
                if (checkInterval) {
                  clearInterval(checkInterval);
                  checkInterval = null;
                }
              }
            } catch (err) {
              console.error("Error checking brief status:", err);
              if (checkInterval) {
                clearInterval(checkInterval);
                checkInterval = null;
              }
              setError(
                "Failed to check content status. Please refresh the page."
              );
            }
          }, 5000);
        } else {
          setBrief(data);
          setLoading(false);
        }
      } catch (err) {
        console.error("Error fetching brief:", err);
        setError("Failed to fetch content. Please refresh the page.");
        setLoading(false);
      }
    };

    fetchTodayFeed();

    // Cleanup function that runs when component unmounts or effect re-runs
    return () => {
      if (checkInterval) {
        clearInterval(checkInterval);
        checkInterval = null;
      }
    };
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
