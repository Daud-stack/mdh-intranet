# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                       ngrok Setup Instructions                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

## ✅ ngrok Has Been Downloaded!

ngrok v3.35.0 has been successfully downloaded to:
  c:\Users\HomePC\mdh_intranet\ngrok\ngrok.exe

## 🔑 Authentication Required

ngrok v3 requires an authentication token to use. This is FREE!

### Step-by-Step Setup:

1. **Create a FREE ngrok Account**
   - Go to: https://dashboard.ngrok.com/signup
   - Sign up with your email (Gmail, GitHub, etc.)
   - It's completely free for basic use!

2. **Get Your Authentication Token**
   - After signing in, go to: https://dashboard.ngrok.com/get-started/your-authtoken
   - Copy your authtoken (looks like: 2abc123def456...)

3. **Configure ngrok with Your Token**
   Run this command in PowerShell:
   ```powershell
   .\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN_HERE
   ```
   
   Example:
   ```powershell
   .\ngrok\ngrok.exe config add-authtoken 2abc123def456ghi789jkl
   ```

4. **Start ngrok Tunnel**
   ```powershell
   .\ngrok\ngrok.exe http 8000
   ```

5. **Copy the URL**
   You'll see output like:
   ```
   Forwarding    https://abc123.ngrok.io -> http://localhost:8000
   ```
   
   Copy the URL: **https://abc123.ngrok.io**

6. **Update Django Settings**
   Edit: c:\Users\HomePC\mdh_intranet\mdh_intranet\settings.py
   
   Find the line:
   ```python
   ALLOWED_HOSTS = os.environ.get(
       'DJANGO_ALLOWED_HOSTS',
       'localhost,127.0.0.1,[::1],host.docker.internal,10.232.190.161'
   ).split(',')
   ```
   
   Change to:
   ```python
   ALLOWED_HOSTS = os.environ.get(
       'DJANGO_ALLOWED_HOSTS',
       'localhost,127.0.0.1,[::1],host.docker.internal,10.232.190.161,abc123.ngrok.io'
   ).split(',')
   ```
   
   (Replace abc123.ngrok.io with YOUR actual ngrok URL - without the https://)

7. **Restart Django Server**
   - Stop the current server (Ctrl+C in the terminal)
   - Start it again: `python manage.py runserver`

8. **Access Your App**
   Open your browser and go to: https://abc123.ngrok.io
   (Use YOUR ngrok URL)

9. **Test Office Web Viewer**
   - Login to your app
   - Go to Documents
   - Upload a .docx file
   - Click "View Online"
   - It should work now!

## 📋 Quick Command Reference

```powershell
# Add auth token (do this once)
.\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN

# Start tunnel
.\ngrok\ngrok.exe http 8000

# Stop tunnel
# Press Ctrl+C
```

## 🎯 Why is This Needed?

Microsoft Office Web Viewer needs to access your documents from the internet.
ngrok creates a secure tunnel from the internet to your localhost:8000.

```
Internet ←→ ngrok.io ←→ Your Computer (localhost:8000)
```

## ⚠️ Important Notes

1. **Free Plan Limitations:**
   - URL changes each time you restart ngrok
   - 40 connections/minute limit
   - Perfect for testing!

2. **Keep ngrok Running:**
   - Keep the ngrok terminal window open
   - If you close it, the tunnel stops

3. **Update ALLOWED_HOSTS:**
   - Every time ngrok restarts, you get a new URL
   - Update settings.py with the new URL

4. **Security:**
   - ngrok URLs are publicly accessible
   - Anyone with the URL can access your app
   - Good for testing, don't use in production

## 🚀 Alternative: ngrok Free Static Domain

If you want a consistent URL that doesn't change:
1. Upgrade to ngrok's free plan with static domain
2. Visit: https + The URL you get is permanent

## 💡 Troubleshooting

**Problem**: "Invalid authtoken"
- Make sure you copied the entire token
- No spaces or extra characters

**Problem**: "Connection refused"
- Make sure Django is running on port 8000
- Run: `python manage.py runserver`

**Problem**: ngrok works but Office Viewer doesn't
- Check ALLOWED_HOSTS includes your ngrok URL
- Restart Django after updating settings.py
- Make sure you're accessing via the ngrok URL (not localhost)

**Problem**: "This site can't be reached"
- ngrok might have stopped
- Restart ngrok tunnel

## 📞 Need Help?

Check the terminal output for any error messages.
ngrok will show you exactly what's happening!

═══════════════════════════════════════════════════════════════════════════

Ready to set up? Follow the steps above! 🚀
