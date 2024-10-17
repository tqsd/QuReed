import argparse
import inspect
import os
import re
import sys

from jinja2 import Environment, FileSystemLoader

import qureed.gui.icons.icon_list
from qureed.signals import *


def camel_to_snake(name):
    # Insert an underscore before any capital letters (except the first one)
    # and convert all letters to lowercase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    snake_case = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return snake_case


def get_template_env():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    templates_path = os.path.join(dir_path, "templates")
    return Environment(loader=FileSystemLoader(templates_path))


def list_signals():
    signals = []
    for name, obj in inspect.getmembers(sys.modules["qureed.signals"]):
        if inspect.isclass(obj):  # Optionally, filter by some criteria
            signals.append(name)
    return signals


def list_icons():
    icons = [None]
    module = sys.modules["qureed.gui.icons.icon_list"]
    for name, obj in inspect.getmembers(module):
        print(name, obj)
        if isinstance(obj, str) and name.isupper():
            icons.append(name)
    return icons


def get_user_choice(options):
    for index, option in enumerate(options, start=1):
        print(f"{index}. {option}")
    choice = int(input("Select an option: "))
    while choice < 1 or choice > len(options):
        print("Invalid selection, please try again.")
        choice = int(input("Select an option: "))
    return options[choice - 1]


def main():
    parser = argparse.ArgumentParser(
        description="Create delist_signalsvice templates for qureed"
    )
    parser.add_argument("--path", help="Path to the device template", required=True)
    parser.add_argument("--name", help="New ClassName", required=True)
    args = parser.parse_args()
    normalized_path = args.path.rstrip("/")

    print(f"You have provided the path: {normalized_path}")
    if input("Is this path correct? (y/n): ").strip().lower() != "y":
        print("Operation cancelled.")
        return

    in_port_num = int(input("How many input ports does the device have?  "))
    out_port_num = int(input("How many output ports does the device have?  "))
    input_ports = {}
    output_ports = {}
    signal_types = list_signals()
    for i in range(in_port_num):
        label = input(f"Label of input port with index {i}: ")
        s_type = get_user_choice(signal_types)
        input_ports[label] = s_type

    for i in range(out_port_num):
        label = input(f"Label of output port with index {i}: ")
        s_type = get_user_choice(signal_types)
        output_ports[label] = s_type

    icons = list_icons()
    icon = get_user_choice(icons)

    env = get_template_env()
    template = env.get_template("device_template.jinja")
    output = template.render(
        name=args.name,
        input_ports=input_ports,
        output_ports=output_ports,
        gui_icon=icon,
    )
    print(output)
    if input("Save?(y/n): ").strip().lower() != "y":
        print("Operation cancelled.")
        return
    name = camel_to_snake(args.name)

    with open(f"{normalized_path}/{name}.py", "w") as f:
        f.write(output)


if __name__ == "__main__":
    main()
