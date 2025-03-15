import json


class Store:
    def __init__(self, path):
        self.path = path
        self.load()

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"Columns": self.keys, "Todos": self.todos}, f)

    def load(self):
        with open(self.path) as f:
            data = json.load(f)
            self.keys = data["Columns"]
            self.todos = {}
            for key in self.keys:
                self.todos[key] = data["Todos"][key]

    def move_up(self, col, row):
        todos = self[col]
        if row == 0:
            return (col, row)
        todos[row], todos[row - 1] = (
            todos[row - 1],
            todos[row],
        )
        self.save()
        return (col, row - 1)

    def move_down(self, col, row):
        todos = self[col]
        if row == len(todos) - 1:
            return (col, row)
        todos[row], todos[row + 1] = (
            todos[row + 1],
            todos[row],
        )
        self.save()
        return (col, row + 1)

    def move_right(self, col, row):
        col_idx = col if isinstance(col, int) else self.keys.index(col)
        next_idx = min(col_idx + 1, len(self) - 1)
        if next_idx != col_idx:
            todo = self[col].pop(row)
            self[next_idx].append(todo)
            self.save()
            return (next_idx, len(self[next_idx]) - 1)
        return (next_idx, row)

    def move_left(self, col, row):
        col_idx = col if isinstance(col, int) else self.keys.index(col)
        next_idx = max(col_idx - 1, 0)
        if next_idx != col_idx:
            todo = self[col].pop(row)
            self[next_idx].append(todo)
            self.save()
            return (next_idx, len(self[next_idx]) - 1)
        return (next_idx, row)

    def remove(self, col, row):
        self[col].pop(row)
        self.save()

    def insert(self, col, row, todo):
        self[col].insert(row, todo)
        self.save()

    def append(self, col, row, todo):
        self[col].insert(row + 1, todo)
        self.save()

    def items(self):
        return self.todos.items()

    def __getitem__(self, i):
        if isinstance(i, tuple):
            col, row = i
        else:
            col, row = i, None
        key = self.keys[col] if isinstance(col, int) else col
        if row is None:
            return self.todos[key]
        return self.todos[key][row]

    def __setitem__(self, i, todo):
        if isinstance(i, tuple):
            col, row = i
        else:
            col, row = i, None
        key = self.keys[col] if isinstance(col, int) else col

        if row is None:
            self[key] = [todo]
        else:
            self[key][row] = todo

        self.save()

    def __iter__(self):
        return self.todos

    def __len__(self):
        return len(self.todos)
