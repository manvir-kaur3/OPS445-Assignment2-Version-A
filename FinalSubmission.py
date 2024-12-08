#!/usr/bin/env python3

'''
OPS445 Assignment 2
Program: assignment2.py 
Author: "Manvir Kaur"
Semester: "Fall 2024"

The python code in this file is original work written by
"Yuvraj Dhiman". No code in this file is copied from any other source 
except those provided by the course instructor, including any person, 
textbook, or on-line resource. I have not shared this python script 
with anyone or anything except for submission for grading.  
I understand that the Academic Honesty Policy will be enforced and 
violators will be reported and appropriate action will be taken.

Description: A program to visualize memory usage and provide information 
about memory consumed by processes.
'''

import argparse
import os
import sys

def parse_command_args() -> object:
    """
    Set up argparse for command-line argument parsing.
    """
    parser = argparse.ArgumentParser(description="Memory Visualiser -- See Memory Usage Report with bar charts",
                                     epilog="Copyright 2023")
    parser.add_argument("-l", "--length", type=int, default=20,
                        help="Specify the length of the graph. Default is 20.")
    parser.add_argument("-H", "--human-readable", action="store_true",
                        help="Prints sizes in human-readable format.")
    parser.add_argument("program", type=str, nargs='?',
                        help="If a program is specified, show memory use of all associated processes.")
    args = parser.parse_args()
    return args

def percent_to_graph(percent: float, length: int = 20) -> str:
    """
    Convert a percentage into a bar graph string.
    :param percent: float, percentage value between 0.0 and 1.0
    :param length: int, length of the bar graph
    :return: str, bar graph representation (without brackets)
    """
    filled_length = int(round(percent * length))
    return f"{'#' * filled_length}{' ' * (length - filled_length)}"


def get_sys_mem() -> int:
    """
    Return total system memory (in kB) by reading /proc/meminfo.
    """
    try:
        with open("/proc/meminfo", "r") as meminfo:
            for line in meminfo:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1])
    except FileNotFoundError:
        print("Error: /proc/meminfo not found.")
        sys.exit(1)
    return 0

def get_avail_mem() -> int:
    """
    Return available system memory (in kB) by reading /proc/meminfo.
    Handles WSL cases where 'MemAvailable' may not exist.
    """
    try:
        with open("/proc/meminfo", "r") as meminfo:
            mem_free = 0
            swap_free = 0
            for line in meminfo:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1])
                if line.startswith("MemFree:"):
                    mem_free = int(line.split()[1])
                if line.startswith("SwapFree:"):
                    swap_free = int(line.split()[1])
            return mem_free + swap_free
    except FileNotFoundError:
        print("Error: /proc/meminfo not found.")
        sys.exit(1)
    return 0

def pids_of_prog(app_name: str) -> list:
    """
    Given an app name, return all PIDs associated with the app.
    """
    try:
        pids = os.popen(f"pidof {app_name}").read().strip().split()
        return pids if pids else []
    except Exception:
        return []

def rss_mem_of_pid(proc_id: str) -> int:
    """
    Given a process ID, return the resident memory used (in kB), zero if not found.
    """
    try:
        rss_total = 0
        with open(f"/proc/{proc_id}/smaps", "r") as smaps:
            for line in smaps:
                if line.lstrip().startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        rss_value = int(parts[1])
                        rss_total += rss_value
        return rss_total
    except FileNotFoundError:
        print(f"FileNotFoundError: /proc/{proc_id}/smaps not found.")
        return 0
    except Exception as e:
        print(f"Exception while reading /proc/{proc_id}/smaps: {e}")
        return 0


def bytes_to_human_r(kibibytes: int, decimal_places: int = 2) -> str:
    """
    Convert kibibytes to a human-readable format.
    :param kibibytes: int, size in KiB
    :param decimal_places: int, number of decimal places
    :return: str, human-readable string
    """
    suffixes = ['KiB', 'MiB', 'GiB', 'TiB']
    suf_count = 0
    result = kibibytes
    while result >= 1024 and suf_count < len(suffixes) - 1:
        result /= 1024
        suf_count += 1
    return f"{result:.{decimal_places}f} {suffixes[suf_count]}"

if __name__ == "__main__":
    args = parse_command_args()

    if not args.program:
        # Total memory and usage calculation
        total_memory = get_sys_mem()
        available_memory = get_avail_mem()
        used_memory = total_memory - available_memory
        percent_used = used_memory / total_memory

        # Format memory output
        if args.human_readable:
            total_memory_str = bytes_to_human_r(total_memory)
            used_memory_str = bytes_to_human_r(used_memory)
        else:
            total_memory_str = f"{total_memory} kB"
            used_memory_str = f"{used_memory} kB"

        # Display the bar graph
        graph = percent_to_graph(percent_used, args.length)
        print(f"Memory         {graph} {percent_used * 100:.0f}% {used_memory_str}/{total_memory_str}")

    else:
        # Per-process memory usage for a specific program
        pids = pids_of_prog(args.program)
        if not pids:
            print(f"{args.program} not found.")
            sys.exit(1)

        total_rss = 0
        process_mem_info = []

        for pid in pids:
            rss = rss_mem_of_pid(pid)
            total_rss += rss
            process_mem_info.append((pid, rss))

        # Format memory output
        if args.human_readable:
            total_memory_str = bytes_to_human_r(get_sys_mem())
            process_mem_info = [(pid, bytes_to_human_r(rss)) for pid, rss in process_mem_info]
        else:
            total_memory_str = f"{get_sys_mem()} kB"
            process_mem_info = [(pid, f"{rss} kB") for pid, rss in process_mem_info]

        # Display individual processes
        for pid, rss in process_mem_info:
            rss_value = int(float(rss.split()[0])) if isinstance(rss, str) else rss
            percent_used = rss_value / get_sys_mem()
            graph = percent_to_graph(percent_used, args.length)
            print(f"{pid:10} {graph} {rss}/{total_memory_str}")

        # Display total for the program
        percent_used = total_rss / get_sys_mem()
        graph = percent_to_graph(percent_used, args.length)
        total_rss_str = bytes_to_human_r(total_rss) if args.human_readable else f"{total_rss} kB"
        print(f"{args.program:10} {graph} {total_rss_str}/{total_memory_str}")
