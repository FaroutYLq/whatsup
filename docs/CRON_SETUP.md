# Automated Scheduling with Cron

This guide explains how to schedule the ArXiv Weekly Digest 
to run automatically every day.

## Overview

Cron is a time-based job scheduler in Unix-like operating 
systems (macOS, Linux). It allows you to run scripts 
automatically at specified times.

---

## Basic Cron Syntax

A cron job consists of:
```
* * * * * command-to-execute
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, 0 & 7 = Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

Examples:
- `0 8 * * *` - Every day at 8:00 AM
- `30 9 * * 1-5` - Weekdays at 9:30 AM
- `0 18 * * *` - Every day at 6:00 PM

---

## Setup Instructions

### Step 1: Find Your Python Path

First, find the full path to your Python executable:

```bash
which python3
```

Example output: `/usr/local/bin/python3`

### Step 2: Find Your Project Path

Note the full path to your whatsup directory:

```bash
cd /path/to/whatsup
pwd
```

Example output: `/Users/yourusername/Documents/whatsup`

### Step 3: Create a Wrapper Script (Recommended)

Create a script to handle logging and environment:

```bash
cd /Users/yourusername/Documents/whatsup
nano run_digest.sh
```

Add this content (adjust paths):

```bash
#!/bin/bash

# Set paths
PROJECT_DIR="/Users/yourusername/Documents/whatsup"
PYTHON="/usr/local/bin/python3"
LOG_FILE="$PROJECT_DIR/digest.log"

# Change to project directory
cd "$PROJECT_DIR"

# Run the digest and log output
echo "=== ArXiv Digest - $(date) ===" >> "$LOG_FILE"
$PYTHON src/main.py config.yaml >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
```

Make it executable:

```bash
chmod +x run_digest.sh
```

### Step 4: Open Crontab

Open the cron editor:

```bash
crontab -e
```

If prompted, choose your preferred editor (nano is easiest).

### Step 5: Add Cron Job

Add this line (adjust the path):

```cron
# ArXiv Weekly Digest - Run every day at 8:00 AM
0 8 * * * /Users/yourusername/Documents/whatsup/run_digest.sh
```

Save and exit:
- In nano: Press `Ctrl+X`, then `Y`, then `Enter`
- In vim: Press `Esc`, type `:wq`, press `Enter`

### Step 6: Verify Cron Job

List your cron jobs:

```bash
crontab -l
```

You should see your new job listed.

---

## Common Schedule Examples

### Every day at 8:00 AM
```cron
0 8 * * * /path/to/whatsup/run_digest.sh
```

### Weekdays only at 9:00 AM
```cron
0 9 * * 1-5 /path/to/whatsup/run_digest.sh
```

### Twice weekly: 8 AM and 6 PM
```cron
0 8,18 * * * /path/to/whatsup/run_digest.sh
```

### Every Monday at 7:00 AM
```cron
0 7 * * 1 /path/to/whatsup/run_digest.sh
```

---

## Testing Your Setup

### Test the wrapper script manually

```bash
cd /Users/yourusername/Documents/whatsup
./run_digest.sh
```

Check the log file:

```bash
cat digest.log
```

### Test with a short-term cron job

Add a job to run in 2 minutes:

```bash
crontab -e
```

Add (adjust the time to 2 minutes from now):

```cron
# Test job - runs once
25 14 * * * /path/to/whatsup/run_digest.sh
```

Wait 2 minutes, then check:

```bash
cat /path/to/whatsup/digest.log
```

Remove the test job after verifying:

```bash
crontab -e
# Delete the test line
```

---

## Troubleshooting

### Cron job doesn't run

**Check if cron service is running:**

```bash
# macOS
sudo launchctl list | grep cron

# Linux
systemctl status cron
```

**Check cron logs:**

```bash
# macOS
log show --predicate 'process == "cron"' --last 1h

# Linux
grep CRON /var/log/syslog
```

### "Command not found" errors

Cron has a limited environment. Always use absolute paths:

✗ Wrong:
```bash
python src/main.py
```

✓ Correct:
```bash
/usr/local/bin/python3 /full/path/to/src/main.py
```

### Environment variables not available

Cron doesn't load your shell profile. Set variables in 
the wrapper script:

```bash
#!/bin/bash
export PATH="/usr/local/bin:/usr/bin:/bin"
export OPENAI_API_KEY="your-key"  # If using env vars
# ... rest of script
```

### Permission denied

Make sure the script is executable:

```bash
chmod +x run_digest.sh
```

### No email received

1. Check the log file for errors
2. Run the script manually first
3. Verify Gmail setup (see GMAIL_SETUP.md)

---

## macOS-Specific: Full Disk Access

On macOS Catalina and later, cron may need permission:

1. Open **System Preferences → Security & Privacy**
2. Click **Privacy** tab
3. Select **Full Disk Access** from the left
4. Click the lock icon to make changes
5. Click **+** and add `/usr/sbin/cron`
6. Restart your Mac

---

## Alternative: Launchd (macOS)

macOS prefers launchd over cron. To use launchd:

### Create a plist file

```bash
nano ~/Library/LaunchAgents/com.arxiv.digest.plist
```

Add this content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.arxiv.digest</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourusername/Documents/whatsup/run_digest.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/yourusername/Documents/whatsup/digest.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/Documents/whatsup/digest.log</string>
</dict>
</plist>
```

### Load the job

```bash
launchctl load ~/Library/LaunchAgents/com.arxiv.digest.plist
```

### Verify it's loaded

```bash
launchctl list | grep arxiv
```

### To unload (stop)

```bash
launchctl unload ~/Library/LaunchAgents/com.arxiv.digest.plist
```

---

## Monitoring and Maintenance

### Check logs regularly

```bash
tail -f /path/to/whatsup/digest.log
```

### Log rotation

To prevent large log files, add to your wrapper script:

```bash
# Keep only last 100 lines
tail -n 100 "$LOG_FILE" > "$LOG_FILE.tmp"
mv "$LOG_FILE.tmp" "$LOG_FILE"
```

### Email notifications on failure

Add to wrapper script:

```bash
if [ $? -ne 0 ]; then
    echo "ArXiv Digest failed!" | mail -s "Digest Error" you@email.com
fi
```

---

## Stopping/Removing the Cron Job

To remove the scheduled job:

```bash
crontab -e
```

Delete the line with your job, then save and exit.

To remove all cron jobs:

```bash
crontab -r
```

