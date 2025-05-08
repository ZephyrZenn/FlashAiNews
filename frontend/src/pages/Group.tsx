import { useParams } from "react-router-dom";
import GroupDetailForm from "../components/group/GroupDetailForm";

export default function Group() {
  const { id } = useParams();

  return (
    <div className="w-4/5">
      <GroupDetailForm id={id ? parseInt(id) : null} />
    </div>
  );
}
