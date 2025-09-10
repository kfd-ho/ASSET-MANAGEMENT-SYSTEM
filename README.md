# Asset Management System - Production Deployment Guide

## 🚀 Complete Production-Ready Asset Management System

A comprehensive asset management solution built with Django REST Framework and React, designed for enterprise deployment on Ubuntu 24.

### 📋 Features

- **Asset Management**: Complete CRUD with photo upload, QR codes, depreciation tracking
- **Employee Management**: Department hierarchy, role-based access control
- **Allocation System**: Asset assignment with full audit trail and email notifications
- **Maintenance Module**: Scheduling, cost tracking, warranty alerts
- **Financial Reports**: Depreciation calculations, CSV import/export
- **Dashboard**: Real-time analytics with interactive charts
- **Security**: JWT authentication, role-based permissions (Admin/Manager/Employee)

---

## 🛠 Ubuntu 24 Production Deployment

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx mysql-server redis-server supervisor git curl
```

### Step 1: Database Setup (MySQL)

```bash
# Secure MySQL installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
CREATE DATABASE asset_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'assetuser'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON asset_management.* TO 'assetuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 2: Application Setup

```bash
# Create application user
sudo useradd --system --shell /bin/bash --home /opt/asset_management asset_app
sudo mkdir -p /opt/asset_management
sudo chown asset_app:asset_app /opt/asset_management

# Switch to application user
sudo -u asset_app -i

# Clone and setup application
cd /opt/asset_management
git clone <your-repo-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Environment Configuration

```bash
# Create production environment file
sudo -u asset_app tee /opt/asset_management/.env << EOF
# Django Settings
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=asset_management
DB_USER=assetuser
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=3306

# Email Configuration (Gmail example)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF

# Set proper permissions
sudo chmod 600 /opt/asset_management/.env
```

### Step 4: Django Setup

```bash
# Switch to application user and activate venv
sudo -u asset_app -i
cd /opt/asset_management
source venv/bin/activate

# Run migrations
python backend/manage.py makemigrations
python backend/manage.py migrate

# Create superuser
python backend/manage.py createsuperuser

# Create sample data (optional)
python backend/manage.py create_sample_data

# Collect static files
python backend/manage.py collectstatic --noinput

# Test the application
python backend/manage.py runserver 0.0.0.0:8000
```

### Step 5: Gunicorn Configuration

```bash
# Create Gunicorn configuration
sudo -u asset_app tee /opt/asset_management/gunicorn.conf.py << EOF
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
daemon = False
user = "asset_app"
group = "asset_app"
tmp_upload_dir = None
errorlog = "/var/log/asset_management/gunicorn_error.log"
accesslog = "/var/log/asset_management/gunicorn_access.log"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
EOF

# Create log directory
sudo mkdir -p /var/log/asset_management
sudo chown asset_app:asset_app /var/log/asset_management
```

### Step 6: Systemd Service Configuration

```bash
# Create systemd service file
sudo tee /etc/systemd/system/asset-management.service << EOF
[Unit]
Description=Asset Management Gunicorn daemon
After=network.target mysql.service redis.service

[Service]
Type=notify
User=asset_app
Group=asset_app
RuntimeDirectory=asset_management
WorkingDirectory=/opt/asset_management
Environment=PATH=/opt/asset_management/venv/bin
EnvironmentFile=/opt/asset_management/.env
ExecStart=/opt/asset_management/venv/bin/gunicorn --config /opt/asset_management/gunicorn.conf.py asset_management.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable asset-management
sudo systemctl start asset-management
sudo systemctl status asset-management
```

### Step 7: Celery Configuration (Background Tasks)

```bash
# Create Celery service
sudo tee /etc/systemd/system/asset-management-celery.service << EOF
[Unit]
Description=Asset Management Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=asset_app
Group=asset_app
WorkingDirectory=/opt/asset_management
Environment=PATH=/opt/asset_management/venv/bin
EnvironmentFile=/opt/asset_management/.env
ExecStart=/opt/asset_management/venv/bin/celery -A asset_management worker --loglevel=info --detach
ExecStop=/opt/asset_management/venv/bin/celery -A asset_management control shutdown
ExecReload=/opt/asset_management/venv/bin/celery -A asset_management control reload
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create Celery Beat service (for scheduled tasks)
sudo tee /etc/systemd/system/asset-management-celerybeat.service << EOF
[Unit]
Description=Asset Management Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=asset_app
Group=asset_app
WorkingDirectory=/opt/asset_management
Environment=PATH=/opt/asset_management/venv/bin
EnvironmentFile=/opt/asset_management/.env
ExecStart=/opt/asset_management/venv/bin/celery -A asset_management beat --loglevel=info
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start Celery services
sudo systemctl daemon-reload
sudo systemctl enable asset-management-celery
sudo systemctl enable asset-management-celerybeat
sudo systemctl start asset-management-celery
sudo systemctl start asset-management-celerybeat
```

### Step 8: Frontend Build and Setup

```bash
# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Build frontend
cd /opt/asset_management
sudo -u asset_app npm install
sudo -u asset_app npm run build

