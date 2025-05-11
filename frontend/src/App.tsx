import { BrowserRouter, Route, Routes } from "react-router-dom";
import Group from "./pages/Group";
import Brief from "./pages/Brief";
import Home from "./pages/Home";

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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/group/:id" element={<Group />} />
          <Route path="/groups/new" element={<Group />} />
          <Route path="/brief/:id" element={<Brief />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
