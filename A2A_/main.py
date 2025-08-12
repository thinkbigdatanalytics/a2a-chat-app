import subprocess
import time

def start_postgres_mcp_server():
    command = [
        "docker",
        "run",
        "-i",
        "--rm",
        "-p", "5432:5432",
        "--name", "mcp_postgres_test",
        "-e", "POSTGRES_USER=postgres",
        "-e", "POSTGRES_PASSWORD=postgres",
        "-e", "POSTGRES_DB=sample_db",
        "postgres"  # or your "mcp/postgres" image if it's correct
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(10)

    return process

def stop_postgres_mcp_server(process):
    process.terminate()
    process.wait()
