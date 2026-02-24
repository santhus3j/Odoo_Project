# Docker & Odoo Best Practices Guide
## How to Avoid Database Loss and Internal Server Errors

---

## PART 1: What Caused Your Problems

### Problem 1: Internal Server Error (500)
**Root Cause:** Database schema was incomplete. The Odoo cron threads couldn't find required tables like `ir_module_module`.

**Why it happened:** 
- Odoo started without the `-i base` flag
- The base modules weren't initialized
- Database existed but was empty/incomplete

### Problem 2: Database Loss (SanDB)
**Root Cause:** I deleted the Docker volume `odoo18_project_odoo18_db_data` to reset the corrupted database.

**Why you lost it:**
- No backup was taken before deletion
- Data was stored ONLY in that volume
- Once volume is deleted, data is permanently gone

---

## PART 2: How I Fixed the Internal Server Error

### Step 1: Diagnosed the Issue
```bash
# Checked running containers
docker ps -a

# Read error logs to find root cause
docker logs odoo18_app --tail 100
```
Found: `psycopg2.OperationalError: server closed the connection unexpectedly` and `relation "ir_module_module" does not exist`

### Step 2: Fixed the Dockerfile
**Changed from:**
```dockerfile
FROM odoo:18
USER root
RUN apt-get update && apt-get install -y fonts-urw-base35 fonts-liberation ttf-dejavu-core
USER odoo
```

**Changed to:**
```dockerfile
FROM odoo:18
USER root
RUN apt-get update && apt-get install -y fonts-urw-base35 fonts-liberation fonts-dejavu
USER odoo
```

**Why:** Package `ttf-dejavu-core` doesn't exist in Ubuntu Noble. Changed to `fonts-dejavu`.

### Step 3: Fixed the docker-compose.yml
**Added initialization command:**
```yaml
odoo:
  build: .
  image: odoo18_app
  container_name: odoo18_app
  depends_on:
    db:
      condition: service_healthy
  ports:
    - "8069:8069"
  environment:
    - HOST=db
    - USER=odoo
    - PASSWORD=odoo
  command: odoo -d odoo -i base  # ← THIS LINE FIXED IT
  volumes:
    - ./config:/etc/odoo
    - ./addons:/mnt/extra-addons
    - ./logs:/var/log/odoo
```

**Why:** 
- `command: odoo -d odoo -i base` tells Odoo to:
  - `-d odoo` = use database named "odoo"
  - `-i base` = initialize with base modules on first run
  - Creates all required database tables and schema

### Step 4: Removed Corrupted Volume & Restarted
```bash
docker volume rm odoo18_project_odoo18_db_data
docker compose down
docker compose up --build
```

---

## PART 3: How to AVOID These Issues Going Forward

### ✅ BACKUP YOUR DATABASE REGULARLY

#### Option 1: Automated Daily Backup (RECOMMENDED)
Create a backup script: `backup-db.sh`
```bash
#!/bin/bash
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup all Odoo databases
docker exec odoo18_db pg_dump -U odoo -d odoo > $BACKUP_DIR/odoo_$TIMESTAMP.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "odoo_*.sql" -mtime +7 -delete

echo "Database backed up to: $BACKUP_DIR/odoo_$TIMESTAMP.sql"
```

Make it executable and run daily:
```bash
chmod +x backup-db.sh
# Add to crontab (Linux/Mac):
# 0 2 * * * /path/to/backup-db.sh  (runs at 2 AM daily)
```

#### Option 2: Manual Backup Before Major Changes
```bash
# Backup before restarting or updating
docker exec odoo18_db pg_dump -U odoo -d odoo > odoo_backup_$(date +%Y%m%d).sql

# List backups
ls -lh *.sql
```

#### Option 3: Use Named Volumes with Backup Strategy
Update `docker-compose.yml`:
```yaml
volumes:
  odoo_db_volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/postgres_data

services:
  db:
    image: postgres:15
    volumes:
      - odoo_db_volume:/var/lib/postgresql/data
```

