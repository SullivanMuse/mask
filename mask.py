#!/usr/bin/python3

import argparse
import copy
import datetime
import json
import os

MASK_FILE = os.path.expanduser("~/.mask")


def counter(start=0):
    def count():
        nonlocal start
        out = start
        start += 1
        return out

    return count


count = counter(1)


def exit_failure(message):
    code = count()

    def f():
        print(message)
        exit(code)

    return f


def exit_success():
    print("Success")
    exit(0)


exit_no_mask_file = exit_failure(f"{MASK_FILE} does not exist; run `mask init`")
exit_invalid_mask_file = exit_failure(
    f"{MASK_FILE} exists but is not valid; remove {MASK_FILE} and then run `mask init`"
)
exit_mask_already_exists = exit_failure(f"{MASK_FILE} already exists")
exit_user_abort = exit_failure("User chose to abort")


def init():
    try:
        with open(MASK_FILE, "r") as file:
            json.load(file)
        exit_mask_already_exists()
    except FileNotFoundError:
        with open(MASK_FILE, "x") as file:
            json.dump({"version": "0.0.1", "revs": [], "tasks": []}, file)
        exit_success()
    except json.JSONDecodeError:
        exit_invalid_mask_file()


def load():
    try:
        with open(MASK_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        exit_no_mask_file()
    except json.JSONDecodeError:
        exit_invalid_mask_file()


def write(data):
    content = json.dumps(data)
    with open(MASK_FILE, "w+") as file:
        file.write(content)


def add(args, data):
    # Create first rev
    rev = {
        "task": args.task,
        "after": args.after,
        "before": args.before,
        "due": datetime.datetime.fromisoformat(args.due).isoformat()
        if args.due is not None
        else None,
        # Metadata
        "created": datetime.datetime.now().isoformat(),
    }
    rev_id = len(data["revs"])
    data["revs"].append(rev)

    # Create task
    task = {
        "revs": [rev_id],
    }
    task_id = len(data["tasks"])
    data["tasks"].append(task)

    # Print task id for future reference
    print(task_id)


def edit(args, data):
    revs = data["revs"]
    task_rev_ids = data["tasks"][args.task_id]["revs"]

    # Create new rev
    prev_rev = revs[task_rev_ids[-1]]
    rev = copy.deepcopy(prev_rev)
    if args.name is not None:
        rev["name"] = args.name
    if args.after is not None:
        rev["after"].extend(args.after)
    if args.remove_after is not None:
        raise NotImplementedError
    if args.before is not None:
        rev["before"].extend(args.before)
    if args.remove_before is not None:
        raise NotImplementedError
    if args.due is not None:
        rev["due"] = datetime.datetime.fromisoformat(args.due).isoformat()
    if args.remove_due is not None:
        rev["due"] = None
    rev["created"] = datetime.datetime.now().isoformat()
    rev_id = len(data["revs"])
    revs.append(rev)

    # Append rev to task
    task_rev_ids.append(rev_id)


def ls(args, data):
    raise NotImplementedError


def rm(args, data):
    # Print tasks so the user knows what they are deleting
    for task_id in args.task_id:
        latest_rev_id = data["tasks"][task_id]["revs"][-1]
        latest_rev = data["revs"][latest_rev_id]
        print(latest_rev["name"])

    # Confirm
    user_input = input("Are you sure you want to delete these tasks? (y/N) ")
    if user_input.lower() != "y":
        exit_user_abort()

    # Clear all revs and clear the task
    for task_id in args.task_id:
        task = data["tasks"][task_id]
        task_rev_ids = task["revs"]
        for rev_id in task_rev_ids:
            data["revs"][rev_id].clear()
        task.clear()


def gc(args, data):
    raise NotImplementedError


def mark(args, data):
    raise NotImplementedError


def migrate(args, data):
    raise NotImplementedError


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="subparser")

    # mask init
    parser_init = subparsers.add_parser(name="init")

    # mask add
    parser_add = subparsers.add_parser(name="add")
    parser_add.add_argument("task")
    parser_add.add_argument("-a", "--after", nargs="*", action="extend", default=[])
    parser_add.add_argument("-b", "--before", nargs="*", action="extend", default=[])
    parser_add.add_argument("-d", "--due")

    # mask edit
    parser_edit = subparsers.add_parser(name="edit")
    parser_edit.add_argument("task_id")
    parser_edit.add_argument("-n", "--name")
    parser_edit.add_argument(
        "-a", "--add-after", nargs="*", action="extend", default=[]
    )
    parser_edit.add_argument(
        "-b", "--add-before", nargs="*", action="extend", default=[]
    )
    parser_edit.add_argument(
        "-A", "--remove-after", nargs="*", action="extend", default=[]
    )
    parser_edit.add_argument(
        "-B", "--remove-before", nargs="*", action="extend", default=[]
    )
    parser_edit.add_argument("-d", "--due")
    parser_edit.add_argument("-D", "--remove-due")

    # mask rm
    parser_rm = subparsers.add_parser(name="rm")
    parser_rm.add_argument("task_id", nargs="*")

    args = parser.parse_args()

    if args.verbose:
        print(args)

    if args.subparser == "init":
        init()
    else:
        # Select the appropriate function
        f = {
            "add": add,
            "edit": edit,
            "ls": ls,
            "gc": gc,
            "rm": rm,
            "migrate": migrate,
            "mark": mark,
        }[args.subparser]

        data = load()
        f(args, data)
        write(data)
