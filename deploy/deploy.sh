#!/bin/bash

# BodyWeight Deployment Script
# Run on server as: sudo bash deploy.sh

set -e

PROJECT_DIR="/var/www/bodyweight"
REPO_URL="git@github.com:YOUR_USERNAME/bodyweight.git"

echo "🎮 BodyWeight Deployment Starting..."

# Create project directory
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone or update repository
if [ -d ".git" ]; then
    echo "📥 Pulling latest changes..."
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone $REPO_URL .
fi

# Backend setup
echo "🔧 Setting up backend..."
cd $PROJECT_DIR/backend

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "⚠️ Please create .env file with required variables!"
    cp .env.example .env
fi

# Frontend setup
echo "🎨 Building frontend..."
cd $PROJECT_DIR/frontend/mini-app

# Install Node.js dependencies
npm install

# Build
npm run build

# Set permissions
chown -R www-data:www-data $PROJECT_DIR

# Install systemd services
echo "📋 Installing services..."
cp $PROJECT_DIR/deploy/bodyweight-api.service /etc/systemd/system/
cp $PROJECT_DIR/deploy/bodyweight-bot.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start services
systemctl enable bodyweight-api
systemctl enable bodyweight-bot
systemctl restart bodyweight-api
systemctl restart bodyweight-bot

# Reload nginx
echo "🔄 Reloading nginx..."
nginx -t && systemctl reload nginx

echo "✅ Deployment complete!"
echo ""
echo "📊 Service status:"
systemctl status bodyweight-api --no-pager
systemctl status bodyweight-bot --no-pager

echo ""
echo "🎮 BodyWeight is now available at:"
echo "   Mini App: https://stepaproject.ru/bodyweight"
echo "   API: https://stepaproject.ru/bodyweight/api"
