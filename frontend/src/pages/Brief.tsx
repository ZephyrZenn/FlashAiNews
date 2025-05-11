import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import BriefCard from "../components/brief/BriefCard";
import BriefHistory from "../components/brief/BriefHistory";
import GroupList from "../components/GroupList";
import { GeneratingBrief } from "../constants";
import { BriefContext } from "../contexts/BriefContext";
import { FeedBrief } from "../types";

export default function Brief() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeBrief, setActiveBrief] = useState<FeedBrief>(GeneratingBrief);

  return (
    <BriefContext.Provider value={{ activeBrief, setActiveBrief }}>
      <div className={`grid grid-cols-4 h-4/5 gap-6 w-full`}>
        <div className={`col-span-1 h-full`}>
          <GroupList
            onGroupSelect={(group) => navigate(`/brief/${group.id}`)}
          />
        </div>
        <div className={`col-span-3 h-full grid grid-cols-3`}>
          <div className="col-span-2">
            <BriefCard briefId={id ? parseInt(id) : undefined} />
          </div>
          <div className="col-span-1">
            <BriefHistory />
          </div>
        </div>
      </div>
    </BriefContext.Provider>
  );
}
