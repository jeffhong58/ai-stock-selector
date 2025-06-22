#!/bin/bash
# scripts/backup.sh
# 資料庫自動備份腳本 - 每天自動備份PostgreSQL資料庫

# 設定顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 載入環境變數
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# 設定備份參數
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="ai_stock_backup_${DATE}.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# 資料庫連線資訊
DB_HOST=${POSTGRES_HOST:-postgres}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-ai_stock_db}
DB_USER=${POSTGRES_USER:-stock_user}
DB_PASSWORD=${POSTGRES_PASSWORD}

echo -e "${GREEN}=== AI選股系統資料庫備份 ===${NC}"
echo "開始時間: $(date)"
echo "備份檔案: ${BACKUP_FILE}"
echo "保留天數: ${RETENTION_DAYS} 天"
echo "-----------------------------------"

# 檢查備份目錄
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}建立備份目錄: $BACKUP_DIR${NC}"
    mkdir -p "$BACKUP_DIR"
fi

# 執行資料庫備份
echo -e "${YELLOW}正在備份資料庫...${NC}"

# 使用pg_dump進行備份
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --encoding=UTF8 \
    > "$BACKUP_DIR/$BACKUP_FILE"

# 檢查備份是否成功
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 資料庫備份成功！${NC}"
    
    # 壓縮備份檔案
    echo -e "${YELLOW}正在壓縮備份檔案...${NC}"
    gzip "$BACKUP_DIR/$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 備份檔案壓縮完成: ${BACKUP_FILE}.gz${NC}"
        BACKUP_FILE="${BACKUP_FILE}.gz"
    else
        echo -e "${RED}⚠️ 備份檔案壓縮失敗${NC}"
    fi
    
    # 顯示備份檔案大小
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo "備份檔案大小: $BACKUP_SIZE"
    
else
    echo -e "${RED}❌ 資料庫備份失敗！${NC}"
    exit 1
fi

# 清理舊的備份檔案
echo -e "${YELLOW}正在清理 ${RETENTION_DAYS} 天前的備份檔案...${NC}"

# 找出並刪除超過保留天數的備份檔案
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "ai_stock_backup_*.sql.gz" -mtime +$RETENTION_DAYS)

if [ ! -z "$OLD_BACKUPS" ]; then
    echo "刪除以下舊備份檔案:"
    echo "$OLD_BACKUPS"
    find "$BACKUP_DIR" -name "ai_stock_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo -e "${GREEN}✅ 舊備份檔案清理完成${NC}"
else
    echo "沒有需要清理的舊備份檔案"
fi

# 顯示當前所有備份檔案
echo ""
echo "當前備份檔案列表:"
ls -lh "$BACKUP_DIR"/ai_stock_backup_*.sql.gz 2>/dev/null || echo "沒有找到備份檔案"

# 可選：上傳到雲端儲存 (如果設定了)
if [ ! -z "$AWS_S3_BUCKET" ] && [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
    echo -e "${YELLOW}正在上傳備份到 S3...${NC}"
    
    aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" "s3://$AWS_S3_BUCKET/database-backups/" \
        --region $AWS_REGION \
        --storage-class STANDARD_IA
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 備份已上傳到 S3${NC}"
    else
        echo -e "${RED}⚠️ S3 上傳失敗${NC}"
    fi
fi

# 備份InfluxDB (時序資料庫)
if [ "$INFLUXDB_ENABLED" = "true" ]; then
    echo -e "${YELLOW}正在備份 InfluxDB...${NC}"
    
    INFLUX_BACKUP_FILE="influxdb_backup_${DATE}.tar.gz"
    
    # 使用influx backup命令
    docker exec ai_stock_influxdb influx backup /tmp/backup_${DATE} \
        --host http://localhost:8086 \
        --token $INFLUXDB_TOKEN \
        --org $INFLUXDB_ORG
    
    # 從容器複製備份檔案
    docker cp ai_stock_influxdb:/tmp/backup_${DATE} "$BACKUP_DIR/"
    
    # 壓縮InfluxDB備份
    tar -czf "$BACKUP_DIR/$INFLUX_BACKUP_FILE" -C "$BACKUP_DIR" "backup_${DATE}"
    rm -rf "$BACKUP_DIR/backup_${DATE}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ InfluxDB備份完成: $INFLUX_BACKUP_FILE${NC}"
    else
        echo -e "${RED}⚠️ InfluxDB備份失敗${NC}"
    fi
fi

# 發送備份完成通知 (如果設定了Email)
if [ ! -z "$ALERT_EMAIL_RECIPIENTS" ]; then
    echo -e "${YELLOW}發送備份完成通知...${NC}"
    
    SUBJECT="AI選股系統 - 資料庫備份完成 ($(date +%Y-%m-%d))"
    BODY="資料庫備份已成功完成

備份時間: $(date)
備份檔案: $BACKUP_FILE
備份大小: $BACKUP_SIZE
備份位置: $BACKUP_DIR

系統狀態: 正常運行
下次備份: 明天同一時間

此為自動發送的通知郵件。"

    # 使用sendmail或其他郵件服務發送通知
    echo "$BODY" | mail -s "$SUBJECT" "$ALERT_EMAIL_RECIPIENTS" 2>/dev/null || \
    echo -e "${RED}⚠️ 郵件通知發送失敗${NC}"
fi

echo ""
echo -e "${GREEN}=== 備份作業完成 ===${NC}"
echo "結束時間: $(date)"
echo "備份檔案: $BACKUP_DIR/$BACKUP_FILE"

# 記錄備份日誌
echo "$(date): 備份完成 - $BACKUP_FILE" >> "$BACKUP_DIR/backup.log"