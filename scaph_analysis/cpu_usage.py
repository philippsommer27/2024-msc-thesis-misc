import psutil
import docker
import time
import csv
import signal
import sys

client = docker.from_env()

running = True

def get_total_cpu_usage():
    return psutil.cpu_percent(interval=None)

def get_container_cpu_usages():
    container_usages = []
    for container in client.containers.list():
        try:
            container_stats = container.stats(stream=False)
            if not container_stats or 'cpu_stats' not in container_stats or 'precpu_stats' not in container_stats:
                print(f"Invalid stats for container {container.name}. Skipping...")
                continue

            cpu_delta = container_stats["cpu_stats"]["cpu_usage"]["total_usage"] - container_stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_cpu_delta = container_stats["cpu_stats"]["system_cpu_usage"] - container_stats["precpu_stats"]["system_cpu_usage"]
            
            if system_cpu_delta > 0:
                cpu_usage = (cpu_delta / system_cpu_delta) * 100.0
            else:
                cpu_usage = 0.0
            container_usages.append((container.name, cpu_usage))
        except KeyError as e:
            print(f"KeyError: {e} for container {container.name}. Skipping...")
        except ZeroDivisionError:
            print(f"ZeroDivisionError for container {container.name}. Skipping...")
        except Exception as e:
            print(f"Unexpected error: {e} for container {container.name}. Skipping...")
    return container_usages

def record_cpu_usages(file_path, interval=0.5):
    with open(file_path, mode='w') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Total CPU Usage', 'Container Name', 'Container CPU Usage'])

        while running:
            start_time = time.time()
            timestamp = time.time()
            total_cpu_usage = get_total_cpu_usage()
            container_usages = get_container_cpu_usages()
            for container_name, container_cpu_usage in container_usages:
                writer.writerow([timestamp, total_cpu_usage, container_name, container_cpu_usage])
            file.flush() 

            elapsed_time = time.time() - start_time
            sleep_time = max(0, interval - elapsed_time)
            time.sleep(sleep_time)

def signal_handler(sig, frame):
    global running
    print('Stopping the script...')
    running = False

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print('Starting the script. Press Ctrl+C to stop.')
    try:
        record_cpu_usages('cpu_usages.csv', interval=0.5)
    except Exception as e:
        print(f"An error occurred: {e}")
    print('Script stopped.')