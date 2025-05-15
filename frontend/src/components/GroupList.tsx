import { FileIcon, Pencil1Icon, PlusIcon } from "@radix-ui/react-icons";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getFeedGroups, importOpml } from "../services/FeedService";
import { FeedGroup } from "../types";
import { DropDownMenu } from "./DropDownMenu";
import MenuCard from "./MenuCard";
import { useToast } from "./toast/useToast";
interface GroupListProps {
  onGroupSelect?: (group: FeedGroup) => void;
}

const GroupList: React.FC<GroupListProps> = ({ onGroupSelect }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [groups, setGroups] = useState<FeedGroup[]>([]);
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  const filteredGroups = groups.filter((group) =>
    group.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    const fetchGroups = async () => {
      const groups = await getFeedGroups();
      setGroups(groups);
    };
    fetchGroups();
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
      toast.promise(importOpml(undefined, content), {
        pending: "Importing...",
        success: "Imported successfully",
        error: "Failed to import",
      });
    } else {
      toast.error("No file selected");
    }
  };

  return (
    <MenuCard>
      {/* Search bar */}
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search groups..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
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
                    Create New Group
                  </div>
                ),
                onClick: () => {
                  navigate("/group/new");
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
          {/* <Link to="/groups/new">
            <img src="/assets/plus.svg" alt="Add Group" className="w-4 h-4" />
          </Link> */}
        </div>
      </div>

      {/* Groups list */}
      <div className="space-y-4">
        {filteredGroups.map((group) => (
          <div
            key={group.id}
            onClick={() => onGroupSelect?.(group)}
            className="p-4 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors duration-200"
          >
            <h3 className="text-lg font-semibold">{group.title}</h3>
            <p className="text-sm text-gray-600 mt-1">{group.desc}</p>
          </div>
        ))}
      </div>
    </MenuCard>
  );
};

export default GroupList;
