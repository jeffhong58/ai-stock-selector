// frontend/src/components/Layout/Sidebar.tsx
// 左側導航選單組件

import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  StockOutlined,
  LineChartOutlined,
  RobotOutlined,
  BarChartOutlined,
  SwapOutlined
} from '@ant-design/icons';

const { Sider } = Layout;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // 選單項目設定
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '總覽儀表板',
    },
    {
      key: '/stocks',
      icon: <StockOutlined />,
      label: '股票清單',
    },
    {
      key: '/industry-rotation',
      icon: <SwapOutlined />,
      label: '產業輪動',
    },
    {
      key: '/smart-selection',
      icon: <RobotOutlined />,
      label: '智能選股',
    },
    {
      key: '/technical-analysis',
      icon: <BarChartOutlined />,
      label: '技術分析',
    },
  ];

  // 處理選單點擊事件
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Sider 
      width={200} 
      style={{ 
        background: '#fff',
        borderRight: '1px solid #f0f0f0'
      }}
      breakpoint="lg"
      collapsedWidth="0"
    >
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ 
          height: '100%', 
          borderRight: 0,
          paddingTop: '16px'
        }}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </Sider>
  );
};

export default Sidebar;