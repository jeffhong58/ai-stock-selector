// frontend/src/pages/StockList.tsx
// 股票清單頁面 - 顯示所有股票的基本資訊和價格

import React, { useState } from 'react';
import { 
  Table, 
  Input, 
  Button, 
  Typography, 
  Space,
  Tag,
  Card
} from 'antd';
import { 
  SearchOutlined, 
  StockOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;
const { Search } = Input;

// 股票資料的介面定義
interface StockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  industry: string;
}

const StockList: React.FC = () => {
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState('');

  // 假的股票資料 (將來會從API獲取)
  const mockStockData: StockData[] = [
    {
      symbol: '2330',
      name: '台積電',
      price: 580.00,
      change: 5.00,
      changePercent: 0.87,
      volume: 25000000,
      industry: '半導體'
    },
    {
      symbol: '2454',
      name: '聯發科',
      price: 920.00,
      change: -15.00,
      changePercent: -1.60,
      volume: 8500000,
      industry: '半導體'
    },
    {
      symbol: '2317',
      name: '鴻海',
      price: 105.50,
      change: 2.50,
      changePercent: 2.43,
      volume: 45000000,
      industry: '電子製造'
    },
    {
      symbol: '2881',
      name: '富邦金',
      price: 62.80,
      change: -0.30,
      changePercent: -0.48,
      volume: 12000000,
      industry: '金融'
    },
    {
      symbol: '1301',
      name: '台塑',
      price: 98.70,
      change: 1.20,
      changePercent: 1.23,
      volume: 3200000,
      industry: '石化'
    }
  ];

  // 表格欄位定義
  const columns = [
    {
      title: '股票代號',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      render: (symbol: string) => (
        <Button 
          type="link" 
          onClick={() => navigate(`/stocks/${symbol}`)}
        >
          {symbol}
        </Button>
      ),
    },
    {
      title: '股票名稱',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '股價',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price: number) => `$${price.toFixed(2)}`,
      align: 'right' as const,
    },
    {
      title: '漲跌',
      dataIndex: 'change',
      key: 'change',
      width: 100,
      render: (change: number, record: StockData) => (
        <Space>
          <span className={change >= 0 ? 'stock-up' : 'stock-down'}>
            {change >= 0 ? '+' : ''}{change.toFixed(2)}
          </span>
          <span className={change >= 0 ? 'stock-up' : 'stock-down'}>
            ({change >= 0 ? '+' : ''}{record.changePercent.toFixed(2)}%)
          </span>
        </Space>
      ),
      align: 'right' as const,
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      width: 120,
      render: (volume: number) => {
        if (volume >= 1000000) {
          return `${(volume / 1000000).toFixed(1)}M`;
        } else if (volume >= 1000) {
          return `${(volume / 1000).toFixed(1)}K`;
        }
        return volume.toString();
      },
      align: 'right' as const,
    },
    {
      title: '產業',
      dataIndex: 'industry',
      key: 'industry',
      width: 100,
      render: (industry: string) => (
        <Tag color="blue">{industry}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record: StockData) => (
        <Button
          type="primary"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/stocks/${record.symbol}`)}
        >
          查看
        </Button>
      ),
    },
  ];

  // 搜尋功能
  const handleSearch = (value: string) => {
    setSearchText(value);
    // 這裡將來會實作真正的搜尋功能
    console.log('搜尋:', value);
  };

  // 過濾股票資料
  const filteredData = mockStockData.filter(stock =>
    stock.symbol.includes(searchText.toUpperCase()) ||
    stock.name.includes(searchText)
  );

  return (
    <div>
      {/* 頁面標題 */}
      <Title level={2}>
        <StockOutlined style={{ marginRight: 8 }} />
        股票清單
      </Title>

      {/* 搜尋和操作區 */}
      <Card style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Search
            placeholder="輸入股票代號或名稱搜尋"
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            style={{ width: 300 }}
            onSearch={handleSearch}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <Button type="primary" size="large">
            匯出資料
          </Button>
          <Button size="large">
            重新整理
          </Button>
        </Space>
      </Card>

      {/* 股票表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey="symbol"
          pagination={{
            total: filteredData.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 筆，共 ${total} 筆股票`,
          }}
          scroll={{ x: 800 }}
          loading={false} // 將來連接API時會用到
        />
      </Card>
    </div>
  );
};

export default StockList;