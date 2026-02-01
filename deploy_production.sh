#!/bin/bash
# Production Deployment Script
# สำหรับ scale: ~1000 users/day, ~200 stores/day

set -e

echo "=========================================="
echo "Food Court Management System - Production Deployment"
echo "=========================================="
echo ""

# 1. Check Python version
echo "1. Checking Python version..."
python3 --version

# 2. Install dependencies
echo ""
echo "2. Installing dependencies..."
pip install -r requirements.txt

# 3. Setup environment
echo ""
echo "3. Setting up environment..."
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your configuration!"
fi

# 4. Check database connection
echo ""
echo "4. Checking database connection..."
python3 -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); result = conn.execute(text('SELECT 1')); print('✅ Database connection OK'); conn.close()"

# 5. Create systemd service (optional)
echo ""
read -p "5. Create systemd service? (Y/N): " create_service
if [ "$create_service" = "Y" ] || [ "$create_service" = "y" ]; then
    sudo tee /etc/systemd/system/foodcourt.service > /dev/null <<EOF
[Unit]
Description=Food Court Management System
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(which gunicorn) main:app -c gunicorn_config.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable foodcourt
    echo "✅ Systemd service created"
    echo "   Start: sudo systemctl start foodcourt"
    echo "   Status: sudo systemctl status foodcourt"
    echo "   Logs: sudo journalctl -u foodcourt -f"
fi

# 6. Setup Nginx (optional)
echo ""
read -p "6. Setup Nginx configuration? (Y/N): " setup_nginx
if [ "$setup_nginx" = "Y" ] || [ "$setup_nginx" = "y" ]; then
    echo "Copy nginx.conf.example to /etc/nginx/sites-available/foodcourt"
    echo "Then run:"
    echo "  sudo ln -s /etc/nginx/sites-available/foodcourt /etc/nginx/sites-enabled/"
    echo "  sudo nginx -t"
    echo "  sudo systemctl reload nginx"
fi

# 7. Setup SSL with Let's Encrypt (optional)
echo ""
read -p "7. Setup SSL with Let's Encrypt? (Y/N): " setup_ssl
if [ "$setup_ssl" = "Y" ] || [ "$setup_ssl" = "y" ]; then
    read -p "Enter your domain: " domain
    sudo certbot --nginx -d $domain -d www.$domain
    echo "✅ SSL certificate installed"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "To start the server:"
echo "  gunicorn main:app -c gunicorn_config.py"
echo ""
echo "Or use systemd:"
echo "  sudo systemctl start foodcourt"
echo ""

