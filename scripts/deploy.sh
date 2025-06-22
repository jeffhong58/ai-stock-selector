#!/bin/bash
# scripts/deploy.sh
# AI選股系統自動部署腳本 - 支援開發和生產環境部署

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 腳本設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-development}
BACKUP_BEFORE_DEPLOY=${BACKUP_BEFORE_DEPLOY:-true}

echo -e "${GREEN}=== AI選股系統自動部署腳本 ===${NC}"
echo "專案目錄: $PROJECT_ROOT"
echo "部署環境: $ENVIRONMENT"
echo "開始時間: $(date)"
echo "=========================================="

# 檢查必要的工具
check_dependencies() {
    echo -e "${YELLOW}檢查系統依賴...${NC}"
    
    local missing_deps=()
    
    # 檢查Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # 檢查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    # 檢查Git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}❌ 缺少必要依賴: ${missing_deps[*]}${NC}"
        echo "請先安裝缺少的依賴項目"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 系統依賴檢查完成${NC}"
}

# 檢查環境變數檔案
check_env_files() {
    echo -e "${YELLOW}檢查環境變數檔案...${NC}"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        ENV_FILE="deployment/.env.prod"
        if [ ! -f "$PROJECT_ROOT/$ENV_FILE" ]; then
            echo -e "${RED}❌ 找不到生產環境變數檔案: $ENV_FILE${NC}"
            echo "請從 deployment/.env.prod.example 複製並設定正確的值"
            exit 1
        fi
    else
        ENV_FILE=".env"
        if [ ! -f "$PROJECT_ROOT/$ENV_FILE" ]; then
            echo -e "${YELLOW}⚠️ 找不到 .env 檔案，從範例檔案複製...${NC}"
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            echo -e "${YELLOW}請編輯 .env 檔案並設定正確的環境變數${NC}"
            echo "按 Enter 繼續，或 Ctrl+C 取消..."
            read
        fi
    fi
    
    echo -e "${GREEN}✅ 環境變數檔案檢查完成${NC}"
}

# 備份現有資料
backup_existing_data() {
    if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
        echo -e "${YELLOW}部署前備份資料...${NC}"
        
        # 檢查是否有運行中的容器
        if docker-compose ps | grep -q "Up"; then
            echo "正在備份資料庫..."
            bash "$PROJECT_ROOT/scripts/backup.sh"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ 資料備份完成${NC}"
            else
                echo -e "${RED}❌ 資料備份失敗${NC}"
                echo "是否要繼續部署? (y/N)"
                read -r continue_deploy
                if [[ ! $continue_deploy =~ ^[Yy]$ ]]; then
                    echo "部署已取消"
                    exit 1
                fi
            fi
        else
            echo "沒有找到運行中的容器，跳過備份"
        fi
    fi
}

# 拉取最新程式碼
update_code() {
    echo -e "${YELLOW}更新程式碼...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # 檢查是否為Git儲存庫
    if [ -d ".git" ]; then
        echo "從Git儲存庫拉取最新代碼..."
        
        # 保存本地變更
        git stash push -m "Auto-stash before deploy $(date)"
        
        # 拉取最新代碼
        git pull origin main
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 程式碼更新完成${NC}"
        else
            echo -e "${RED}❌ 程式碼更新失敗${NC}"
            exit 1
        fi
    else
        echo "非Git儲存庫，跳過程式碼更新"
    fi
}

# 建置Docker映像檔
build_images() {
    echo -e "${YELLOW}建置Docker映像檔...${NC}"
    
    cd "$PROJECT_ROOT"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "建置生產環境映像檔..."
        docker-compose -f deployment/docker-compose.prod.yml build --no-cache
    else
        echo "建置開發環境映像檔..."
        docker-compose build --no-cache
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Docker映像檔建置完成${NC}"
    else
        echo -e "${RED}❌ Docker映像檔建置失敗${NC}"
        exit 1
    fi
}

# 停止現有服務
stop_services() {
    echo -e "${YELLOW}停止現有服務...${NC}"
    
    cd "$PROJECT_ROOT"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f deployment/docker-compose.prod.yml down
    else
        docker-compose down
    fi
    
    echo -e "${GREEN}✅ 服務已停止${NC}"
}

