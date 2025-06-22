// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider, Layout } from 'antd';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

// Components
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Footer from './components/Layout/Footer';

// Pages
import Dashboard from './pages/Dashboard';
import StockList from './pages/StockList';
import StockDetail from './pages/StockDetail';
import IndustryRotation from './pages/IndustryRotation';
import SmartSelection from './pages/SmartSelection';
import TechnicalAnalysis from './pages/TechnicalAnalysis';

// Styles
import './App.css';

const { Content } = Layout;

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Ant Design theme configuration
const theme = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    borderRadius: 6,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={theme}>
        <Router>
          <Layout style={{ minHeight: '100vh' }}>
            <Header />
            <Layout>
              <Sidebar />
              <Layout style={{ padding: '0 24px 24px' }}>
                <Content
                  style={{
                    padding: 24,
                    margin: 0,
                    minHeight: 280,
                    background: '#fff',
                    borderRadius: 6,
                  }}
                >
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/stocks" element={<StockList />} />
                    <Route path="/stocks/:symbol" element={<StockDetail />} />
                    <Route path="/industry-rotation" element={<IndustryRotation />} />
                    <Route path="/smart-selection" element={<SmartSelection />} />
                    <Route path="/technical-analysis" element={<TechnicalAnalysis />} />
                  </Routes>
                </Content>
              </Layout>
            </Layout>
            <Footer />
          </Layout>
        </Router>
      </ConfigProvider>
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools />}
    </QueryClientProvider>
  );
};

export default App;