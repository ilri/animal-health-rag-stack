-- Apply ILRI tuning for a machine with 64GB RAM and 8 CPUs
-- These will be written to postgresql.auto.conf

ALTER SYSTEM SET log_rotation_size = '1GB';
ALTER SYSTEM SET log_min_duration_statement = 250; -- ms
ALTER SYSTEM SET log_checkpoints = 'on';
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
ALTER SYSTEM SET log_lock_waits = 'on';
ALTER SYSTEM SET log_temp_files = 0; -- log all temp files

ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET work_mem = '512MB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET effective_cache_size = '4GB';
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET checkpoint_timeout = '10min';
ALTER SYSTEM SET effective_io_concurrency = 100;

-- Reload config to pick up parameters that are reloadable during init
SELECT pg_reload_conf(); 