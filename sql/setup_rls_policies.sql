-- Setup Row Level Security (RLS) Policies
-- Run this script with admin database credentials

-- ============================================
-- STEP 1: Create database users
-- ============================================

-- Create restricted user (uses RLS policies)
-- Replace 'app_user' and 'secure_password' with your actual credentials
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'app_user') THEN
        CREATE USER app_user WITH PASSWORD 'secure_password';
    END IF;
END $$;

-- Create admin user (bypasses RLS policies)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'app_admin') THEN
--         CREATE USER app_admin WITH PASSWORD 'admin_secure_password';
--         GRANT BYPASSRLS TO app_admin;
--     END IF;
-- END $$;

-- Grant necessary permissions to restricted user
GRANT CONNECT ON DATABASE your_database_name TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_user;

-- ============================================
-- STEP 2: Enable RLS on tables
-- ============================================

-- Enable RLS for users table
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users FORCE ROW LEVEL SECURITY;

-- Enable RLS for notifications table
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications FORCE ROW LEVEL SECURITY;

-- Enable RLS for logs table
ALTER TABLE public.logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.logs FORCE ROW LEVEL SECURITY;

-- ============================================
-- STEP 3: Create RLS policies for USERS table
-- ============================================

-- Policy: Users can only see their own profile
CREATE POLICY users_select_own
    ON users
    FOR SELECT
    USING (id = current_setting('app.current_user_id', true)::uuid);

-- Policy: Users can update their own profile
CREATE POLICY users_update_own
    ON users
    FOR UPDATE
    USING (id = current_setting('app.current_user_id', true)::uuid)
    WITH CHECK (id = current_setting('app.current_user_id', true)::uuid);

-- Policy: Allow user registration (INSERT for anyone)
CREATE POLICY users_insert_own
    ON users
    FOR INSERT
    WITH CHECK (true);  -- Anyone can register, but other validations happen in app logic

-- Policy: Users cannot delete their own account (controlled by admin)
-- If you want to allow self-deletion, uncomment below:
-- CREATE POLICY users_delete_own
--     ON users
--     FOR DELETE
--     USING (id::text = current_setting('app.current_user_id', true));

-- ============================================
-- STEP 4: Create RLS policies for NOTIFICATIONS table
-- ============================================

-- Policy: Users can only see their own notifications
CREATE POLICY notifications_select_own
    ON notifications
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id', true)::uuid);

-- Policy: System can insert notifications for any user (handled by admin connection)
CREATE POLICY notifications_insert_system
    ON notifications
    FOR INSERT
    WITH CHECK (true);  -- Insert is controlled by admin session

-- Policy: Users can update their own notifications (mark as read)
CREATE POLICY notifications_update_own
    ON notifications
    FOR UPDATE
    USING (user_id = current_setting('app.current_user_id', true)::uuid)
    WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);

-- Policy: Users cannot delete notifications (controlled by admin)
-- If you want to allow deletion, uncomment below:
-- CREATE POLICY notifications_delete_own
--     ON notifications
--     FOR DELETE
--     USING (user_id::text = current_setting('app.current_user_id', true));

-- ============================================
-- STEP 5: Create RLS policies for LOGS table
-- ============================================

-- Policy: Users can only see their own logs
CREATE POLICY logs_select_own
    ON logs
    FOR SELECT
    USING (
        user_id = current_setting('app.current_user_id', true)::uuid
        OR user_id IS NULL  -- Allow viewing system logs
    );

-- Policy: System can insert logs (handled by admin connection)
CREATE POLICY logs_insert_system
    ON logs
    FOR INSERT
    WITH CHECK (true);  -- Insert is controlled by admin session

-- Policy: Users cannot update logs (immutable)
-- Logs should be immutable, so no UPDATE policy

-- Policy: Users cannot delete logs (controlled by admin)
-- Logs should be permanent, so no DELETE policy for regular users

-- ============================================
-- STEP 6: Grant bypass to admin user
-- ============================================

-- Admin user should bypass RLS policies
-- This is automatically done by making them SUPERUSER
-- If not using SUPERUSER, you can grant BYPASSRLS privilege:
-- ALTER USER app_admin BYPASSRLS;

-- ============================================
-- STEP 7: Verify RLS setup
-- ============================================

-- Check which tables have RLS enabled
SELECT 
    schemaname, 
    tablename, 
    rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Check all policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public';

-- ============================================
-- NOTES:
-- ============================================
-- 1. Always test RLS policies thoroughly before deploying to production
-- 2. Use the admin connection for system operations (user creation, notifications, logs)
-- 3. Use the regular connection for user-facing operations
-- 4. Monitor the 'app.current_user_id' setting in your application logs
-- 5. Consider adding policies for admin users if needed
-- 6. Update database names, usernames, and passwords according to your setup