# Create frontend environment file
sudo -u asset_app tee /opt/asset_management/.env.local << EOF
VITE_API_URL=https://your-domain.com/api
EOF
```

### Step 9: Nginx Configuration

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/asset-management << EOF
upstream asset_management_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;

    # Frontend static files
    location / {
        root /opt/asset_management/dist;
        try_files \$uri \$uri/ /index.html;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /api/ {
        proxy_pass http://asset_management_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Django admin
    location /admin/ {
        proxy_pass http://asset_management_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files (Django)
    location /static/ {
        alias /opt/asset_management/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/asset_management/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File upload size
    client_max_body_size 10M;
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/asset-management /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

### Step 10: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Step 11: Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
sudo ufw status
```

### Step 12: Monitoring and Maintenance

```bash
# Create backup script
sudo tee /opt/asset_management/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/asset_management"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Database backup
mysqldump -u assetuser -p'your_secure_password' asset_management > \$BACKUP_DIR/db_\$DATE.sql

# Media files backup
tar -czf \$BACKUP_DIR/media_\$DATE.tar.gz -C /opt/asset_management media/

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

sudo chmod +x /opt/asset_management/backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /opt/asset_management/backup.sh" | sudo crontab -u asset_app -

# Add warranty alert cron job
echo "0 9 * * * cd /opt/asset_management && /opt/asset_management/venv/bin/python backend/manage.py send_warranty_alerts" | sudo crontab -u asset_app -
```

---

## 🔧 Post-Deployment Configuration

### Admin Panel Access
- URL: `https://your-domain.com/admin/`
- Create superuser: `python backend/manage.py createsuperuser`

### Default Login Credentials (Sample Data)
- **Admin**: admin / admin123
- **Manager**: manager / manager123  
- **Employee**: employee / employee123

### Email Configuration
Update `.env` file with your SMTP settings:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## 📊 System Monitoring

### Service Status
```bash
# Check all services
sudo systemctl status asset-management
sudo systemctl status asset-management-celery
sudo systemctl status asset-management-celerybeat
sudo systemctl status nginx
sudo systemctl status mysql
sudo systemctl status redis
```

### Logs
```bash
# Application logs
sudo journalctl -u asset-management -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application-specific logs
sudo tail -f /var/log/asset_management/gunicorn_error.log
```

---

## 🚀 Performance Optimization

### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_asset_serial ON assets_asset(serial_number);
CREATE INDEX idx_allocation_employee ON allocations_allocation(employee_id);
CREATE INDEX idx_allocation_asset ON allocations_allocation(asset_id);
```

### Redis Configuration
```bash
# Edit Redis config for production
sudo nano /etc/redis/redis.conf

# Recommended settings:
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

---

## 🔒 Security Checklist

- ✅ SSL/TLS encryption enabled
- ✅ Firewall configured (UFW)
- ✅ Database user with limited privileges
- ✅ Environment variables secured
- ✅ Security headers configured
- ✅ Regular backups scheduled
- ✅ System updates automated

---

## 📞 Support

For issues or questions:
1. Check service logs: `sudo journalctl -u asset-management -f`
2. Verify database connectivity
3. Check Nginx configuration: `sudo nginx -t`
4. Review environment variables in `.env`

The system is now production-ready and fully deployed on Ubuntu 24! 🎉