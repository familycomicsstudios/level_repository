# Vercel Deployment Instructions

## 1. Install Vercel CLI (if not already installed)
```bash
npm i -g vercel
```

## 2. Login to Vercel
```bash
vercel login
```

## 3. Set Environment Variables in Vercel
In your Vercel project dashboard, add these environment variables:

```
SECRET_KEY=8n*-hxci%26du^xj-mkeprymdnzwxzhjb15r5f1)q(9a%va$ai
DEBUG=False
POSTGRES_URL=postgres://postgres.xrqsenwyychcvpclrmur:iweQm4wqZWY7Irfp@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
POSTGRES_DATABASE=postgres
POSTGRES_HOST=db.xrqsenwyychcvpclrmur.supabase.co
POSTGRES_USER=postgres.xrqsenwyychcvpclrmur
POSTGRES_PASSWORD=iweQm4wqZWY7Irfp
SUPABASE_URL=https://xrqsenwyychcvpclrmur.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhycXNlbnd5eWNoY3ZwY2xybXVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxMzc3NzYsImV4cCI6MjA4NDcxMzc3Nn0.vwU_y3cYnfDRhUiqFAKt12TB-tgP3vZxHO6ew5OlrzY
```

## 4. Deploy to Vercel
```bash
vercel --prod
```

## 5. Run Migrations on Vercel
After deployment, you need to run migrations. You can either:

### Option A: Use Vercel CLI
```bash
vercel env pull
python manage.py migrate
```

### Option B: Create a one-time deployment script
Add a `vercel_migrate.py` file and run it once after deployment.

## Important Notes:
- The app will use SQLite locally and Supabase PostgreSQL in production
- Static files are handled by WhiteNoise
- Make sure to add your Vercel domain to ALLOWED_HOSTS (already configured for .vercel.app)
- Database migrations will run automatically during build

## Local Development:
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Troubleshooting:
- If you get database errors, check that POSTGRES_URL is correctly set in Vercel environment variables
- For static file issues, run `python manage.py collectstatic` locally to test
- Check Vercel logs with `vercel logs`
