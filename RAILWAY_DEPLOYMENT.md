# Railway Deployment Guide

## 🚀 Quick Deploy to Railway

### Method 1: One-Click Deploy
1. Click the deploy button (if available) or continue with manual setup

### Method 2: Manual Setup

#### Step 1: Create Railway Project
\`\`\`bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway new
\`\`\`

#### Step 2: Add PostgreSQL Database
1. Go to your Railway dashboard
2. Click "Add Service" → "Database" → "PostgreSQL"
3. Railway will automatically provide the `DATABASE_URL` environment variable

#### Step 3: Configure Environment Variables
Set these in your Railway dashboard under "Variables":

**Required:**
- `DATABASE_URL` (automatically set by Railway PostgreSQL)
- `SESSION_SECRET_KEY` (generate a secure random string)
- `JWT_SECRET_KEY` (generate a secure random string)

**Optional but Recommended:**
- `FRONTEND_URL` (your frontend app URL)
- `GOOGLE_CLIENT_ID` (for Google OAuth)
- `GOOGLE_CLIENT_SECRET` (for Google OAuth)
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` (for email features)

#### Step 4: Deploy
\`\`\`bash
# Connect to your Railway project
railway link

# Deploy your code
railway up
\`\`\`

## 🔧 Post-Deployment Setup

### 1. Verify Deployment
Visit your Railway app URL and check the health endpoint:
\`\`\`
https://your-app.railway.app/
\`\`\`

### 2. Run Database Setup (if needed)
\`\`\`bash
railway run python scripts/railway_setup.py
\`\`\`

### 3. Update Frontend CORS
Make sure your frontend URL is added to the CORS origins in `main.py`

## 📊 Monitoring

### Health Check
Your app includes a health check endpoint at `/` that Railway uses for monitoring.

### Logs
View logs in Railway dashboard or via CLI:
\`\`\`bash
railway logs
\`\`\`

## 🔒 Security Considerations

1. **Environment Variables**: Never commit secrets to your repository
2. **Database**: Railway PostgreSQL is automatically secured
3. **HTTPS**: Railway provides HTTPS by default
4. **CORS**: Configure properly for your frontend domain

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection Error**
   - Check if PostgreSQL service is running
   - Verify `DATABASE_URL` environment variable

2. **Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python path configuration

3. **File Upload Issues**
   - Railway has ephemeral storage
   - Consider using AWS S3 for persistent file storage

4. **Memory/CPU Limits**
   - Monitor resource usage in Railway dashboard
   - Optimize AI model loading if needed

### Getting Help
- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Check Railway status: https://status.railway.app
