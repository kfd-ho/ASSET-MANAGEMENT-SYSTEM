# 🚀 Production Deployment Guide - Asset Management System

## Quick Start Commands

### 1. System Preparation
```bash
# Update system and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx mysql-server redis-server supervisor git curl nodejs npm

# Create application user
sudo useradd --system --shell /bin/bash --home /opt/asset_management asset_app
sudo mkdir -p /opt/asset_management
sudo chown asset_app:asset_app /opt/asset_management
```

### 2. Database Setup
```bash
# Secure MySQL and create database
sudo mysql_secure_installation
sudo mysql -u root -p
```

```sql
CREATE DATABASE asset_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'assetuser'@'localhost' IDENTIFIED BY 'SecurePassword123!';
GRANT ALL PRIVILEGES ON asset_management.* TO 'assetuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Application Deployment
```bash
# Switch to app user and setup
sudo -u asset_app -i
cd /opt/asset_management

# Clone repository (replace with your repo URL)
git clone https://github.com/your-username/asset-management-system.git .

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost

DB_ENGINE=django.db.backends.mysql
DB_NAME=asset_management
DB_USER=assetuser
DB_PASSWORD=SecurePassword123!
DB_HOST=localhost
DB_PORT=3306

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF

chmod 600 .env

# Run Django setup
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py create_sample_data  # Optional: creates demo data
python manage.py collectstatic --noinput

# Build frontend
cd ..
npm install
npm run build
```

### 4. Service Configuration
```bash
# Copy service files
sudo cp deployment/systemd/*.service /etc/systemd/system/
sudo cp deployment/gunicorn.conf.py /opt/asset_management/
sudo cp deployment/nginx.conf /etc/nginx/sites-available/asset-management

# Create log directories
sudo mkdir -p /var/log/asset_management /var/run/asset_management
sudo chown asset_app:asset_app /var/log/asset_management /var/run/asset_management

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable asset-management asset-management-celery asset-management-celerybeat
sudo systemctl start asset-management asset-management-celery asset-management-celerybeat

# Configure Nginx
sudo ln -sf /etc/nginx/sites-available/asset-management /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL Certificate
```bash
# Install Certbot and get certificate
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
sudo systemctl enable certbot.timer
```

### 6. Firewall and Security
```bash
# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Setup monitoring and backups
sudo cp deployment/backup.sh /opt/asset_management/
sudo cp deployment/monitoring.sh /opt/asset_management/
sudo chmod +x /opt/asset_management/*.sh

# Add cron jobs
sudo -u asset_app crontab -e
# Add these lines:
# 0 2 * * * /opt/asset_management/backup.sh
# */5 * * * * /opt/asset_management/monitoring.sh
# 0 9 * * * cd /opt/asset_management && /opt/asset_management/venv/bin/python backend/manage.py send_warranty_alerts
```

## Verification

### Check Services
```bash
sudo systemctl status asset-management
sudo systemctl status asset-management-celery
sudo systemctl status nginx
sudo systemctl status mysql
sudo systemctl status redis
```

### Test Application
```bash
# Test API endpoint
curl -k https://your-domain.com/api/auth/profile/

# Check logs
sudo journalctl -u asset-management -f
sudo tail -f /var/log/asset_management/gunicorn_error.log
```

## Default Access

- **Application**: https://your-domain.com
- **Admin Panel**: https://your-domain.com/admin/
- **API**: https://your-domain.com/api/

### Demo Credentials (if sample data created)
- **Admin**: admin / admin123
- **Manager**: manager / manager123
- **Employee**: employee / employee123

## Maintenance Commands

```bash
# Update application
sudo -u asset_app -i
cd /opt/asset_management
git pull
source venv/bin/activate
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py collectstatic --noinput
npm install
npm run build
sudo systemctl restart asset-management

# View logs
sudo journalctl -u asset-management -f
sudo tail -f /var/log/nginx/error.log

# Backup manually
/opt/asset_management/backup.sh

# Check system health
/opt/asset_management/monitoring.sh
```

## Troubleshooting

### Common Issues

1. **Service won't start**: Check logs with `sudo journalctl -u asset-management`
2. **Database connection error**: Verify credentials in `.env` file
3. **Static files not loading**: Run `python manage.py collectstatic --noinput`
4. **Email not working**: Check SMTP settings in `.env`
5. **SSL certificate issues**: Run `sudo certbot renew --dry-run`

### Performance Tuning

1. **Database**: Add indexes for frequently queried fields
2. **Redis**: Configure memory limits and persistence
3. **Nginx**: Adjust worker processes and connections
4. **Gunicorn**: Tune worker count based on CPU cores

The system is now production-ready! 🎉