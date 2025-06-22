// frontend/src/pages/TechnicalAnalysis.tsx
// 技術分析頁面

import React, { useState } from 'react';
import { 
  Typography, 
  Card, 
  Input, 
  Button, 
  Space, 
  Row, 
  Col,
  Statistic,
  Progress,
  Tag,
  Descriptions,
  Alert
} from 'antd';
import { 
  BarChartOutlined, 
  SearchOutlined,
  LineChartOutlined,
  RiseOutlined,
  FallOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Search } = Input;

interface TechnicalData {
  symbol: string;
  name: string;
  rsi: number;
  macd: string;
  kd: string;
  bb: string;
  ma: string;
  support: number;
  resistance: number;
  trend: 'bullish' | 'bearish' | 'neutral';
  signal: string;
}

const TechnicalAnalysis: React.FC = () => {
  const [searchValue, setSearchValue] = useState('');
  const [analysisData, setAnalysisData] = useState<TechnicalData | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = (value: string) => {
    if (!value.trim()) return;
    
    setLoading(true);
    setSearchValue(value);
    
    // 模擬API調用
    setTimeout(() => {
      const mockData: TechnicalData = {
        symbol: value.toUpperCase(),
        name: value === '2330' ? '台積電' : 
              value === '2454' ? '聯發科' :
              value === '2317' ? '鴻海' : '未知股票',
        rsi: 65.2,
        macd: '多頭排列',
        kd: '黃金交叉',
        bb: '中軌附近',
        ma: '站上20日線',
        support: 560,
        resistance: 600,
        trend: 'bullish',
        signal: '買進訊號'
      };
      
      setAnalysisData(mockData);
      setLoading(false);
    }, 1500);
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'bullish': return '#52c41a';
      case 'bearish': return '#ff4d4f';
      default: return '#1890ff';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'bullish': return <RiseOutlined />;
      case 'bearish': return <FallOutlined />;
      default: return <LineChartOutlined />;
    }
  };

  const getRSIStatus = (rsi: number) => {
    if (rsi >= 70) return { status: 'error', text: '超買' };
    if (rsi <= 30) return { status: 'success', text: '超賣' };
    return { status: 'normal', text: '適中' };
  };

  return (
    <div>
      <Title level={2}>
        <BarChartOutlined style={{ marginRight: 8 }} />
        技術分析
      </Title>
      
      {/* 搜尋區域 */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="large" style={{ width: '100%', justifyContent: 'center' }}>
          <Search
            placeholder="輸入股票代號或名稱 (例: 2330)"
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            style={{ width: 400 }}
            loading={loading}
            onSearch={handleSearch}
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
          <Button 
            type="primary" 
            size="large"
            onClick={() => handleSearch(searchValue)}
            loading={loading}
          >
            開始分析
          </Button>
        </Space>
      </Card>

      {/* 分析結果 */}
      {analysisData && (
        <>
          {/* 基本資訊 */}
          <Card 
            title={`${analysisData.symbol} - ${analysisData.name} 技術分析`}
            style={{ marginBottom: 16 }}
          >
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <Statistic
                  title="趨勢方向"
                  value={
                    analysisData.trend === 'bullish' ? '多頭' :
                    analysisData.trend === 'bearish' ? '空頭' : '盤整'
                  }
                  valueStyle={{ color: getTrendColor(analysisData.trend) }}
                  prefix={getTrendIcon(analysisData.trend)}
                />
              </Col>
              <Col xs={24} sm={8}>
                <Statistic
                  title="支撐位"
                  value={analysisData.support}
                  prefix="$"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col xs={24} sm={8}>
                <Statistic
                  title="壓力位"
                  value={analysisData.resistance}
                  prefix="$"
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>
            
            <Alert
              message={analysisData.signal}
              type={
                analysisData.trend === 'bullish' ? 'success' :
                analysisData.trend === 'bearish' ? 'error' : 'info'
              }
              showIcon
              style={{ marginTop: 16 }}
            />
          </Card>

          {/* 技術指標詳情 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="📊 技術指標">
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="RSI (相對強弱指標)">
                    <Space>
                      <Progress 
                        percent={analysisData.rsi} 
                        size="small" 
                        style={{ width: 100 }}
                        strokeColor={
                          analysisData.rsi >= 70 ? '#ff4d4f' :
                          analysisData.rsi <= 30 ? '#52c41a' : '#1890ff'
                        }
                      />
                      <span>{analysisData.rsi}</span>
                      <Tag color={
                        analysisData.rsi >= 70 ? 'red' :
                        analysisData.rsi <= 30 ? 'green' : 'blue'
                      }>
                        {getRSIStatus(analysisData.rsi).text}
                      </Tag>
                    </Space>
                  </Descriptions.Item>
                  
                  <Descriptions.Item label="MACD">
                    <Tag color="green">{analysisData.macd}</Tag>
                  </Descriptions.Item>
                  
                  <Descriptions.Item label="KD指標">
                    <Tag color="blue">{analysisData.kd}</Tag>
                  </Descriptions.Item>
                  
                  <Descriptions.Item label="布林帶">
                    <Tag color="purple">{analysisData.bb}</Tag>
                  </Descriptions.Item>
                  
                  <Descriptions.Item label="移動平均">
                    <Tag color="orange">{analysisData.ma}</Tag>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
            
            <Col xs={24} lg={12}>
              <Card title="💡 分析建議">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Alert
                    message="技術面建議"
                    description={
                      analysisData.trend === 'bullish' 
                        ? '多項指標顯示多頭訊號，可考慮逢低買進，但注意風險控制'
                        : analysisData.trend === 'bearish'
                        ? '技術指標偏空，建議觀望或減碼，等待更好進場時機'
                        : '指標呈現盤整格局，建議等待明確方向突破'
                    }
                    type={
                      analysisData.trend === 'bullish' ? 'success' :
                      analysisData.trend === 'bearish' ? 'warning' : 'info'
                    }
                    showIcon
                  />
                  
                  <div>
                    <Text strong>操作策略：</Text>
                    <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                      <li>進場點：接近支撐位 ${analysisData.support} 附近</li>
                      <li>停損點：跌破支撐位 ${analysisData.support - 10}</li>
                      <li>目標價：挑戰壓力位 ${analysisData.resistance}</li>
                      <li>注意事項：配合大盤走勢和成交量變化</li>
                    </ul>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>

          {/* 圖表區域 */}
          <Card title="📈 技術分析圖表" style={{ marginTop: 16 }}>
            <div style={{ 
              height: 400,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              backgroundColor: '#fafafa',
              border: '2px dashed #d9d9d9',
              borderRadius: 8
            }}>
              <BarChartOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
              <Text style={{ fontSize: 18, marginBottom: 8 }}>
                {analysisData.symbol} 技術分析圖表
              </Text>
              <Text type="secondary">
                完整的K線圖、技術指標圖表將在第二階段整合 TradingView
              </Text>
              <Button type="primary" style={{ marginTop: 16 }}>
                查看完整圖表 (即將推出)
              </Button>
            </div>
          </Card>
        </>
      )}

      {/* 空狀態 */}
      {!analysisData && !loading && (
        <Card style={{ height: 400 }}>
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column',
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%',
            color: '#8c8c8c'
          }}>
            <BarChartOutlined style={{ fontSize: 64, marginBottom: 24 }} />
            <Title level={4} style={{ color: '#8c8c8c' }}>
              請搜尋股票以查看技術分析
            </Title>
            <Text type="secondary">
              輸入股票代號 (如：2330) 或股票名稱開始分析
            </Text>
          </div>
        </Card>
      )}
    </div>
  );
};

export default TechnicalAnalysis;