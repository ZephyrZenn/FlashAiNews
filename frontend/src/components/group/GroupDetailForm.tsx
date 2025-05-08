import { useEffect, useState } from "react";
import {
  createFeedGroup,
  getAllFeeds,
  getFeedGroupDetail,
  updateFeedGroup,
} from "../../services/FeedService";
import { Feed, FeedGroup } from "../../types";
import MainCard from "../MainCard";
import FeedSelectorModal from "./FeedSelectorModal";

interface GroupDetailProps {
  id: number;
}

export default function GroupDetailForm({ id }: GroupDetailProps) {
  const [group, setGroup] = useState<FeedGroup>({
    id: 0,
    title: "",
    desc: "",
    feeds: [],
  });
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [selectedFeeds, setSelectedFeeds] = useState<Feed[]>([]);
  const [showFeedSelector, setShowFeedSelector] = useState(false);

  useEffect(() => {
    const fetchGroup = async () => {
      const group = await getFeedGroupDetail(id);
      setGroup(group);
    };
    const fetchFeeds = async () => {
      const feeds = await getAllFeeds();
      setFeeds(feeds);
    };
    console.log(id);
    if (id) {
      fetchGroup();
      fetchFeeds();
    } else {
      setGroup({
        id: 0,
        title: "",
        desc: "",
        feeds: [],
      });
    }
  }, [id]);

  const handleAddFeed = () => {
    setShowFeedSelector(true);
  };

  const handleCloseModal = () => {
    setShowFeedSelector(false);
    setSelectedFeeds([]);
  };

  const handleAddSelected = () => {
    if (group) {
      setGroup({
        ...group,
        feeds: [...group.feeds, ...selectedFeeds],
      });
    }
    handleCloseModal();
  };

  const handleSaveGroup = async () => {
    if (!id) {
      const newGroup = await createFeedGroup(group);
      setGroup(newGroup);
    } else {
      await updateFeedGroup(group);
    }
  };

  return (
    <MainCard>
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Title
          </label>
          <input
            type="text"
            value={group.title}
            onChange={(e) => {
              setGroup({ ...group, title: e.target.value });
            }}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Description
          </label>
          <textarea
            value={group.desc}
            rows={3}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            onChange={(e) => {
              setGroup({ ...group, desc: e.target.value });
            }}
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-4">
            <label className="block text-sm font-medium text-gray-700">
              Feeds
            </label>
            <button
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={handleAddFeed}
            >
              Add Feed
            </button>
          </div>

          <div className="space-y-2 overflow-y-auto max-h-[350px]">
            {group.feeds?.map((feed) => (
              <div
                key={feed.id}
                className="flex justify-between items-center p-3 border rounded-lg"
              >
                <span>{feed.title}</span>
                <button
                  onClick={() => {
                    /* Remove feed handler */
                    setGroup({
                      ...group,
                      feeds: group.feeds.filter((f) => f.id !== feed.id),
                    });
                  }}
                  className="text-red-600 hover:text-red-800"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div className="mt-6">
            <button
              className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={handleSaveGroup}
            >
              Save Group
            </button>
          </div>
        </div>
      </div>

      <FeedSelectorModal
        isOpen={showFeedSelector}
        onClose={handleCloseModal}
        feeds={feeds}
        selectedFeeds={selectedFeeds}
        onSelectedFeedsChange={setSelectedFeeds}
        onAddSelected={handleAddSelected}
        existingFeeds={group?.feeds || []}
      />
    </MainCard>
  );
}
