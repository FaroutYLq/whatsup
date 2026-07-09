# Gmail SMTP Setup Guide

This guide shows you how to set up Gmail to send your 
weekly ArXiv digest emails.

## Overview

Gmail requires an **App Password** for third-party 
applications. You cannot use your regular Gmail password 
for security reasons.

---

## Prerequisites

- A Gmail account
- Two-Factor Authentication (2FA) must be enabled

---

## Step-by-Step Setup

### Step 1: Enable Two-Factor Authentication

If you haven't already enabled 2FA:

1. Go to your Google Account: 
   https://myaccount.google.com/

2. Click **Security** in the left sidebar

3. Under "Signing in to Google," 
   click **2-Step Verification**

4. Click **Get Started** and follow the prompts to 
   set up 2FA
   - You can use your phone, authenticator app, or 
     security key

5. Complete the 2FA setup

### Step 2: Generate an App Password

1. Go to your Google Account: 
   https://myaccount.google.com/

2. Click **Security** in the left sidebar

3. Under "Signing in to Google," 
   click **2-Step Verification**

4. Scroll down to the bottom of the page

5. Click **App passwords**
   - If you don't see this option, make sure 2FA is 
     fully enabled

6. You may be asked to sign in again

7. In the "Select app" dropdown, choose **Mail**

8. In the "Select device" dropdown, choose **Other** 
   and type a name like "ArXiv Digest"

9. Click **Generate**

10. Google will display a 16-character app password
    - It will look like: `abcd efgh ijkl mnop`
    - **Copy this password immediately** 
      (you won't see it again)

### Step 3: Update Configuration

1. Open your `config.yaml` file

2. Update the email section:

```yaml
email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  from_email: your.email@gmail.com
  password: abcdefghijklmnop  # 16-char app password
  to_email: your.email@gmail.com  # Can be different
```

**Important Notes:**
- Remove spaces from the app password when pasting
- The app password is **NOT** your Gmail password
- Use your full Gmail address for `from_email`

### Step 4: Test the Setup

Run the digest manually to test:

```bash
cd /path/to/whatsup
python src/main.py
```

If configured correctly, you should receive an email.

---

## Troubleshooting

### "Authentication failed" error

**Possible causes:**
1. App password is incorrect
   - Regenerate a new app password
   - Remove all spaces when copying

2. Using regular Gmail password instead of app password
   - Must use the 16-character app password

3. 2FA not enabled
   - Enable 2FA first, then create app password

### "SMTP connection failed" error

**Check:**
- SMTP server: `smtp.gmail.com`
- SMTP port: `587` (for TLS)
- Internet connection is working
- Firewall isn't blocking SMTP connections

### "Quota exceeded" error

Gmail has sending limits:
- Free accounts: ~500 emails/day
- This shouldn't be an issue for weekly digests, but if 
  testing repeatedly, wait a few minutes

### Can't find "App passwords" option

**Requirements:**
1. 2FA must be fully enabled
2. Using a personal Gmail account 
   (workspace accounts may have restrictions)
3. Try accessing directly: 
   https://myaccount.google.com/apppasswords

---

## Security Best Practices

1. **Protect your app password**
   - Treat it like a password
   - Don't share or commit to version control

2. **Use environment variables** (optional but recommended):
   - Instead of storing password in config.yaml:
   ```bash
   export ARXIV_EMAIL_PASSWORD="your-app-password"
   ```
   - Update config.yaml to use: `${ARXIV_EMAIL_PASSWORD}`

3. **Revoke unused app passwords**
   - If you stop using the digest, revoke the app password
   - Go to: Google Account → Security → App passwords
   - Click trash icon next to the password

4. **Monitor account activity**
   - Check Google account activity periodically
   - Look for unexpected sign-ins

---

## Using a Different Email Provider

If you use a different email provider:

### Outlook/Hotmail

```yaml
email:
  smtp_server: smtp-mail.outlook.com
  smtp_port: 587
  from_email: your.email@outlook.com
  password: your-password
  to_email: your.email@outlook.com
```

### Yahoo Mail

```yaml
email:
  smtp_server: smtp.mail.yahoo.com
  smtp_port: 587
  from_email: your.email@yahoo.com
  password: your-app-password  # Also requires app password
  to_email: your.email@yahoo.com
```

### Other Providers

Look up your provider's SMTP settings:
- SMTP server address
- SMTP port (usually 587 for TLS or 465 for SSL)
- Whether they require app passwords

