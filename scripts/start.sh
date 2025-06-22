#!/bin/bash
# start.sh
# AI選股系統一鍵啟動腳本

echo "🚀 AI選股系統啟動中..."
echo "=================================="

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 複製環境變數檔案（如果不存在）
if [ ! -f .env ]; then
    echo "📝 建立環境變數檔案..."
    cp .env.example .env
    echo "✅ 已建立 .env 檔案，使用預設設定"
fi

# 停止現有容器
echo "🛑 停止現有服務..."
docker-compose down

# 建置映像檔
echo "🔨 建置 Docker 映像檔..."
docker-compose build

# 啟動服務
echo "🚀 啟動服務..."
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 30

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose ps

echo ""
echo "🎉 AI選股系統啟動完成！"
echo "=================================="
echo "📱 前端網站: http://localhost:3000"
echo "🔧 API文檔: http://localhost:8000/docs"
echo "📊 Celery監控: http://localhost:5555"
echo "🏥 健康檢查: http://localhost:8000/health"
echo ""
echo "💡 常用指令："
echo "  查看日誌: docker-compose logs -f"
echo "  重啟服務: docker-compose restart"
echo "  停止服務: docker-compose down"
echo ""
echo "⚠️ 首次啟動需要等待2-3分鐘進行資料初始化"