
import os
import subprocess
import datetime

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_postgres():
    """
    Backup Postgres database running in Docker.
    Assumes container name contains 'postgres'.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{BACKUP_DIR}/db_backup_{timestamp}.sql"
    
    # Check for container
    # This command tries to find the actual container name running for the project
    # Fallback to 'ai-agent-framework-postgres-1' or similar guessed names if not using fixed names
    container_name = "ai-agent-framework-postgres-1" 
    
    print(f"Backing up database from {container_name} to {filename}...")
    
    try:
        # PGPASSWORD is expected inside the container or trusted auth for 'user'
        # Typically: docker exec -t container pg_dump -U user dbname > file
        cmd = f"docker exec -t {container_name} pg_dump -U user ai_agent_db > {filename}"
        
        # Note: 'user' and 'ai_agent_db' should match .env values. 
        # Ideally read from .env but keeping simple for script.
        
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Backup successful: {filename}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed: {e}")
        # Try finding container if name was wrong?
        print("Tip: Ensure docker container is running and name matches script.")

if __name__ == "__main__":
    backup_postgres()
