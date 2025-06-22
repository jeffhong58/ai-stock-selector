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

export default StockDetail;