import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import Group from "./pages/Group";
import Brief from "./pages/Brief";
import Home from "./pages/Home";
import { ToastProvider } from "./components/toast/ToastProvider";

function App() {
  return (
    <div
      className="
      min-h-screen
      flex
      items-center
      justify-center
      p-4 sm:p-8
      mx-10
    "
    >
      <ToastProvider />
      <BrowserRouter>
        <div className="fixed top-0 left-0 right-0 bg-white bg-opacity-20 p-4 flex justify-end">
          <nav className="space-x-6 mr-28">
            <Link to="/" className="text-gray-800 hover:text-gray-600">
              Home
            </Link>
            <Link to="/brief" className="text-gray-800 hover:text-gray-600">
              Brief
            </Link>
            <Link
              to="/groups/new"
              className="text-gray-800 hover:text-gray-600"
            >
              Groups
            </Link>
            <Link to="/settings" className="text-gray-800 hover:text-gray-600">
              Settings
            </Link>
          </nav>
        </div>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/group/:id" element={<Group />} />
          <Route path="/groups/new" element={<Group />} />
          <Route path="/brief" element={<Brief />} />
          <Route path="/brief/:id" element={<Brief />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
