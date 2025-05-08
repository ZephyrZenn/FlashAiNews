import { useParams } from "react-router-dom";
import GroupDetailForm from "../components/group/GroupDetailForm";

export default function Group() {
  const { id } = useParams();
  if (!id) {
    return <div>No id</div>;
  }
  const groupId = parseInt(id);

  return (
    <div className="w-4/5">
      <GroupDetailForm id={groupId} />
    </div>
  );
}
