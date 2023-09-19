import argparse
import copy
import datetime
import json
import os

TASKS_FILE = os.path.expanduser("~/.tasks")

def init(args):
    if os.path.isfile(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            print(".tasks already exists, but is not valid; move or remove it before runnin `tasks init`")
            exit(1)
        print(".tasks already exists")
        exit(1)
    else:
        with open(TASKS_FILE, "x") as file:
            json.dump({"version": "0.0.1", "revs": [], "tasks": []}, file)
        print("created .tasks")

def add(args):
    with open(TASKS_FILE, "r") as file:
        data = json.load(file)

    # Create first rev
    rev = {
        "task": args.task,
        "after": args.after,
        "before": args.before,
        "due": datetime.datetime.fromisoformat(args.due).isoformat() if args.due is not None else None,

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
    print(task_id)

    content = json.dumps(data)
    with open(TASKS_FILE, "w") as file:
        file.write(content)

def edit(args):
    with open(TASKS_FILE, "r") as file:
        data = json.load(file)
    
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

    content = json.dumps(data)
    with open(TASKS_FILE, "w") as file:
        file.write(content)

def ls(args):
    raise NotImplementedError

def rm(args):
    # Confirm
    user_input = input("Are you sure? (y/N) ")
    if user_input.lower() != "y":
        print("Aborting.")
        exit(0)

    # Load the data
    with open(TASKS_FILE, "r") as file:
        data = json.load(file)

    # Clear all revs and clear the task
    for task_id in args.task_id:
        task = data["tasks"][task_id]
        task_rev_ids = task["revs"]
        for rev_id in task_rev_ids:
            data["revs"][rev_id].clear()
        task.clear()

    # Write to disk
    content = json.dumps(data)
    with open(TASKS_FILE, "w") as file:
        file.write(content)

def gc(args):
    raise NotImplementedError

def mark(args):
    raise NotImplementedError

def migrate(args):
    raise NotImplementedError

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subparser")
    parser_init = subparsers.add_parser(name="init")

    parser_add = subparsers.add_parser(name="add")
    parser_add.add_argument("task")
    parser_add.add_argument("-a", "--after", nargs="*", action="extend", default=[])
    parser_add.add_argument("-b", "--before", nargs="*", action="extend", default=[])
    parser_add.add_argument("-d", "--due")

    parser_edit = subparsers.add_parser(name="edit")
    parser_edit.add_argument("task_id")
    parser_edit.add_argument("-n", "--name")
    parser_edit.add_argument("-a", "--add-after", nargs="*", action="extend", default=[])
    parser_edit.add_argument("-b", "--add-before", nargs="*", action="extend", default=[])
    parser_edit.add_argument("-A", "--remove-after", nargs="*", action="extend", default=[])
    parser_edit.add_argument("-B", "--remove-before", nargs="*", action="extend", default=[])
    parser_edit.add_argument("-d", "--due")
    parser_edit.add_argument("-D", "--remove-due")

    parser_rm = subparsers.add_parser(name="rm")
    parser_rm.add_argument("task_id", nargs="*")

    args = parser.parse_args()

    print(args)

    {
        "init": init,
        "add": add,
        "edit": edit,
        "ls": ls,
        "gc": gc,
        "rm": rm,
        "migrate": migrate,
        "mark": mark,
        None: hlp,
    }[args.subparser](args)
