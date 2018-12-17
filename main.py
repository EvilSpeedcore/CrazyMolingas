#  TODO: File should be in UTF-8 without BOM.
#  TODO: There is should be no blank lines in file.
import collections
import os, pathlib
import textwrap
import subprocess

from PIL import Image, ImageTk
from tkinter import (
    Tk, BOTH, Text, Button, END, filedialog, messagebox, NORMAL, DISABLED,
    Canvas, Checkbutton, IntVar, S, W, E, N
)
from tkinter.ttk import Frame, Label, Style

KB_PATH = r'D:\Python\CrazyMolingas\source.txt'
IMAGES_PATH = r'D:\Python\CrazyMolingas\images'
FORMULAS_PATH = r'D:\Python\CrazyMolingas\formulas'
PostCondition = collections.namedtuple('PostConditionImage', ['path', 'name'])


class PostconditionHandler:

    def __init__(self, path):
        self.path = path

    def gathered_conditions(self):
        with os.scandir(self.path) as directory:
            for child in directory:
                path = pathlib.Path(child.path)
                yield PostCondition(path, path.stem)

    def find_condition(self, filename):
        condition = [cond for cond in self.gathered_conditions() if cond.name == filename]
        return condition[0]


class Moling:

    def __init__(self, line):
        self.parts = [part.strip() for part in line.split(';')]
        self.identifier_codes = self._get_identifier_cores()
        self.postconditions = [self.postcondition]

    @property
    def identifier(self):
        return self.parts[0]

    @property
    def condition(self):
        return self.parts[1]

    @property
    def core(self):
        return self.parts[2]

    @property
    def dict_numbers(self):
        return self.parts[3]

    @property
    def confidence_factor(self):
        return self.parts[4]

    @property
    def postcondition(self):
        print(self.parts)
        return self.parts[5]

    @property
    def source(self):
        return self.identifier_codes[0]

    def chapter(self):
        return self.identifier_codes[1]

    def paragraph(self):
        return self.identifier_codes[2]

    @property
    def subparagraph(self):
        return self.identifier_codes[3]

    def indent(self):
        return self.identifier_codes[4]

    def number(self):
        return self.identifier_codes[5]

    def is_first(self):
        return self.number() == '1'

    def _get_identifier_cores(self):
        ids = self.identifier.split('.')
        return ids

    def __repr__(self):
        r = 'Moling({},{},{},{},{},{})'
        return r.format(self.identifier,
                        self.condition,
                        self.core,
                        self.dict_numbers,
                        self.confidence_factor,
                        self.postcondition)


class Blocks:

    def __init__(self, knowledge_base):
        self.molings = [Moling(entry) for entry in knowledge_base]
        self.blocks = self._create_blocks()
        self.assert_molings_have_valid_last_character()
        self.assert_identifier_cores_length()

    def __iter__(self):
        return iter(self.blocks)

    def _create_blocks(self):
        blocks, text_molings = [], []
        for moling in self.molings:
            if moling.postcondition:
                if text_molings:
                    blocks.append(text_molings)
                    text_molings = []
                duplicate = [e for e in blocks if not isinstance(e, list)
                             and e.identifier == moling.identifier]
                if duplicate:
                    duplicate[0].postconditions.append(moling.postcondition)
                else:
                    blocks.append(moling)
            else:
                text_molings.append(moling)

        if not blocks:
            blocks.append(text_molings)

        d = collections.deque()
        for block in blocks:
            if isinstance(block, list):
                d.append(TextBlock(block))
            else:
                d.append(PostconditionBlock(block))
        return d

    def rotate_right(self):
        row = self.blocks[0]
        self.blocks.rotate(1)
        return row

    def rotate_left(self):
        row = self.blocks[0]
        self.blocks.rotate(-1)
        return row

    def assert_molings_have_valid_last_character(self):
        for moling in self.molings:
            if not moling.core.endswith(('.', '...', '!', '?')):
                messagebox.showerror('Error', message='Invalid end of core: {}'.format(moling.core))

    def assert_identifier_cores_length(self):
        for moling in self.molings:
            ids = moling.identifier.split('.')
            if len(ids) != 6:
                messagebox.showerror('Error', message='Invalid identifier length: {}'.format(moling.identifier))


class PostconditionBlock:

    def __init__(self, moling):
        self.moling = moling
        self.postconditions = self.moling.postconditions

    def __repr__(self):
        return self.text

    @property
    def text(self):
        if self.moling.is_first():
            return textwrap.indent('\n{}'.format(self.moling.core), '    ')
        return textwrap.indent(self.moling.core, ' ')

    def image(self):
        return [pst for pst in self.postconditions if 'рис' in pst][0]

    def formula(self):
        return [pst for pst in self.postconditions if 'форм' in pst][0]


