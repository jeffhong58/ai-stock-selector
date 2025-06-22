// frontend/src/components/Layout/Footer.tsx
// 網站底部組件

import React from 'react';
import { Layout, Typography, Space, Divider } from 'antd';
import { GithubOutlined, MailOutlined } from '@ant-design/icons';

const { Footer: AntFooter } = Layout;
const { Text, Link } = Typography;

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <AntFooter 
      style={{ 
        textAlign: 'center',
        background: '#f0f2f5',
        borderTop: '1px solid #d9d9d9'
      }}
    >
      <Space direction="vertical" size="small">
        {/* 版權資訊 */}
        <Text type="secondary">
          AI選股系統 ©{currentYear} Created by jeffhong58
        </Text>
        
        <Divider type="vertical" />
        
        {/* 連結區域 */}
        <Space split={<Divider type="vertical" />}>
          <Link 
            href="https://github.com/jeffhong58/ai-stock-selector" 
            target="_blank"
          >
            <GithubOutlined /> GitHub
          </Link>
          <Link href="mailto:support@example.com">
            <MailOutlined /> 聯絡我們
          </Link>
          <Text type="secondary">
            資料來源：Yahoo Finance、證交所
          </Text>
        </Space>
        
        {/* 免責聲明 */}
        <Text 
          type="secondary" 
          style={{ fontSize: '12px', marginTop: '8px' }}
        >
          本系統僅供參考，投資有風險，請謹慎評估
        </Text>
      </Space>
    </AntFooter>
  );
};

export default Footer;