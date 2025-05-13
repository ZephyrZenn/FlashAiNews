import { useNavigate, useParams } from "react-router-dom";
import GroupDetailForm from "../components/group/GroupDetailForm";
import GroupList from "../components/GroupList";
export default function Group() {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div className={`grid grid-cols-4 h-4/5 gap-6 w-full`}>
      <div className={`col-span-1 h-full`}>
        <GroupList
          onGroupSelect={(group) => {
            navigate(`/group/${group.id}`);
          }}
        />
      </div>
      <div className={`col-span-3 h-full w-4/5`}>
        <GroupDetailForm id={id ? parseInt(id) : null} />
      </div>
    </div>
  );
}
