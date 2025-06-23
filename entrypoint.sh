#!/bin/sh

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
    echo "Waiting for database to be ready..."
    sleep 20
    
    echo "Initializing database schema..."
    if ! mariadb -h db -u root -p"${MYSQL_ROOT_PASSWORD}" "${MYSQL_DATABASE}" < schema.sql --ssl=0 --default-auth=mysql_native_password; then
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

case "$RTE" in
  dev)
    echo "=== Development Mode ==="

    initDatabase

    flask run --host=0.0.0.0 --port=4000 --debug --reload
    ;;

  test)
    echo "=== Test Mode ==="

    initDatabase

    echo "Starting Flask app with gunicorn..."
    gunicorn -b 0.0.0.0:4000 app:app &

    # Wait for Nginx to be ready and successfully proxy the Flask app
    URL="http://nginx"
    MAX_RETRIES=15
    RETRY_DELAY=2
    RETRIES=0

    echo "Waiting for Nginx to respond with HTTP 200..."
    until curl -s -o /dev/null -w "%{http_code}" "$URL" | grep -q "200"; do
        echo "Still waiting... ($RETRIES/$MAX_RETRIES)"
        RETRIES=$((RETRIES + 1))
        if [ "$RETRIES" -ge "$MAX_RETRIES" ]; then
            echo "❌ ERROR: Nginx did not respond with status 200 in time."
            exit 1
        fi
        sleep "$RETRY_DELAY"
    done

    echo "✅ Nginx responded with HTTP 200"

    echo "Running test suite with coverage..."
    pytest --cov=. --cov-report=term --cov-report=xml

    TEST_EXIT_CODE=$?

    if [ "$TEST_EXIT_CODE" -eq 0 ]; then
        echo "✅ All tests passed!"
    else
        echo "❌ Some tests failed!"
    fi

    exit "$TEST_EXIT_CODE"
    ;;


  prod)
    echo "=== Production Mode ==="

    initDatabase

    gunicorn -b 0.0.0.0:4000 app:app
    ;;

  *)
    echo "❌ Unknown runtime environment: $RTE"
    exit 1
    ;;
esac

