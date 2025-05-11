import { useContext } from "react";
import Markdown from "react-markdown";
import MainCard from "../MainCard";
import { BriefContext } from "../../contexts/BriefContext";
interface BriefCardProps {
  briefId?: number;
}

const BriefCard: React.FC<BriefCardProps> = () => {
  const { activeBrief } = useContext(BriefContext);
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
      {activeBrief?.title && (
        <div className="mb-4">
          <h3 className="text-xl font-bold">{activeBrief.title}</h3>
          <div className="mt-2 h-px bg-gradient-to-r from-gray-200 via-gray-400 to-gray-200"></div>
        </div>
      )}

      {/* Card content */}
      <div className="mb-4">
        <Markdown>{activeBrief?.content || ""}</Markdown>
      </div>

      {/* Card footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        Published Date:{" "}
        {activeBrief?.pubDate
          ? new Date(activeBrief.pubDate).toLocaleDateString()
          : "N/A"}
        {activeBrief?.group?.title && (
          <>
            <br />
            Group: {activeBrief.group.title}
          </>
        )}
      </div>
    </MainCard>
  );
};
export default BriefCard;
