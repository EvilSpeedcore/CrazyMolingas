import collections
import os, pathlib
import textwrap
import subprocess

from PIL import Image, ImageTk
from tkinter import Tk, BOTH, Text, Button, END, filedialog, messagebox
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

    @property
    def identifier(self):
        return self.parts[0]

    @property
    def condition(self):
        return self.parts[1]

    @property
    def core(self):
        c = self.parts[2]
        if c[-1] not in ('.', '...', '?', '!'):
            raise Exception('No period in the end of sentence in "{}"'.format(c))
        return c

    @property
    def dict_numbers(self):
        return self.parts[3]

    @property
    def confidence_factor(self):
        return self.parts[4]

    @property
    def postcondition(self):
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
        if len(ids) != 6:
            raise Exception('Invalid identifier: {}'.format(self))
        else:
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

    def __iter__(self):
        return iter(self.blocks)

    def _create_blocks(self):
        blocks, text_molings = [], []
        for moling in self.molings:
            if moling.postcondition:
                if text_molings:
                    blocks.append(text_molings)
                    text_molings = []
                #  Check if moling with same identifier already collected (рис, форм) -> add second postcondition.
                blocks.append([moling])
            else:
                text_molings.append(moling)

        d = collections.deque()
        for block in blocks:
            if len(block) == 1:
                d.append(PostconditionBlock(block[0]))
            else:
                d.append(TextBlock(block))
        return d

    def rotate_right(self):
        row = self.blocks[0]
        self.blocks.rotate(1)
        return row

    def rotate_left(self):
        row = self.blocks[0]
        self.blocks.rotate(-1)
        return row


class PostconditionBlock:

    def __init__(self, moling):
        self.moling = moling
        self.postcondition = self.moling.postcondition

    def __repr__(self):
        return self.text

    @property
    def text(self):
        if self.moling.is_first():
            return textwrap.indent('\n{}'.format(self.moling.core), '    ')
        return textwrap.indent(self.moling.core, ' ')

    def is_contains_image(self):
        return 'рис' in self.moling.postcondition

    def is_contains_formula(self):
        return 'форм' in self.moling.postcondition


class TextBlock:

    def __init__(self, molings):
        self.molings = molings

    def __repr__(self):
        return self.text

    def _join_molings(self):
        formatted_molings = []
        for index, moling in enumerate(self.molings):
            text = moling.core
            if moling.is_first():
                formatted_molings.append(textwrap.indent('\n{}'.format(text), '    '))
            elif moling.is_first() and self.molings.index(moling) != 0:
                if moling.identifier == self.molings[index-1:0].identifier:
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


class Example(Frame):

    def __init__(self):
        super().__init__()
        self.blocks, self.image_handler, self.formulas_handler = (None, None, None)
        self.init_ui()

    def init_ui(self):
        self.master.title('MolingViewer')
        self.pack(fill=BOTH, expand=1)

        Style().configure('TFrame', background='#333')

        self.image_label = Label(self)
        self.image_label.place(x=0, y=0)
        self.displayed_text = Text(height=25, width=105)
        self.displayed_text.place(x=568, y=7)
        button_forward = Button(self, height=1, width=12, text='Forward', command=self.show_next_block)
        button_forward.place(x=570, y=540)
        load_kb_button = Button(self, height=1, width=12, text='Load KB', command=self.load_kb)
        load_kb_button.place(x=695, y=540)
        load_images_button = Button(self, height=1, width=12, text='Load images', command=self.load_images)
        load_images_button.place(x=820, y=540)
        load_formulas_button = Button(self, height=1, width=12, text='Load formulas', command=self.load_formulas)
        load_formulas_button.place(x=945, y=540)

    def show_next_block(self):
        try:
            block = self.blocks.rotate_left()
        except AttributeError:
            messagebox.showerror('Not so fast.', message='Load knowledge base first.')
        else:
            if isinstance(block, TextBlock):
                self.image_label.config(image='')
            elif block.is_contains_image():
                pst = self.image_handler.find_condition(block.postcondition)
                image = Image.open(pst.path)
                image = ImageTk.PhotoImage(image)
                self.image_label.configure(image=image)
                self.image_label.image = image
            elif block.is_contains_formula():
                pst = self.formulas_handler.find_condition(block.postcondition)
                subprocess.call(str(pst.path))
            self.displayed_text.insert(END, block)
            self.displayed_text.see(END)

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
    app = Example()
    root.mainloop()


if __name__ == '__main__':
    main()