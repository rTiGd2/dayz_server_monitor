# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import logging
import os

# Master list to collect all messages (for Discord and file output)
output_messages = []

def send_output(config, message):
    if config['output'].get("to_console", True):
        print(message)

    output_messages.append(message)

    # Write to file live
    if config['output'].get("to_file", True):
        file_path = config['output'].get("file_path", "output/last_run.txt")
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            logging.error(f"Failed to write to output file: {e}")

def get_all_output():
    return "\n".join(output_messages)