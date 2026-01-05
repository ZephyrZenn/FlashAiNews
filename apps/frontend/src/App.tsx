import { Navigate, Route, Routes } from 'react-router-dom';

import { Layout } from '@/components/Layout';
import { ToastProvider } from '@/context/ToastContext';
import { ConfirmDialogProvider } from '@/context/ConfirmDialogContext';
import SummaryPage from '@/pages/SummaryPage';
import HistoryPage from '@/pages/HistoryPage';
import SourcesPage from '@/pages/SourcesPage';
import SettingsPage from '@/pages/SettingsPage';
import InstantLabPage from '@/pages/InstantLabPage';
import SchedulesPage from '@/pages/SchedulesPage';
import './styles/app.css';

const App = () => {
  return (
    <ToastProvider>
      <ConfirmDialogProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<SummaryPage />} />
            <Route path="/sources" element={<SourcesPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/instant" element={<InstantLabPage />} />
            <Route path="/schedules" element={<SchedulesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </ConfirmDialogProvider>
    </ToastProvider>
  );
};

export default App;
