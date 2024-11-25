#!/usr/bin/env python3
import os
import glob
from datetime import datetime, timedelta

def cleanup_backups(backup_dir='backups', keep_days=7, keep_min=5):
    """
    Clean up old backup files while maintaining a minimum number of recent backups.
    
    Args:
        backup_dir (str): Directory containing backup files
        keep_days (int): Number of days to keep backups
        keep_min (int): Minimum number of backups to keep regardless of age
    """
    # Ensure backup directory exists
    if not os.path.exists(backup_dir):
        print(f"Backup directory {backup_dir} does not exist")
        return

    # Get all backup files
    backup_files = glob.glob(os.path.join(backup_dir, '*.db'))
    if not backup_files:
        print("No backup files found")
        return

    # Sort files by modification time
    backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    # Always keep the minimum number of backups
    if len(backup_files) <= keep_min:
        print(f"Only {len(backup_files)} backups exist, keeping all")
        return

    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=keep_days)

    # Process files
    for idx, file_path in enumerate(backup_files):
        # Always keep the minimum number of backups
        if idx < keep_min:
            continue

        # Check file age
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if mod_time < cutoff_date:
            try:
                os.remove(file_path)
                print(f"Removed old backup: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

if __name__ == '__main__':
    cleanup_backups()
