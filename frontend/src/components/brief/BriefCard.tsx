import { useContext } from "react";
import Markdown from "react-markdown";
import { BriefContext } from "../../contexts/BriefContext";
import MainCard from "../MainCard";
interface BriefCardProps {
  briefId?: number;
}

const BriefCard: React.FC<BriefCardProps> = () => {
  const { activeBrief: brief } = useContext(BriefContext);
  // const [loading, setLoading] = useState<boolean>(true);
  // const [error, setError] = useState<string | null>(null);
  // if (loading) {
  //   // Loading state
  //   return (
  //     <div className="mx-auto w-full h-full flex items-center justify-center p-6">
  //       <div className="text-gray-500">Loading content...</div>
  //     </div>
  //   );
  // }

  // if (error) {
  //   return (
  //     <div className="mx-auto w-full h-full flex items-center justify-center p-6">
  //       <div className="text-red-500">{error}</div>
  //     </div>
  //   );
  // }

  return (
    <MainCard>
      {/* Card title */}
      {brief?.title && (
        <div className="mb-4">
          <h3 className="text-xl font-bold">{brief.title}</h3>
          <div className="mt-2 h-px bg-gradient-to-r from-gray-200 via-gray-400 to-gray-200"></div>
        </div>
      )}

      {/* Card content */}
      <div className="mb-4">
        <Markdown>{brief.content || ""}</Markdown>
      </div>

      {/* Card footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        Published Date:{" "}
        {brief.pubDate ? new Date(brief.pubDate).toLocaleDateString() : "N/A"}
        {brief?.group?.title && (
          <>
            <br />
            Group: {brief.group.title}
          </>
        )}
      </div>
    </MainCard>
  );
};
export default BriefCard;
