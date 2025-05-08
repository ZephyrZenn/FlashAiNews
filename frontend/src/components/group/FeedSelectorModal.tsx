import { Feed } from "../../types";

interface FeedSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  feeds: Feed[];
  selectedFeeds: Feed[];
  onSelectedFeedsChange: (feeds: Feed[]) => void;
  onAddSelected: () => void;
  existingFeeds: Feed[];
}

export default function FeedSelectorModal({
  isOpen,
  onClose,
  feeds,
  selectedFeeds,
  onSelectedFeedsChange,
  onAddSelected,
  existingFeeds,
}: FeedSelectorModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg w-[500px]">
        <h3 className="text-lg font-medium mb-4">Select Feeds</h3>

        <div className="max-h-[400px] overflow-y-auto">
          {feeds
            .filter(
              (feed) =>
                !existingFeeds.some((existing) => existing.id === feed.id)
            )
            .map((feed) => (
              <div key={feed.id} className="flex items-center p-2">
                <input
                  type="checkbox"
                  id={`feed-${feed.id}`}
                  checked={selectedFeeds.some(
                    (selected) => selected.id === feed.id
                  )}
                  onChange={(e) => {
                    if (e.target.checked) {
                      onSelectedFeedsChange([...selectedFeeds, feed]);
                    } else {
                      onSelectedFeedsChange(
                        selectedFeeds.filter(
                          (selected) => selected.id !== feed.id
                        )
                      );
                    }
                  }}
                  className="mr-2"
                />
                <label htmlFor={`feed-${feed.id}`}>{feed.title}</label>
              </div>
            ))}
        </div>

        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onAddSelected}
            className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Add Selected
          </button>
        </div>
      </div>
    </div>
  );
}
