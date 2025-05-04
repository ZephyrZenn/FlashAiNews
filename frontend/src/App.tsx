import BriefCard from "./components/SummaryCard";

function App() {
  return (
    <div
      className="
      min-h-screen
      flex
      items-center
      justify-center
      p-4 sm:p-8
    "
    >
      <div className="grid grid-cols-4">
        <div className="col-span-1"></div>
        <div className="col-span-2">
          <BriefCard />
        </div>
        <div className="col-span-1"></div>
      </div>
    </div>
  );
}

export default App;
