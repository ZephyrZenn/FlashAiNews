import { Navigate, Route, Routes } from 'react-router-dom';

import { Layout } from '@/components/Layout';
import { ToastProvider } from '@/context/ToastContext';
import { ConfirmDialogProvider } from '@/context/ConfirmDialogContext';
import SummaryPage from '@/pages/SummaryPage';
import GroupsPage from '@/pages/GroupsPage';
import FeedsPage from '@/pages/FeedsPage';
import SettingsPage from '@/pages/SettingsPage';
import './styles/app.css';

const App = () => {
  return (
    <ToastProvider>
      <ConfirmDialogProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<SummaryPage />} />
            <Route path="/groups" element={<GroupsPage />} />
            <Route path="/feeds" element={<FeedsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </ConfirmDialogProvider>
    </ToastProvider>
  );
};

export default App;
