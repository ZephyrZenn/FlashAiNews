import { useEffect, useState } from "react";
import { createFeed, updateFeed } from "../../services/FeedService";
import { Feed } from "../../types";
import { useToast } from "../toast/useToast";

interface ModifyFeedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFeedModified: () => void;
  feed?: Feed;
}

export default function ModifyFeedModal({
  isOpen,
  onClose,
  onFeedModified,
  feed,
}: ModifyFeedModalProps) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [desc, setDesc] = useState("");
  const toast = useToast();

  useEffect(() => {
    if (isOpen) {
      if (feed) {
        setTitle(feed.title || "");
        setUrl(feed.url || "");
        setDesc(feed.desc || "");
      } else {
        // Reset form fields when opening for a new feed
        setTitle("");
        setUrl("");
        setDesc("");
      }
    }
  }, [feed, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !url) {
      toast.error("Title and URL are required");
      return;
    }

    const newFeedData = { title, url, desc };

    try {
      if (feed) {
        await updateFeed(feed.id, newFeedData);
      } else {
        await createFeed(newFeedData);
      }
      toast.success("Feed added successfully!");
      onFeedModified();
      onClose();
    } catch (error) {
      console.log(error);
      toast.error(`Failed to add feed. ${error}. Please try again.`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">
          {feed ? "Edit" : "Add New"} Feed
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="title"
              className="block text-sm font-medium text-gray-700"
            >
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
              required
            />
          </div>
          <div>
            <label
              htmlFor="url"
              className="block text-sm font-medium text-gray-700"
            >
              URL <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border ${feed ? "bg-gray-100 cursor-not-allowed" : ""}`}
              readOnly={!!feed}
              required
            />
          </div>
          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-gray-700"
            >
              Description
            </label>
            <textarea
              id="description"
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={3}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {feed ? "Update" : "Add"} Feed
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
