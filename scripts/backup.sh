#!/bin/bash
BACKUP_DIR=/backup
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME=keypilot
DB_USER=keypilot
DB_PASS=${POSTGRES_PASSWORD}

mkdir -p $BACKUP_DIR
pg_dump -U $DB_USER -h postgres -Fc $DB_NAME > $BACKUP_DIR/$DB_NAME_$DATE.dump
# 可选：上传到 OSS
# ossutil cp $BACKUP_DIR/$DB_NAME_$DATE.dump oss://your-bucket/backups/

# 保留最近7天
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete