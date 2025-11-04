# Row Level Security (RLS) Setup Guide

This FastAPI application uses PostgreSQL Row Level Security (RLS) to provide data isolation and enhanced security at the database level.

## 🔒 What is Row Level Security?

Row Level Security (RLS) is a PostgreSQL feature that allows you to control which rows users can access in a database table. It adds an additional layer of security beyond application-level access control.

### Benefits:
- **Defense in Depth**: Security at the database level, not just application level
- **Multi-tenancy**: Automatic data isolation between users/tenants
- **Compliance**: Helps meet regulatory requirements for data access
- **Fail-safe**: Even if application logic has bugs, database enforces access rules

## 🏗️ Architecture

This application uses **two database connections**:

### 1. Regular Connection (RLS-Restricted)
- **User**: `app_user`
- **Purpose**: Normal application operations
- **RLS**: **Enabled** - Policies applied automatically
- **Access**: Only sees data for the authenticated user
- **Used for**: User-facing API endpoints

### 2. Admin Connection (RLS-Bypass)
- **User**: `app_admin` (superuser)
- **Purpose**: System operations and admin tasks
- **RLS**: **Bypassed** - Full database access
- **Access**: Can see and modify all data
- **Used for**:
  - Creating users (registration)
  - Sending notifications
  - Creating logs
  - Migrations
  - Bulk operations

## 📋 Setup Instructions

### Step 1: Create Database Users

Connect to PostgreSQL as a superuser and run:

```sql
-- Create restricted user (with RLS)
CREATE USER app_user WITH PASSWORD 'your_secure_password';

-- Create admin user (bypasses RLS)
CREATE USER app_admin WITH PASSWORD 'your_admin_password' SUPERUSER;

-- Grant permissions
GRANT CONNECT ON DATABASE your_db_name TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
```

### Step 2: Configure Environment Variables

Update your `.env` file:

```env
# Regular DB User (with RLS policies applied)
DB_USERNAME=app_user
DB_PASSWORD=your_secure_password

# Admin DB User (bypasses RLS policies)
DB_ADMIN_USERNAME=app_admin
DB_ADMIN_PASSWORD=your_admin_password

# Database Name
DB_NAME=your_db_name
```

### Step 3: Run Database Migrations

```bash
# Create and run migrations for UUID changes
alembic revision --autogenerate -m "Convert to UUID and setup for RLS"
alembic upgrade head
```

### Step 4: Apply RLS Policies

Run the RLS setup script with admin credentials:

```bash
psql -U app_admin -d your_db_name -f sql/setup_rls_policies.sql
```

Or manually apply the policies (see `sql/setup_rls_policies.sql`)

### Step 5: Test the Setup

```bash
# Start the application
fastapi dev

# Test that regular users can only see their own data
# Test that admin operations work correctly
```

## 🔍 How It Works

### 1. User Authentication
When a user logs in, the JWT token contains their user ID (UUID).

### 2. Request Processing
For each authenticated request:
1. The RLS middleware extracts the user ID from the JWT token
2. The user ID is stored in a context variable
3. When a database session is created, it sets: `SET LOCAL app.current_user_id = '<user_id>'`

### 3. RLS Policy Application
PostgreSQL automatically applies RLS policies:
```sql
-- Example: Users can only see their own data
CREATE POLICY users_select_own
    ON users
    FOR SELECT
    USING (id::text = current_setting('app.current_user_id', true));
```

### 4. Query Execution
All queries are automatically filtered:
```sql
-- User executes:
SELECT * FROM users;

-- PostgreSQL actually runs:
SELECT * FROM users 
WHERE id::text = current_setting('app.current_user_id', true);
```

## 🛠️ Using RLS in Your Application

### For Regular Endpoints (with RLS)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps.db_deps import get_db_with_rls

@router.get("/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db_with_rls)  # RLS applied
):
    # This query automatically filters to current user's data
    result = await db.execute(select(User))
    return result.scalars().first()
```

### For Public Endpoints (no auth required)

```python
from app.api.deps.db_deps import get_db_without_auth

@router.post("/register")
async def register(
    db: AsyncSession = Depends(get_db_without_auth)  # No RLS
):
    # Used for public endpoints like registration
    pass
```

### For Admin Operations (bypass RLS)

```python
from app.api.deps.db_deps import get_admin_session

@router.post("/create-notification")
async def create_notification(
    db: AsyncSession = Depends(get_admin_session)  # Bypasses RLS
):
    # Can create notifications for any user
    # Can access all data without restrictions
    pass
```

## 📊 Current RLS Policies

### Users Table
- **SELECT**: Users can only see their own profile
- **UPDATE**: Users can only update their own profile
- **INSERT**: Anyone can register (public operation)
- **DELETE**: Disabled (controlled by admin)

### Notifications Table
- **SELECT**: Users can only see their own notifications
- **UPDATE**: Users can only update their own notifications
- **INSERT**: System operation (uses admin connection)
- **DELETE**: Disabled (controlled by admin)

### Logs Table
- **SELECT**: Users can see their own logs + system logs (where user_id IS NULL)
- **INSERT**: System operation (uses admin connection)
- **UPDATE**: Disabled (logs are immutable)
- **DELETE**: Disabled (logs are permanent)

## 🔐 Security Best Practices

### ✅ DO:
- Always use `get_db_with_rls()` for user-facing operations
- Use `get_admin_session()` only for system operations
- Test RLS policies thoroughly before production
- Monitor database logs for suspicious activity
- Keep admin credentials separate and highly secured
- Use environment variables for credentials, never hardcode
- Regularly audit RLS policies
- Log all admin session usage

### ❌ DON'T:
- Don't use admin connection for user requests
- Don't hardcode user IDs in queries
- Don't bypass RLS unless absolutely necessary
- Don't trust user input for user_id parameters
- Don't share admin credentials
- Don't disable RLS in production
- Don't create overly permissive policies

## 🧪 Testing RLS Policies

### Manual Testing

```bash
# Connect as restricted user
psql -U app_user -d your_db_name

# Set current user context
SET app.current_user_id = 'some-uuid-here';

# Try to select data - should only see data for that user
SELECT * FROM users;
SELECT * FROM notifications;
```

### Automated Testing

```python
import pytest
from app.db.database import get_db, get_admin_db

@pytest.mark.asyncio
async def test_rls_user_isolation():
    # Test that users can only see their own data
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    
    # Create users with admin connection
    async for admin_session in get_admin_db():
        # Create test users
        pass
    
    # Test with user1 connection
    async for session in get_db(user1_id):
        result = await session.execute(select(User))
        users = result.scalars().all()
        assert len(users) == 1
        assert users[0].id == user1_id
```

## 📝 Customizing RLS Policies

### Adding New Policies

1. **Create the policy SQL**:
```sql
CREATE POLICY my_custom_policy
    ON my_table
    FOR SELECT
    USING (user_id::text = current_setting('app.current_user_id', true));
```

2. **Add to migration** or run with admin connection

3. **Test thoroughly**

### Example: Multi-Tenant Support

```sql
-- Set organization context
SET LOCAL app.current_org_id = 'org-uuid';

-- Policy for organization isolation
CREATE POLICY org_isolation_policy
    ON users
    FOR ALL
    USING (organization_id::text = current_setting('app.current_org_id', true));
```

### Example: Admin Override

```sql
-- Policy that allows admin users to see everything
CREATE POLICY admin_override
    ON users
    FOR SELECT
    USING (
        id::text = current_setting('app.current_user_id', true)
        OR current_setting('app.user_role', true) = 'admin'
    );
```

## 🚨 Troubleshooting

### Issue: "permission denied for table"
**Solution**: Grant proper permissions to app_user
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

### Issue: "No rows returned" when data should exist
**Solution**: Check if RLS policy is too restrictive or current_user_id is not set
```sql
-- Debug: Check current setting
SELECT current_setting('app.current_user_id', true);
```

### Issue: "unrecognized configuration parameter"
**Solution**: Make sure you're using PostgreSQL 9.5+

### Issue: Admin operations not working
**Solution**: Ensure admin user has SUPERUSER or BYPASSRLS privilege
```sql
ALTER USER app_admin BYPASSRLS;
```

## 📚 Additional Resources

- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [RLS Best Practices](https://www.postgresql.org/docs/current/ddl-rowsecurity.html#DDL-ROWSECURITY-BEST-PRACTICES)
- [SQLAlchemy and RLS](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)

## 🔄 Migration from Non-RLS Setup

If you have an existing database without RLS:

1. **Backup your database**
2. **Create new database users**
3. **Update environment variables**
4. **Apply RLS policies** (existing data remains)
5. **Test thoroughly in staging**
6. **Deploy to production**

Note: RLS policies are added on top of existing data - no data migration needed!

