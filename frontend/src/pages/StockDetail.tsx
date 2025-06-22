// frontend/src/pages/StockDetail.tsx
// 個別股票詳細資訊頁面

import React from 'react';
import { useParams } from 'react-router-dom';
import { Typography, Card, Row, Col, Statistic, Tag, Button, Space } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, StockOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const StockDetail: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();

  return (
    <div>
      <Title level={2}>
        <StockOutlined style={{ marginRight: 8 }} />
        {symbol} - 股票詳細資訊
      </Title>
      
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="基本資訊" loading={false}>
            <Paragraph>
              這裡將顯示 {symbol} 的詳細資訊，包括技術分析圖表、基本面資料、法人進出狀況等。
              (第二階段將實作完整功能)
            </Paragraph>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// frontend/src/pages/IndustryRotation.tsx
// 產業輪動分析頁面

import React from 'react';
import { Typography, Card, Row, Col, Progress, Tag } from 'antd';
import { SwapOutlined } from '@ant-design/icons';

const { Title } = Typography;

const IndustryRotation: React.FC = () => {
  const industries = [
    { name: '半導體', strength: 85, trend: 'up' },
    { name: '電動車', strength: 72, trend: 'up' },
    { name: '生技醫療', strength: 68, trend: 'stable' },
    { name: '金融', strength: 45, trend: 'down' },
    { name: '傳統產業', strength: 32, trend: 'down' }
  ];

  return (
    <div>
      <Title level={2}>
        <SwapOutlined style={{ marginRight: 8 }} />
        產業輪動分析
      </Title>
      
      <Row gutter={[16, 16]}>
        {industries.map(industry => (
          <Col xs={24} md={12} lg={8} key={industry.name}>
            <Card title={industry.name}>
              <Progress 
                percent={industry.strength} 
                status={industry.trend === 'up' ? 'active' : 'normal'}
              />
              <Tag color={
                industry.trend === 'up' ? 'green' : 
                industry.trend === 'down' ? 'red' : 'blue'
              }>
                {industry.trend === 'up' ? '↗️ 上升' : 
                 industry.trend === 'down' ? '↘️ 下降' : '➡️ 持平'}
              </Tag>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

// frontend/src/pages/SmartSelection.tsx
// AI智能選股頁面

import React, { useState } from 'react';
import { Typography, Card, Radio, Button, Table, Space } from 'antd';
import { RobotOutlined } from '@ant-design/icons';

const { Title } = Typography;

const SmartSelection: React.FC = () => {
  const [period, setPeriod] = useState('short');
  const [count, setCount] = useState(10);

  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
    },
    {
      title: '股票代號',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
    },
    {
      title: '股票名稱',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'AI評分',
      dataIndex: 'score',
      key: 'score',
      width: 100,
    },
    {
      title: '推薦原因',
      dataIndex: 'reason',
      key: 'reason',
    },
  ];

  return (
    <div>
      <Title level={2}>
        <RobotOutlined style={{ marginRight: 8 }} />
        AI智能選股
      </Title>
      
      <Card title="選股設定" style={{ marginBottom: 16 }}>
        <Space direction="vertical" size="large">
          <div>
            <Typography.Text strong>投資期間：</Typography.Text>
            <Radio.Group value={period} onChange={(e) => setPeriod(e.target.value)}>
              <Radio value="short">短期 (7-14天)</Radio>
              <Radio value="medium">中期 (1-3個月)</Radio>
              <Radio value="long">長期 (3個月以上)</Radio>
            </Radio.Group>
          </div>
          
          <div>
            <Typography.Text strong>推薦數量：</Typography.Text>
            <Radio.Group value={count} onChange={(e) => setCount(e.target.value)}>
              <Radio value={10}>前10名</Radio>
              <Radio value={20}>前20名</Radio>
              <Radio value={30}>前30名</Radio>
            </Radio.Group>
          </div>
          
          <Button type="primary" size="large">
            開始AI選股分析
          </Button>
        </Space>
      </Card>

      <Card title="推薦結果">
        <Table 
          columns={columns} 
          dataSource={[]} 
          loading={false}
          locale={{ emptyText: '請先設定條件並開始分析' }}
        />
      </Card>
    </div>
  );
};

// frontend/src/pages/TechnicalAnalysis.tsx
// 技術分析頁面

import React from 'react';
import { Typography, Card, Input, Button, Space } from 'antd';
import { BarChartOutlined, SearchOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { Search } = Input;

const TechnicalAnalysis: React.FC = () => {
  const handleSearch = (value: string) => {
    console.log('搜尋股票:', value);
  };

  return (
    <div>
      <Title level={2}>
        <BarChartOutlined style={{ marginRight: 8 }} />
        技術分析
      </Title>
      
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="輸入股票代號或名稱"
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            style={{ width: 300 }}
            onSearch={handleSearch}
          />
          <Button type="primary" size="large">
            分析
          </Button>
        </Space>
      </Card>

      <Card title="技術分析圖表" style={{ height: 600 }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100%',
          color: '#8c8c8c'
        }}>
          請搜尋股票以查看技術分析圖表
          <br />
          (完整圖表功能將在第二階段實作)
        </div>
      </Card>
    </div>
  );
};

// 匯出所有組件
export { StockDetail, IndustryRotation, SmartSelection, TechnicalAnalysis };