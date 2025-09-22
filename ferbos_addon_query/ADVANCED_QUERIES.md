# Advanced Query Support - Ferbos Mini Addon

This document explains how to enable and safely use all SQL query types (INSERT, UPDATE, DELETE) in your Ferbos Mini Addon.

## ⚠️ **IMPORTANT SECURITY WARNING**

**Enabling all query types is DANGEROUS and can cause:**
- **Data loss** - Accidental DELETE operations
- **Data corruption** - Invalid UPDATE operations  
- **System instability** - Breaking Home Assistant functionality
- **No recovery** - Deleted data cannot be restored

**Only enable this if you:**
- Understand the risks
- Have database backups
- Know what you're doing
- Accept full responsibility

## 🔧 **Configuration**

### **Step 1: Enable All Queries**

In your addon configuration, set:

```json
{
  "allow_all_queries": true,
  "allowed_tables": ["custom_table1", "custom_table2"]
}
```

### **Step 2: Configure Table Restrictions (Recommended)**

For safety, specify which tables can be modified:

```json
{
  "allow_all_queries": true,
  "allowed_tables": [
    "custom_sensors",
    "user_data", 
    "temp_data"
  ]
}
```

**Leave `allowed_tables` empty to allow ALL tables (VERY DANGEROUS)**

## 🛡️ **Safety Features**

### **1. Dangerous Operations Blocked**
These operations are **always blocked** for safety:
- `DROP TABLE` - Table deletion
- `ALTER TABLE` - Schema modification
- `CREATE TABLE` - New table creation
- `TRUNCATE` - Table truncation
- `VACUUM` - Database maintenance
- `REINDEX` - Index rebuilding

### **2. Table Restrictions**
If `allowed_tables` is configured, only those tables can be modified.

### **3. Query Validation**
All queries are validated before execution.

## 📋 **Supported Query Types**

### **✅ SELECT (Always Allowed)**
```sql
SELECT * FROM states WHERE entity_id = 'sensor.temperature'
SELECT COUNT(*) FROM statistics WHERE metadata_id = 375
```

### **✅ INSERT (When Enabled)**
```sql
INSERT INTO custom_table (name, value) VALUES ('test', 123)
INSERT INTO user_data (user_id, data) VALUES (1, '{"key": "value"}')
```

### **✅ UPDATE (When Enabled)**
```sql
UPDATE custom_table SET value = 456 WHERE name = 'test'
UPDATE user_data SET data = '{"updated": true}' WHERE user_id = 1
```

### **✅ DELETE (When Enabled)**
```sql
DELETE FROM custom_table WHERE name = 'test'
DELETE FROM user_data WHERE user_id = 1
```

## 🚀 **Usage Examples**

### **Example 1: Safe Configuration**
```json
{
  "allow_all_queries": true,
  "allowed_tables": ["custom_data", "user_preferences"]
}
```

**Allowed:**
```sql
INSERT INTO custom_data (key, value) VALUES ('test', 123)
UPDATE custom_data SET value = 456 WHERE key = 'test'
DELETE FROM custom_data WHERE key = 'test'
```

**Blocked:**
```sql
INSERT INTO states (entity_id, state) VALUES ('sensor.test', 'on')  -- states not in allowed_tables
DROP TABLE custom_data  -- DROP operations always blocked
```

### **Example 2: Dangerous Configuration (NOT RECOMMENDED)**
```json
{
  "allow_all_queries": true,
  "allowed_tables": []
}
```

**This allows modification of ALL Home Assistant tables including:**
- `states` - Current entity states
- `events` - Event history
- `statistics` - Long-term statistics
- `statistics_meta` - Statistics metadata

## 🧪 **Testing Examples**

### **Test 1: INSERT Query**
```json
{
  "method": "ferbos/query",
  "args": {
    "query": "INSERT INTO custom_table (name, value) VALUES ('test', 123)",
    "params": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "method": "ferbos/query",
  "result": {
    "query": "INSERT INTO custom_table (name, value) VALUES ('test', 123)",
    "params": [],
    "affected_rows": 1,
    "message": "Query executed successfully. 1 rows affected."
  }
}
```

### **Test 2: UPDATE Query**
```json
{
  "method": "ferbos/query",
  "args": {
    "query": "UPDATE custom_table SET value = 456 WHERE name = 'test'",
    "params": []
  }
}
```

### **Test 3: DELETE Query**
```json
{
  "method": "ferbos/query",
  "args": {
    "query": "DELETE FROM custom_table WHERE name = 'test'",
    "params": []
  }
}
```

## 🔒 **Security Best Practices**

### **1. Use Table Restrictions**
```json
{
  "allow_all_queries": true,
  "allowed_tables": ["safe_table1", "safe_table2"]
}
```

### **2. Create Backup Tables**
```sql
-- Create backup before modifications
CREATE TABLE states_backup AS SELECT * FROM states;
```

### **3. Use Transactions (if supported)**
```sql
BEGIN;
UPDATE table1 SET value = 123;
UPDATE table2 SET value = 456;
COMMIT;
```

### **4. Test on Development First**
- Test all queries on a development environment
- Verify results before using in production
- Keep backups of important data

## 🚨 **Emergency Recovery**

### **If You Accidentally Delete Data:**

1. **Stop the addon immediately**
2. **Restore from backup** (if available)
3. **Check Home Assistant logs** for errors
4. **Restart Home Assistant** if needed

### **Database Recovery Options:**
- Restore from Home Assistant backup
- Use SQLite recovery tools
- Restore from system backup

## 📊 **Monitoring and Logging**

### **Query Logging**
All queries are logged with:
- Query text
- Execution time
- Success/failure status
- User information

### **Monitor These Logs:**
- Addon logs in Home Assistant
- System logs for database errors
- Home Assistant logs for functionality issues

## 🎯 **Recommended Workflow**

### **1. Development Setup**
```json
{
  "allow_all_queries": true,
  "allowed_tables": ["test_table", "dev_data"]
}
```

### **2. Production Setup**
```json
{
  "allow_all_queries": false  // Only SELECT queries
}
```

### **3. Controlled Production**
```json
{
  "allow_all_queries": true,
  "allowed_tables": ["specific_safe_table"]
}
```

## ⚡ **Quick Start**

1. **Enable in config:**
   ```json
   {
     "allow_all_queries": true,
     "allowed_tables": ["your_safe_table"]
   }
   ```

2. **Restart addon**

3. **Test with INSERT:**
   ```json
   {
     "method": "ferbos/query",
     "args": {
       "query": "INSERT INTO your_safe_table (col1, col2) VALUES ('test', 123)",
       "params": []
     }
   }
   ```

4. **Verify results**

## 🆘 **Need Help?**

If you encounter issues:
1. Check addon logs
2. Verify table names exist
3. Check allowed_tables configuration
4. Test with SELECT queries first
5. Create backups before modifications

**Remember: With great power comes great responsibility!** 🕷️
