# Supabase Authentication Implementation Guide

This guide explains how to set up and configure Supabase authentication with email verification and Google OAuth for the Steadi application.

## Prerequisites

1. Create a Supabase account at [https://supabase.com](https://supabase.com)
2. Create a new Supabase project
3. Google Cloud Platform account for Google OAuth setup

## Setup Steps

### 1. Supabase Project Configuration

1. Navigate to your Supabase project dashboard
2. In Authentication > Settings > Email Auth:
   - Enable "Confirm email" to require email verification
   - Customize email templates for confirmation and password reset

3. Configure redirect URLs (in Authentication > URL Configuration):
   - Add your frontend URL: `http://localhost:5173` (or your production URL)
   - Add redirect URL path: `/auth/callback`

### 2. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Navigate to "APIs & Services" > "Credentials"
4. Create OAuth Client ID:
   - Application type: Web application
   - Authorized JavaScript origins: `https://[YOUR-PROJECT].supabase.co`
   - Authorized redirect URIs: `https://[YOUR-PROJECT].supabase.co/auth/v1/callback`

5. In Supabase Authentication > Providers:
   - Enable Google provider
   - Enter Client ID and Client Secret from Google Cloud Console
   - Save changes

### 3. Frontend Configuration

1. Create `.env` file in `steadi-frontend/` with the following variables:
   ```
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key
   VITE_API_URL=http://localhost:8000
   ```

### 4. Backend Configuration

1. Create `.env` file in `app/` with the following variables:
   ```
   # Existing variables
   DATABASE_URL=postgresql://postgres:password@localhost:5432/steadi
   JWT_SECRET=your_jwt_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Supabase variables
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_JWT_SECRET=your_supabase_jwt_secret
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

2. Get the JWT secret from Supabase:
   - Go to Settings > API
   - Copy the JWT Secret

3. Get the Anon Key from Supabase:
   - Go to Settings > API
   - Copy the anon key (public)

### 5. Database Migration for Supabase Integration

Run the following SQL in your database to add the `supabase_id` column to the `user` table:

```sql
ALTER TABLE "user" ADD COLUMN supabase_id TEXT UNIQUE;
CREATE INDEX idx_user_supabase_id ON "user" (supabase_id);
ALTER TABLE "user" ALTER COLUMN password_hash DROP NOT NULL;
```

## Testing the Integration

1. Start the backend server:
   ```
   cd app
   uvicorn main:app --reload
   ```

2. Start the frontend development server:
   ```
   cd steadi-frontend
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:5173`
4. Click "Get Started" to go to the auth page
5. Test both email/password signup and Google OAuth login
6. Verify that email confirmation is required for new signups

## Troubleshooting

### Email Verification Issues
- Check Supabase email provider settings
- Verify email templates in Supabase dashboard
- Check spam folder for verification emails

### Google OAuth Issues
- Verify redirect URIs in Google Cloud Console
- Check that Google provider is enabled in Supabase
- Confirm Client ID and Secret are correctly entered

### Backend Integration Issues
- Verify JWT secret is correctly set in backend .env
- Check logs for authentication errors
- Ensure database migration for supabase_id was applied 