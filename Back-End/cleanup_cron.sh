#!/bin/bash
# Cron job script for cleaning up expired guest URLs
# Add to crontab: 0 3 * * * /path/to/cleanup_cron.sh

# Load environment variables
source .env

# Call cleanup endpoint
curl -X POST http://localhost:8000/admin/cleanup-expired-urls \
  -H "X-Admin-Key: $SECRET_KEY" \
  -H "Content-Type: application/json"

echo "Cleanup job completed at $(date)"