# 啟動服務
start_services() {
    echo -e "${YELLOW}啟動服務...${NC}"
    
    cd "$PROJECT_ROOT"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "啟動生產環境服務..."
        docker-compose -f deployment/docker-compose.prod.yml up -d
    else
        echo "啟動開發環境服務..."
        docker-compose up -d
    fi
    
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
        
        # 檢查後端健康狀態
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

# 執行資料庫遷移
run_migrations() {
    echo -e "${YELLOW}執行資料庫遷移...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # 建立資料表
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f deployment/docker-compose.prod.yml exec backend python -c "
from app.database import db_manager
import asyncio
asyncio.run(db_manager.create_tables())
"
    else
        docker-compose exec backend python -c "
from app.database import db_manager
import asyncio
asyncio.run(db_manager.create_tables())
"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 資料庫遷移完成${NC}"
    else
        echo -e "${RED}❌ 資料庫遷移失敗${NC}"
        exit 1
    fi
}

# 初始化資料
initialize_data() {
    echo -e "${YELLOW}初始化系統資料...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # 觸發初始資料收集
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f deployment/docker-compose.prod.yml exec backend python -c "
from app.main import celery
celery.send_task('app.tasks.daily_data_update')
"
    else
        docker-compose exec backend python -c "
from app.main import celery
celery.send_task('app.tasks.daily_data_update')
"
    fi
    
    echo -e "${GREEN}✅ 資料初始化任務已啟動${NC}"
}

# 執行健康檢查
health_check() {
    echo -e "${YELLOW}執行系統健康檢查...${NC}"
    
    local services=("backend" "frontend" "postgres" "redis" "influxdb")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            echo "✅ $service: 正常運行"
        else
            echo "❌ $service: 異常"
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ 所有服務運行正常${NC}"
    else
        echo -e "${RED}❌ 以下服務異常: ${failed_services[*]}${NC}"
        return 1
    fi
    
    # 測試API端點
    echo ""
    echo "測試API端點..."
    
    local endpoints=(
        "http://localhost:8000/health"
        "http://localhost:8000/api/stocks/"
        "http://localhost:3000/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f "$endpoint" >/dev/null 2>&1; then
            echo "✅ $endpoint: 正常"
        else
            echo "❌ $endpoint: 異常"
        fi
    done
}

# 顯示部署資訊
show_deployment_info() {
    echo ""
    echo -e "${GREEN}=== 部署完成 ===${NC}"
    echo "環境: $ENVIRONMENT"
    echo "完成時間: $(date)"
    echo ""
    echo -e "${BLUE}服務存取資訊:${NC}"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "🌐 前端網站: https://yourdomain.com"
        echo "🔧 API文檔: https://yourdomain.com/docs"
        echo "📊 監控面板: https://yourdomain.com/flower"
    else
        echo "🌐 前端網站: http://localhost:3000"
        echo "🔧 API文檔: http://localhost:8000/docs"
        echo "📊 Celery監控: http://localhost:5555"
        echo "🗄️ 資料庫: localhost:5432"
        echo "🔧 Redis: localhost:6379"
        echo "📈 InfluxDB: http://localhost:8086"
    fi
    
    echo ""
    echo -e "${BLUE}常用指令:${NC}"
    echo "查看日誌: docker-compose logs -f"
    echo "重啟服務: docker-compose restart"
    echo "停止服務: docker-compose down"
    echo "服務狀態: docker-compose ps"
    echo ""
    echo -e "${GREEN}部署成功！🎉${NC}"
}

# 錯誤處理
error_handler() {
    echo -e "${RED}❌ 部署過程中發生錯誤！${NC}"
    echo "請檢查上面的錯誤訊息並修復問題"
    echo ""
    echo "如需查看詳細日誌："
    echo "docker-compose logs"
    exit 1
}

# 設定錯誤處理
trap error_handler ERR

# 主要部署流程
main() {
    echo -e "${BLUE}開始執行部署流程...${NC}"
    
    # 檢查參數
    if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
        echo -e "${RED}❌ 無效的環境參數: $ENVIRONMENT${NC}"
        echo "使用方式: $0 [development|production]"
        exit 1
    fi
    
    # 執行部署步驟
    check_dependencies
    check_env_files
    backup_existing_data
    update_code
    stop_services
    build_images
    start_services
    wait_for_services
    run_migrations
    initialize_data
    
    # 健康檢查
    if health_check; then
        show_deployment_info
    else
        echo -e "${YELLOW}⚠️ 部署完成但某些服務可能有問題${NC}"
        echo "請檢查服務狀態並查看日誌"
    fi
}

# 顯示使用說明
show_help() {
    echo "AI選股系統部署腳本"
    echo ""
    echo "使用方式:"
    echo "  $0 [environment]"
    echo ""
    echo "參數:"
    echo "  development    部署到開發環境 (預設)"
    echo "  production     部署到生產環境"
    echo ""
    echo "環境變數:"
    echo "  BACKUP_BEFORE_DEPLOY    部署前是否備份 (預設: true)"
    echo ""
    echo "範例:"
    echo "  $0                      # 部署到開發環境"
    echo "  $0 development          # 部署到開發環境"
    echo "  $0 production           # 部署到生產環境"
    echo "  BACKUP_BEFORE_DEPLOY=false $0    # 部署時不備份"
}

# 處理命令列參數
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main
        ;;
esac