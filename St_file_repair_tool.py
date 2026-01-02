

import time


def start_crash_handler():
    print("St_file_repair_tool")
    time.sleep(1)
    print("Type \"start_repair\" to begin  or exit_repair_tool to exit the repair process.")
    INPUT = input("Command: ")
    if INPUT == "start_repair":
        print("fasza")
        time.sleep(1)
    elif INPUT == "exit_repair_tool":
        print("nem faszaság")
        time.sleep(1)
    

start_crash_handler()
