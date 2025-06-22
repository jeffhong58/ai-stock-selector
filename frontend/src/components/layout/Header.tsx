// frontend/src/components/Layout/Header.tsx
// 網站頂部的導航列組件

import React from 'react';
import { Layout, Typography, Space, Button } from 'antd';
import { 
  DashboardOutlined, 
  StockOutlined, 
  BarChartOutlined 
} from '@ant-design/icons';

const { Header: AntHeader } = Layout;
const { Title } = Typography;

const Header: React.FC = () => {
  return (
    <AntHeader 
      style={{ 
        display: 'flex', 
        alignItems: 'center',
        background: '#001529',
        padding: '0 24px'
      }}
    >
      {/* 網站Logo和標題 */}
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <StockOutlined 
          style={{ 
            fontSize: '24px', 
            color: '#1890ff', 
            marginRight: '12px' 
          }} 
        />
        <Title 
          level={3} 
          style={{ 
            color: 'white', 
            margin: 0,
            fontWeight: 'bold'
          }}
        >
          AI選股系統
        </Title>
      </div>

      {/* 右側功能按鈕 */}
      <div style={{ marginLeft: 'auto' }}>
        <Space>
          <Button 
            type="ghost" 
            icon={<DashboardOutlined />}
            size="small"
          >
            系統狀態
          </Button>
          <Button 
            type="ghost" 
            icon={<BarChartOutlined />}
            size="small"
          >
            資料更新
          </Button>
        </Space>
      </div>
    </AntHeader>
  );
};

export default Header;