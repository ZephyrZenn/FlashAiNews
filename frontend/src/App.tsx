import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { ToastProvider } from "./components/toast/ToastProvider";
import BriefPage from "./pages/BriefPage";
import FeedPage from "./pages/FeedPage";
import GroupPage from "./pages/GroupPage";
import HomePage from "./pages/HomePage";

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
              to="/group/new"
              className="text-gray-800 hover:text-gray-600"
            >
              Group
            </Link>
            <Link to="/feed" className="text-gray-800 hover:text-gray-600">
              Feed
            </Link>
            <Link to="/settings" className="text-gray-800 hover:text-gray-600">
              Settings
            </Link>
          </nav>
        </div>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/group/:id" element={<GroupPage />} />
          <Route path="/group/new" element={<GroupPage />} />
          <Route path="/brief" element={<BriefPage />} />
          <Route path="/brief/:id" element={<BriefPage />} />
          <Route path="/feed" element={<FeedPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
