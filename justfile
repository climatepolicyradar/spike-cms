download-rds-data:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔄 downloading latest dump from s3"
    LATEST_DUMP_KEY=$(aws s3api list-objects-v2 --bucket cpr-production-rds --prefix dumps/ --query 'sort_by(Contents, &LastModified)[-1].Key' --output=text)
    LATEST_DUMP_FILENAME=$(basename ${LATEST_DUMP_KEY})
    mkdir -p ./.data
    rm -rf ./.data/*
    aws s3 cp s3://cpr-production-rds/${LATEST_DUMP_KEY} ./.data/${LATEST_DUMP_FILENAME}