#!/bin/bash
# scripts/start.sh
# AI選股系統一鍵啟動腳本

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AI選股系統啟動腳本 ===${NC}"
echo "開始時間: $(date)"
echo "=========================================="

# 檢查Docker是否安裝
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker未安裝，請先安裝Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose未安裝，請先安裝Docker Compose${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker環境檢查通過${NC}"
}

# 設定環境變數
setup_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️ 找不到.env檔案，從範例複製...${NC}"
        cp .env.example .env
        
        echo -e "${YELLOW}請編輯.env檔案並設定以下重要變數：${NC}"
        echo "- POSTGRES_PASSWORD (資料庫密碼)"
        echo "- SECRET_KEY (系統金鑰)"
        echo "- INFLUXDB_PASSWORD (InfluxDB密碼)"
        echo ""
        echo "按Enter繼續，或Ctrl+C取消編輯..."
        read
    fi
    
    echo -e "${GREEN}✅ 環境變數設定完成${NC}"
}

# 停止現有服務
stop_services() {
    echo -e "${YELLOW}停止現有服務...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ 服務已停止${NC}"
}

# 建置映像檔
build_images() {
    echo -e "${YELLOW}建置Docker映像檔...${NC}"
    docker-compose build --no-cache
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 映像檔建置完成${NC}"
    else
        echo -e "${RED}❌ 映像檔建置失敗${NC}"
        exit 1
    fi
}

# 啟動服務
start_services() {
    echo -e "${YELLOW}啟動服務...${NC}"
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 服務啟動完成${NC}"
    else
        echo -e "${RED}❌ 服務啟動失敗${NC}"
        exit 1
    fi
}

# 等待服務就緒
wait_for_services() {
    echo -e "${YELLOW}等待服務就緒...${NC}"
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "檢查服務狀態... (嘗試 $attempt/$max_attempts)"
        
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ 後端服務就緒${NC}"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo -e "${RED}❌ 服務啟動超時${NC}"
            echo "請檢查服務日誌："
            docker-compose logs backend
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
}

# 初始化資料
initialize_data() {
    echo -e "${YELLOW}初始化系統資料...${NC}"
    
    # 觸發資料更新任務
    curl -X POST http://localhost:8000/api/admin/update-data >/dev/null 2>&1
    
    echo -e "${GREEN}✅ 資料初始化任務已啟動${NC}"
}

# 顯示系統資訊
show_info() {
    echo ""
    echo -e "${GREEN}=== 🎉 AI選股系統啟動成功！ ===${NC}"
    echo "完成時間: $(date)"
    echo ""
    echo -e "${BLUE}📱 服務存取資訊：${NC}"
    echo "🌐 前端網站: http://localhost:3000"
    echo "🔧 API文檔: http://localhost:8000/docs"
    echo "📊 Celery監控: http://localhost:5555"
    echo "🏥 系統健康檢查: http://localhost:8000/health"
    echo ""
    echo -e "${BLUE}🛠 常用指令：${NC}"
    echo "查看服務狀態: docker-compose ps"
    echo "查看日誌: docker-compose logs -f"
    echo "重啟服務: docker-compose restart"
    echo "停止服務: docker-compose down"
    echo ""
    echo -e "${YELLOW}📝 注意事項：${NC}"
    echo "• 首次啟動需要等待2-3分鐘進行資料初始化"
    echo "• 股票資料會在每日17:30自動更新"
    echo "• 如遇問題請查看日誌檔案"
    echo ""
    echo -e "${GREEN}🚀 現在可以開始使用AI選股系統了！${NC}"
}

# 主要執行流程
main() {
    case "${1:-start}" in
        "start")
            check_docker
            setup_env
            stop_services
            build_images
            start_services
            wait_for_services
            initialize_data
            show_info
            ;;
        "stop")
            echo -e "${YELLOW}停止AI選股系統...${NC}"
            docker-compose down
            echo -e "${GREEN}✅ 系統已停止${NC}"
            ;;
        "restart")
            echo -e "${YELLOW}重啟AI選股系統...${NC}"
            docker-compose restart
            echo -e "${GREEN}✅ 系統已重啟${NC}"
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "status")
            docker-compose ps
            ;;
        *)
            echo "使用方式: $0 [start|stop|restart|logs|status]"
            echo ""
            echo "指令說明:"
            echo "  start   - 啟動系統 (預設)"
            echo "  stop    - 停止系統"
            echo "  restart - 重啟系統"
            echo "  logs    - 查看日誌"
            echo "  status  - 查看狀態"
            ;;
    esac
}

# 執行主程式
main "$@"