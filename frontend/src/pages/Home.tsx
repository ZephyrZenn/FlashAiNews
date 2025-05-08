import BriefCard from "../components/home/SummaryCard";

export default function Home() {
  return (
    <div className="grid grid-cols-3">
      <div className="col-span-2">
        <BriefCard />
      </div>
      <div className="col-span-1"></div>
    </div>
  );
}