This stores data in `./postgres_data/` which is easier to backup.

---

### ✅ USE PROPER DATABASE INITIALIZATION

#### Correct docker-compose.yml Setup
```yaml
version: '3.9'

services:
  db:
    image: postgres:15
    container_name: odoo18_db
    environment:
      POSTGRES_DB: odoo
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
    volumes:
      - odoo_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U odoo"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  odoo:
    build: .
    image: odoo18_app
    container_name: odoo18_app
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8069:8069"
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
    # IMPORTANT: Initialize database on first run
    command: odoo -d odoo -i base
    volumes:
      - ./config:/etc/odoo
      - ./addons:/mnt/extra-addons
      - ./logs:/var/log/odoo
    restart: unless-stopped

volumes:
  odoo_db_data:
```

**Key points:**
- `command: odoo -d odoo -i base` ensures schema initialization
- `condition: service_healthy` waits for DB to be ready
- `restart: unless-stopped` auto-restarts on crash
- Named volume `odoo_db_data` is tracked by Docker

---

### ✅ AVOID DELETING VOLUMES

```bash
# DANGEROUS - DO NOT RUN
docker volume rm odoo18_project_odoo18_db_data  # ← Data is lost forever!

# SAFE - Inspect first
docker volume inspect odoo18_project_odoo18_db_data

# SAFE - Backup before removing
docker exec odoo18_db pg_dump -U odoo > backup.sql
docker volume rm odoo18_project_odoo18_db_data

# SAFE - Just stop containers (keeps data)
docker compose down  # Data persists in volume

# SAFE - Reset database without losing files
docker exec odoo18_db psql -U odoo -d odoo -c "DROP DATABASE odoo;"
docker exec odoo18_db psql -U odoo -c "CREATE DATABASE odoo;"
```

---

### ✅ PROPER ERROR DEBUGGING WORKFLOW

When you get an internal server error:

#### Step 1: Check Container Status
```bash
docker ps -a
# Shows which containers are running/stopped/crashed
```

#### Step 2: Read the Logs
```bash
# Last 100 lines
docker logs odoo18_app --tail 100

# Last 50 lines from all containers
docker compose logs -f

# Follow logs in real-time
docker logs -f odoo18_app
```

#### Step 3: Check Database Connection
```bash
# Verify DB is healthy
docker ps | grep odoo18_db

# List databases
docker exec odoo18_db psql -U odoo -c "\l"

# Check if required tables exist
docker exec odoo18_db psql -U odoo -d odoo -c "\dt" | grep ir_module_module
```

#### Step 4: Inspect Container Details
```bash
# Full container configuration
docker inspect odoo18_app

# Check port mappings
docker port odoo18_app

# Check environment variables
docker exec odoo18_app env | grep -i odoo
```

---

### ✅ PREVENT PACKAGE ERRORS IN DOCKERFILE

```dockerfile
# ❌ BAD - Can break if packages don't exist
FROM odoo:18
RUN apt-get update && apt-get install -y ttf-dejavu-core

# ✅ GOOD - Verify packages exist first
FROM odoo:18
RUN apt-get update && \
    apt-cache search fonts | grep dejavu && \
    apt-get install -y fonts-dejavu fonts-liberation

# ✅ BETTER - Pin versions
FROM odoo:18
RUN apt-get update && \
    apt-get install -y \
        fonts-dejavu=2.37-8 \
        fonts-liberation=1:2.1.5-3

# ✅ BEST - Use official Odoo image as-is
FROM odoo:18
# Don't modify unless absolutely necessary
```

---

### ✅ MONITOR ODOO HEALTH