class TextBlock:

    def __init__(self, molings):
        self.molings = molings

    def __repr__(self):
        return self.text

    def is_same_sentence(self, index, moling):
        return [each for each in self.molings[:index] if each.identifier == moling.identifier]

    def _join_molings(self):
        formatted_molings = []
        for index, moling in enumerate(self.molings):
            text = moling.core
            if moling.is_first() and not self.is_same_sentence(index, moling):
                formatted_molings.append(textwrap.indent('\n{}'.format(text), '    '))
            elif moling.is_first() and self.is_same_sentence(index, moling):
                if moling.identifier == self.molings[index-1:index][0].identifier:
                    formatted_molings.append(text)
            else:
                formatted_molings.append(text)
        return ' '.join(formatted_molings)

    @property
    def text(self):
        return self._join_molings()

    @property
    def postcondition(self):
        return False

    @staticmethod
    def is_contains_image():
        return False

    @staticmethod
    def is_contains_formula():
        return False


def load_knowledge_base(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
    return lines


class MolingViewer(Frame):

    def __init__(self):
        super().__init__()
        self.blocks, self.image_handler, self.formulas_handler = (None, None, None)
        self.init_ui()

    def init_ui(self):
        self.master.title('MolingViewer')
        Style().configure('TFrame', background='#333')
        self.pack(fill=BOTH, expand=1)

        image = Image.open(r'C:\Users\ася\Desktop\6.jpg')
        image = ImageTk.PhotoImage(image)
        self.canvas = Canvas(self, height=696, width=550, highlightthickness=1, highlightbackground='black')
        self.canvas.grid(row=0, column=1, rowspan=10, columnspan=4, sticky=N+W)
        self.canvas.image = image
        self.canvas.create_image(0, 0, anchor='nw', image=image)

        self.displayed_text = Text(self, width=109, highlightthickness=1, highlightbackground='black', padx=1)
        self.displayed_text.grid(row=0, column=5, rowspan=6, columnspan=7, sticky=N+W)

        b = Button(self, text='Load base', height=1, width=12, command=self.load_kb)
        b.grid(row=6, column=5, sticky=S+W, padx=50)
        b = Button(self, text='Load images', height=1, width=12, command=self.load_images)
        b.grid(row=7, column=5, sticky=S+W, padx=50)
        b = Button(self, text='Load forms', height=1, width=12, command=self.load_formulas)
        b.grid(row=8, column=5, sticky=S+W, padx=50)

        b = Button(self, height=1, width=12, text='Forward', command=lambda: self.show_next_block(''))
        b.grid(row=6, column=11, sticky=S+E, padx=50)

        self.var = IntVar()
        c = Checkbutton(self, text='TEXT ONLY', variable=self.var, height=1, width=10)
        c.grid(row=7, column=11, sticky=S+E, padx=50)

    def show_next_block(self, event):
        try:
            block = self.blocks.rotate_left()
        except AttributeError:
            messagebox.showerror('Not so fast.', message='Load knowledge base first.')
        else:
            self.displayed_text.config(state=NORMAL)
            self.displayed_text.insert(END, block)
            self.displayed_text.see(END)
            self.displayed_text.config(state=DISABLED)
            if isinstance(block, TextBlock):
                self.canvas.delete("all")
            else:
                if not self.var.get():
                    if block.image():
                        pst = self.image_handler.find_condition(block.image())
                        image = Image.open(pst.path)
                        width, height = image.size
                        if width > 600 or height > 1650:
                            image = image.resize((500, 500), Image.ANTIALIAS)
                        image = ImageTk.PhotoImage(image)
                        self.canvas.image = image
                        self.canvas.create_image(0, 0, anchor='nw', image=image)
                        if block.formula():
                            pst = self.formulas_handler.find_condition(block.formula())
                            subprocess.Popen([str(pst.path)])

    def load_kb(self):
        kb_path = filedialog.askopenfile()
        if kb_path:
            kb = load_knowledge_base(kb_path.name)
            self.blocks = Blocks(kb)

    def load_images(self):
        image_directory = filedialog.askdirectory()
        self.image_handler = PostconditionHandler(image_directory)

    def load_formulas(self):
        formulas_directory = filedialog.askdirectory()
        self.formulas_handler = PostconditionHandler(formulas_directory)


def main():
    root = Tk()
    root.geometry("1650x700")
    app = MolingViewer()
    root.mainloop()


if __name__ == '__main__':
    main()