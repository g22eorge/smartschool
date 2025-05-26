#!/bin/bash

# Database configuration
DB_NAME="smartschool"
DB_USER="smartschool_user"
DB_PASSWORD="smart123"  # In production, use a stronger password

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "Error: psql command not found. Make sure PostgreSQL is installed and in your PATH."
    exit 1
fi

# Create database and user
echo "Creating database and user..."

# Connect to the default postgres database and create a new database and user
psql postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database $DB_NAME already exists or could not be created."
psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User $DB_USER already exists or could not be created."
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Create a .env file with the database configuration
echo "Creating .env file with database configuration..."
cat > .env <<EOL
# Database Configuration
DB_HOST=localhost
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_PORT=5432

# Django Secret Key
SECRET_KEY=your-secret-key-here
EOL

echo "Database setup complete!"
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo "Database Password: $DB_PASSWORD"
echo "\nConfiguration has been saved to .env file."
echo "Please update the SECRET_KEY in the .env file with a secure value."
