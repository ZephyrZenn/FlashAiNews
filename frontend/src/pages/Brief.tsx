import { useNavigate, useParams } from "react-router-dom";
import GroupList from "../components/GroupList";
import BriefCard from "../components/home/BriefCard";

export default function Brief() {
  const { id } = useParams();
  const navigate = useNavigate();
  return (
    <div className={`grid grid-cols-4 h-4/5 gap-6 w-full`}>
      <div className={`col-span-1 h-full`}>
        <GroupList onGroupSelect={(group) => navigate(`/brief/${group.id}`)} />
      </div>
      <div className={`col-span-3 h-full grid grid-cols-3`}>
        <div className="col-span-2">
          <BriefCard briefId={id ? parseInt(id) : undefined} />
        </div>
        <div className="col-span-1"></div>
      </div>
    </div>
  );
}