Create a health check script: `check-health.sh`
```bash
#!/bin/bash

echo "=== Container Status ==="
docker ps -a | grep odoo

echo -e "\n=== Recent Logs ==="
docker logs odoo18_app --tail 20

echo -e "\n=== Database Check ==="
docker exec odoo18_db psql -U odoo -c "SELECT version();"

echo -e "\n=== Port Check ==="
netstat -tuln | grep 8069 || ss -tuln | grep 8069

echo -e "\n=== Disk Space ==="
docker system df
```

Run before and after updates:
```bash
bash check-health.sh
```

---

### ✅ VERSION CONTROL & DOCUMENTATION

Keep your project organized:

```
odoo18_project/
├── docker-compose.yml          # Your main config
├── Dockerfile                  # App image definition
├── .env                        # Environment variables (add to .gitignore)
├── config/                     # Odoo config files
├── addons/                     # Custom addons
├── logs/                       # Application logs
├── backups/                    # Database backups
├── postgres_data/              # Database files (add to .gitignore)
├── DOCKER_BEST_PRACTICES.md    # This guide
├── .gitignore                  # Exclude sensitive files
└── README.md                   # Setup instructions
```

**.gitignore example:**
```
.env
postgres_data/
backups/
logs/
*.sql
*.bak
```

---

### ✅ PRE-DEPLOYMENT CHECKLIST

Before restarting Odoo in production:

```bash
# 1. Backup database
docker exec odoo18_db pg_dump -U odoo -d odoo > pre_deploy_backup.sql

# 2. Check logs for errors
docker logs odoo18_app --tail 50 | grep -i error

# 3. Verify database schema
docker exec odoo18_db psql -U odoo -d odoo -c "SELECT COUNT(*) FROM ir_module_module;"

# 4. Test connectivity
curl http://localhost:8069 && echo "✓ Server responding" || echo "✗ Server down"

# 5. Review changes
git diff docker-compose.yml Dockerfile

# 6. Now safe to proceed
docker compose restart odoo
```

---

### ✅ EMERGENCY RECOVERY STEPS

If something goes wrong:

```bash
# Step 1: Keep containers running, check logs
docker logs -f odoo18_app

# Step 2: Don't delete volumes yet!
docker volume ls | grep odoo

# Step 3: Backup data even from broken container
docker exec odoo18_db pg_dump -U odoo -d odoo > emergency_backup.sql

# Step 4: Check disk space before restarting
docker system df

# Step 5: If needed, restart containers
docker compose restart odoo18_app

# Step 6: Verify recovery
docker ps
docker logs odoo18_app --tail 20
```

---

## PART 4: Quick Reference Commands

```bash
# BACKUP
docker exec odoo18_db pg_dump -U odoo -d odoo > backup.sql

# RESTORE
docker exec -i odoo18_db psql -U odoo < backup.sql

# VIEW LOGS
docker logs -f odoo18_app

# CHECK STATUS
docker ps -a

# RESTART
docker compose restart

# STOP SAFELY
docker compose down  # Keeps data
docker volume ls     # Verify volume still exists

# COMPLETELY RESET (with backup first!)
docker exec odoo18_db pg_dump -U odoo -d odoo > final_backup.sql
docker compose down
docker volume rm odoo18_project_odoo18_db_data
docker compose up -d --build

# INSPECT DATABASE
docker exec odoo18_db psql -U odoo -c "\l"        # List databases
docker exec odoo18_db psql -U odoo -d odoo -c "\dt"  # List tables
```

---

## SUMMARY

**To avoid database loss:**
1. ✅ Backup daily using automated script
2. ✅ Backup before major changes
3. ✅ Store backups in multiple locations
4. ✅ Never delete volumes without backup
5. ✅ Use version control for configs

**To avoid internal server errors:**
1. ✅ Always use `-i base` in Odoo initialization
2. ✅ Use healthchecks in docker-compose
3. ✅ Check logs immediately when errors occur
4. ✅ Verify database schema after restarts
5. ✅ Keep Dockerfile minimal and tested

**Key phrase to remember:** 
> "Backup first, investigate second, delete never (unless backed up)"
