import { useEffect, useState } from "react";
import { getFeedGroups } from "../services/FeedService";
import { FeedGroup } from "../types";
import MenuCard from "./MenuCard";
import { Link } from "react-router-dom";

interface GroupListProps {
  onGroupSelect?: (group: FeedGroup) => void;
}

const GroupList: React.FC<GroupListProps> = ({ onGroupSelect }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [groups, setGroups] = useState<FeedGroup[]>([]);

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
          <Link to="/groups/new">
            <img src="/assets/plus.svg" alt="Add Group" className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Groups list */}
      <div className="space-y-4">
        {filteredGroups.map((group) => (
          <div
            key={group.id}
            onClick={() => onGroupSelect?.(group)}
            className="p-4 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors duration-200"
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
