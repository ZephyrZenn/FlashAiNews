import { BrowserRouter, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Group from "./pages/Group";
import GroupList from "./components/GroupList";

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
      <div className={`grid grid-cols-4 h-4/5 gap-6 w-full`}>
        <div className={`col-span-1 h-full`}>
          <GroupList />
        </div>
        <div className={`col-span-3 h-full`}>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/group/:id" element={<Group />} />
            </Routes>
          </BrowserRouter>
        </div>
      </div>
    </div>
  );
}

export default App;
