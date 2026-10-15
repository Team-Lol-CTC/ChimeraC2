import os
import socket
import platform
import getpass
import psutil


def is_elevated():
    try:
        if hasattr(os, "getuid"):
            return os.getuid() == 0

        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_internal_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()

    return ip


def collect_system_survey():
    try:
        mem = psutil.virtual_memory()
        total_ram = round(mem.total / (1024 ** 3), 2)
        avail_ram = round(mem.available / (1024 ** 3), 2)
    except Exception:
        total_ram = 0.0
        avail_ram = 0.0

    processes = []
    try:
        for p in psutil.process_iter(["pid", "name"]):
            processes.append(p.info)
            if len(processes) >= 10:
                break
    except Exception:
        processes = []

    user = getpass.getuser()
    ip = get_internal_ip()

    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "user": user,
        "current_user": user,
        "is_privileged": is_elevated(),
        "ip": ip,
        "internal_ip": ip,
        "cpu_cores": os.cpu_count() or 1,
        "total_ram_gb": total_ram,
        "available_ram_gb": avail_ram,
        "sample_processes": processes,
    }


if __name__ == "__main__":
    import json

    print("[*] Running standalone host triage survey...")
    survey = collect_system_survey()
    print(json.dumps(survey, indent=2))
    print("[+] Survey collection successful!")
