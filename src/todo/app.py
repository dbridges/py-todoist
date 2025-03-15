import os
from collections import namedtuple

from rich.style import Style
from textual import events, on
from textual.app import App
from textual.screen import ModalScreen
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual.widgets import Button, Static, TextArea
from textual.widgets.text_area import TextAreaTheme
from textual.reactive import reactive
from textual.theme import Theme

from .store import Store

TodoFormResult = namedtuple("TodoFormResult", "todo action")

todoist_theme = Theme(
    name="todoist",
    primary="#d1ecff",
    secondary="#fffed3",
    accent="#9c815f",
    foreground="#444444",
    background="#ffffff",
    success="#A3BE8C",
    warning="#EBCB8B",
    error="#BF616A",
    surface="#ffffff",
    panel="#ffffff",
    dark=False,
    variables={
        "block-cursor-text-style": "none",
        "input-selection-background": "#d1ecff",
    },
)

text_area_theme = TextAreaTheme(
    name="todoist_text_area",
    cursor_line_style=Style(bgcolor="#ffffff"),
)


def build_classes(*items) -> str:
    classes = [item for item in items if item]
    return " ".join(classes)


class TodoModal(ModalScreen):
    def __init__(self, todo=None, action="insert"):
        super().__init__()
        self.action = action if todo is None else "update"
        self.todo = todo or ""

    def on_mount(self):
        self.text_area.register_theme(text_area_theme)
        self.text_area.theme = "todoist_text_area"
        self.text_area.cursor_location = self.text_area.document.end
        self.set_focus(self.text_area)

    def compose(self):
        self.text_area = TextArea(text=self.todo)
        with Container(classes="modal-content"):
            yield Static("⚈", classes="header")
            with Vertical(classes="content"):
                yield self.text_area
                with Horizontal():
                    yield Static(classes="spacer")
                    yield Button("Save", id="todo-save-button")

    def on_key(self, event: events.Key):
        if event.key == "escape":
            event.stop()
            self.action_cancel()

    def action_cancel(self):
        self.dismiss(None)

    @on(Button.Pressed, "#todo-save-button")
    def save_todo(self):
        todo = self.text_area.text
        self.text_area.text = ""
        self.dismiss(TodoFormResult(todo=todo, action=self.action))


class Card(Container):
    def __init__(self, content):
        super().__init__()
        self.content = content

    def select(self):
        self.add_class("selected")
        self.scroll_visible()

    def compose(self):
        yield Static("⚈", classes="header")
        yield Static(self.content, classes="content")


class Column(Vertical):
    def __init__(self, label, todos):
        super().__init__(classes="column", id=f"col-{label}")
        self.label = label
        self.todos = todos

    def compose(self):
        yield Static(self.label, classes="header")
        with VerticalScroll(classes="content"):
            for todo in self.todos:
                yield Card(todo)

    async def update(self, todos):
        self.todos = todos
        await self.recompose()

    def select(self, row):
        if row == -1:
            self.query_exactly_one("Column > .header").add_class("selected")
            return
        for n, widget in enumerate(self.query(f"Card")):
            if n == row and (isinstance(widget, Card)):
                widget.select()
                return


class TodoApp(App):
    CSS_PATH = "app.css"
    BINDINGS = [("q", "quit()", "Quit")]

    selection = reactive(None)

    def __init__(self):
        super().__init__()
        self.store = Store(os.path.expanduser("~/.todoist/todos.json"))

    def on_mount(self):
        self.register_theme(todoist_theme)
        self.theme = "todoist"

    def _refresh_selection(self):
        for widget in self.query(".selected"):
            widget.remove_class("selected")
        col = self.selected_column()
        if col is not None and self.selection is not None:
            col.select(self.selection[1])

    def select(self, col, row):
        items = self.store[col]

        if len(items) == 0:
            self.selection = (col, -1)
        elif row < 0:
            self.selection = (col, 0)
        else:
            self.selection = (col, min(row, len(items) - 1))

        self._refresh_selection()

    def clear_selection(self):
        self.selection = None
        self._refresh_selection()

    async def on_key(self, event: events.Key):
        if event.key == "l":
            if self.selection is None:
                self.select(0, 0)
            else:
                self.select(
                    (self.selection[0] + 1) % len(self.store), self.selection[1]
                )
        elif event.key == "h":
            if self.selection is None:
                self.select(0, 0)
            else:
                self.select(
                    (self.selection[0] - 1) % len(self.store), self.selection[1]
                )
        elif event.key == "j":
            if self.selection is None:
                self.select(0, 0)
            else:
                self.select(self.selection[0], self.selection[1] + 1)
        elif event.key == "k":
            if self.selection is None:
                self.select(0, 0)
            else:
                self.select(self.selection[0], self.selection[1] - 1)
        elif event.key == "escape":
            self.clear_selection()
        elif event.key == "J":
            if self.selection is not None:
                next_selection = self.store.move_down(*self.selection)
                if next_selection == self.selection:
                    return
                await self.refresh_lists()
                self.select(*next_selection)
        elif event.key == "K":
            if self.selection is not None:
                next_selection = self.store.move_up(*self.selection)
                if next_selection == self.selection:
                    return
                await self.refresh_lists()
                self.select(*next_selection)
        elif event.key == "L":
            if self.selection is not None:
                next_selection = self.store.move_right(*self.selection)
                if next_selection == self.selection:
                    return
                await self.refresh_lists()
                self.select(*next_selection)
        elif event.key == "H":
            if self.selection is not None:
                next_selection = self.store.move_left(*self.selection)
                if next_selection == self.selection:
                    return
                await self.refresh_lists()
                self.select(*next_selection)
        elif event.key == "ctrl+d":
            if self.selection is not None and self.selection[1] >= 0:
                self.store.remove(*self.selection)
                next_selection = (self.selection[0], max(self.selection[1] - 1, -1))
                await self.refresh_lists()
                self.select(*next_selection)
        elif event.key == "e":
            if self.selection is not None:
                self.push_screen(
                    TodoModal(self.store[self.selection]), self.on_todo_form
                )
        elif event.key == "i":
            if self.selection is not None:
                self.push_screen(TodoModal(action="insert"), self.on_todo_form)
        elif event.key == "a":
            if self.selection is not None:
                self.push_screen(TodoModal(action="append"), self.on_todo_form)
        elif event.key == "R":
            self.store.load()
            await self.refresh_lists()
            self.clear_selection()

    async def on_todo_form(self, info):
        if info is None or self.selection is None:
            return
        todo, action = info
        if action == "update":
            self.store[self.selection] = todo
            await self.refresh_lists()
            self.select(*self.selection)
        elif action == "insert":
            self.store.insert(self.selection[0], self.selection[1], todo)
            await self.refresh_lists()
            self.select(*self.selection)
        elif action == "append":
            self.store.append(self.selection[0], self.selection[1], todo)
            await self.refresh_lists()
            self.select(self.selection[0], self.selection[1] + 1)

    async def refresh_lists(self):
        for label in self.store.keys:
            col = self.find_column(label)
            await col.update(self.store[label])

    def find_column(self, label):
        col = self.query_exactly_one(f"#col-{label}")
        assert isinstance(col, Column)
        return col

    def selected_column(self, selection=None):
        if selection is None:
            selection = self.selection
        if selection is None:
            return None
        label = self.store.keys[selection[0]]
        return self.find_column(label)

    def compose(self):
        for label, todos in self.store.items():
            yield Column(label=label, todos=todos)
