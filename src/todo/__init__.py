import sys
from .app import TodoApp


def get_command():
    if len(sys.argv) == 1:
        return None
    return sys.argv[1]


def usage():
    print("usage: todo [run|help]")


def main():
    cmd = get_command()
    if cmd is None or cmd == "run":
        TodoApp().run()
    else:
        usage()


if __name__ == "__main__":
    main()
