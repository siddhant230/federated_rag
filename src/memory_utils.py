# TODO : test os.pipe vs psutils
import os
# import psutil


def get_ram_usage():
    total_memory, used_memory, free_memory = map(
        int, os.popen('free -t -m').readlines()[-1].split()[1:])
    return {"free_memory": free_memory/1024,
            "used_memory": used_memory/1024,
            "total_memory": total_memory/1024,
            "percent_used_memory": round((used_memory/total_memory) * 100, 2)}


# print(psutil.virtual_memory().percent, psutil.cpu_percent())
# print(get_ram_usage())
