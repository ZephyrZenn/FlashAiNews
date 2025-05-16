import {
  Cross1Icon,
  FileIcon,
  Pencil1Icon,
  PlusIcon,
} from "@radix-ui/react-icons";
import { useEffect, useRef, useState } from "react";
import { AlertDialog } from "../components/AlertDialog";
import { DropDownMenu } from "../components/DropDownMenu";
import ModifyFeedModal from "../components/feed/ModifyFeedModal";
import MainCard from "../components/MainCard";
import { useToast } from "../components/toast/useToast";
import { deleteFeed, getAllFeeds, importOpml } from "../services/FeedService";
import { Feed } from "../types";

interface ModalState {
  isOpen: boolean;
  selectedFeed: Feed | undefined;
}

export default function FeedPage() {
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [modalState, setModalState] = useState<ModalState>({
    isOpen: false,
    selectedFeed: undefined,
  });

  const fetchFeeds = async () => {
    const data = await getAllFeeds();
    setFeeds(data);
  };

  useEffect(() => {
    fetchFeeds();
  }, []);

  const handleImportOpmlClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (file) {
      const content = await file.text();
      await toast.promise(importOpml(undefined, content), {
        pending: "Importing...",
        success: "Imported successfully",
        error: "Failed to import",
      });
      fetchFeeds();
    } else {
      toast.error("No file selected");
    }
  };

  const handleDeleteFeed = async (id: number) => {
    try {
      await deleteFeed(id);
      toast.success("Feed deleted successfully");
      fetchFeeds();
    } catch (error) {
      toast.error("Failed to delete feed. " + error);
    }
  };

  return (
    <div className="w-2/3">
      <MainCard>
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">All Feeds</h2>

            <input
              type="file"
              accept=".opml"
              ref={fileInputRef}
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
            <DropDownMenu
              trigger={<PlusIcon />}
              items={[
                {
                  children: (
                    <div className="flex items-center gap-2">
                      <Pencil1Icon />
                      Add New Feed
                    </div>
                  ),
                  onClick: () => {
                    setModalState({
                      isOpen: true,
                      selectedFeed: undefined,
                    });
                  },
                },
                {
                  children: (
                    <div className="flex items-center gap-2">
                      <FileIcon />
                      Import From OPML
                    </div>
                  ),
                  onClick: handleImportOpmlClick,
                },
              ]}
            />
          </div>
          <div className="grid grid-cols-3 gap-4">
            {feeds?.map((feed) => (
              <div key={feed.id} className="p-4 border rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">
                      {feed.title}
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {feed.desc.length > 30
                        ? feed.desc?.slice(0, 30) + "..."
                        : feed.desc}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Pencil1Icon
                      className="text-blue-500 cursor-pointer"
                      onClick={() => {
                        setModalState({
                          isOpen: true,
                          selectedFeed: feed,
                        });
                      }}
                    />

                    <AlertDialog
                      trigger={
                        <Cross1Icon className="text-red-500 cursor-pointer" />
                      }
                      title="Delete Feed"
                      description="Are you sure you want to delete this feed? This action cannot be undone."
                      confirmText="Delete"
                      onConfirm={() => {
                        handleDeleteFeed(feed.id);
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </MainCard>
      <ModifyFeedModal
        isOpen={modalState.isOpen}
        onClose={() =>
          setModalState({ isOpen: false, selectedFeed: undefined })
        }
        onFeedModified={() => fetchFeeds()}
        feed={modalState.selectedFeed}
      />
    </div>
  );
}
