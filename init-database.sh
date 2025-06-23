#!/bin/bash

generateImages() {
    echo "Checking if images need to be generated..."
    if [ ! -d "/app/images" ] || [ -z "$(ls -A /app/images)" ]; then
        echo "Generating images..."
        mkdir -p /app/images
        cd /app/unsplash
        python get_avatarts.py
        python get_restaurant_images.py
        python get_dishes_images.py
        python get_profile_images.py
        cd /app
        echo "✅ Images generated successfully"
    else
        echo "✅ Images already exist, skipping generation"
    fi
}

initDatabase(){
    
    echo "Initializing database schema..."
    if ! mariadb -h db -u root -p"${MYSQL_ROOT_PASSWORD}" "${MYSQL_DATABASE}" --ssl=0 --default-auth=mysql_native_password < schema.sql; then
        echo "❌ Failed to initialize database schema"
        exit 1
    fi
    
    echo "Seeding database..."
    if ! python seed.py; then
        echo "❌ Failed to seed database"
        exit 1
    fi

    generateImages
}

initDatabase