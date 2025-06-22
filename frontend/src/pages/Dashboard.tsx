// frontend/src/pages/Dashboard.tsx
// 總覽儀表板頁面 - 顯示系統整體狀況和重要資訊

import React from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Typography, 
  Space,
  Alert,
  Button,
  Divider
} from 'antd';
import {
  StockOutlined,
  RiseOutlined,
  FallOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  RobotOutlined
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const Dashboard: React.FC = () => {
  // 這裡的數據將來會從API獲取，現在先用假資料
  const systemStats = {
    totalStocks: 1800,
    updatedToday: 1750,
    risingStocks: 890,
    fallingStocks: 860,
    lastUpdate: '2025-06-22 17:30:00',
    systemStatus: 'healthy'
  };

  return (
    <div>
      {/* 頁面標題 */}
      <Title level={2}>
        <StockOutlined style={{ marginRight: 8 }} />
        系統總覽儀表板
      </Title>
      
      {/* 系統狀態提醒 */}
      <Alert
        message="系統運行正常"
        description={`最後更新時間：${systemStats.lastUpdate} | 資料同步完成`}
        type="success"
        showIcon
        style={{ marginBottom: 24 }}
        action={
          <Button size="small" type="primary">
            手動更新
          </Button>
        }
      />

      {/* 統計資料卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="總股票數"
              value={systemStats.totalStocks}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日已更新"
              value={systemStats.updatedToday}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${systemStats.totalStocks}`}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日上漲"
              value={systemStats.risingStocks}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日下跌"
              value={systemStats.fallingStocks}
              prefix={<FallOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 功能區塊 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card 
            title="🔄 產業輪動分析" 
            style={{ height: '300px' }}
            extra={<Button type="link">查看詳情</Button>}
          >
            <Paragraph>
              根據市場資金流向和價格動能，推薦下一波主流產業股票。
            </Paragraph>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>📈 本週熱門：半導體、電動車</div>
              <div>📊 資金流入：生技醫療、綠能</div>
              <div>⚡ 輪動信號：傳統產業 → 科技股</div>
            </Space>
            <Divider />
            <Button type="primary" block>
              查看產業輪動建議
            </Button>
          </Card>
        </Col>
        
        <Col xs={24} md={12}>
          <Card 
            title="🤖 AI智能選股" 
            style={{ height: '300px' }}
            extra={<Button type="link">開始選股</Button>}
          >
            <Paragraph>
              AI評分系統，支援短中長期投資建議，自定義推薦數量。
            </Paragraph>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>🎯 短期推薦：適合7-14天波段操作</div>
              <div>📊 中期推薦：適合1-3個月趨勢跟隨</div>
              <div>💎 長期推薦：適合3個月以上價值投資</div>
            </Space>
            <Divider />
            <Button type="primary" block>
              <RobotOutlined /> 開始智能選股
            </Button>
          </Card>
        </Col>
      </Row>

      {/* 快速功能按鈕 */}
      <Card title="🚀 快速功能" style={{ marginTop: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Button block size="large" type="default">
              查看股票清單
            </Button>
          </Col>
          <Col xs={24} sm={8}>
            <Button block size="large" type="default">
              技術分析圖表
            </Button>
          </Col>
          <Col xs={24} sm={8}>
            <Button block size="large" type="default">
              系統設定
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default Dashboard;