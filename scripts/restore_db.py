
import sys
import subprocess
import os

def restore_postgres(backup_file):
    """
    Restore Postgres database from a backup file.
    """
    if not os.path.exists(backup_file):
        print(f"Backup file not found: {backup_file}")
        sys.exit(1)
        
    container_name = "ai-agent-framework-postgres-1" 
    print(f"WARNING: This will overwrite the database in {container_name}.")
    confirm = input("Are you sure? (yes/no): ")
    if confirm.lower() != "yes":
        print("Restoration cancelled.")
        return

    print(f"Restoring from {backup_file}...")
    try:
        # cat file | docker exec -i container psql -U user -d db
        cmd = f"type {backup_file} | docker exec -i {container_name} psql -U user -d ai_agent_db"
        if os.name != 'nt': # Linux/Mac uses 'cat'
             cmd = f"cat {backup_file} | docker exec -i {container_name} psql -U user -d ai_agent_db"

        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Restore successful.")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Restore failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/restore_db.py <path_to_backup_file>")
        sys.exit(1)
    
    restore_postgres(sys.argv[1])
