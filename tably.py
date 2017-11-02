#!/usr/bin/env python3

import argparse
import csv


PREAMBLE = r"""\documentclass[11pt, a4paper]{article}
\usepackage{booktabs}
\begin{document}"""

HEADER = r"""\begin{{table}}[htb]
{indent}\centering{label}{caption}
{indent}\begin{{tabular}}{{@{{}}{align}@{{}}}}
{indent}{indent}\toprule"""

FOOTER = r"""{indent}{indent}\bottomrule
{indent}\end{{tabular}}
\end{{table}}"""

LABEL = '\n{indent}\\label{{{label}}}'
CAPTION = '\n{indent}\\caption{{{caption}}}'


class Tably:
    """Object which holds parsed arguments.

    Methods:
        run: creates a LaTeX code/file
        create_table: for each specified file, creates a LaTeX table
    """

    def __init__(self, args):
        """
        Attributes:
            files (string): name(s) of the .csv file(s)
            align (string): wanted alignment of the columns
            caption (string): the name of the table, printed above it
            indent (bool): should a LaTeX code be indented with 4 spaces per
                code block. Doesn't affect the final looks of the table.
            label (string): a label by which the table can be referenced
            no_header (bool): if the .csv contains only content, without a
                header (names for the columns)
            outfile (string): name of the file where to save the results.
            preamble(bool): create a preamble
            sep (string): column separator
            skip (int): number of rows in .csv to skip
            units (list): units for each column
        """
        self.files = args.files
        self.no_header = args.no_header
        self.label = args.label
        self.caption = args.caption
        self.align = args.align
        self.no_indent = args.no_indent
        self.outfile = args.outfile
        self.skip = args.skip
        self.preamble = args.preamble
        self.sep = get_sep(args.sep)
        self.units = args.units

    def run(self):
        """The main method.

        For each file in `files`, calls `create_table` method.
        If `outfile` is provided, calls `save_content` function,
        otherwise prints to the console.
        """
        all_tables = []
        if self.label and len(self.files) > 1:
            all_tables.append("% don't forget to manually re-label the tables")
        for file in self.files:
            table = self.create_table(file)
            if table:
                all_tables.append(table)
        if not all_tables:
            return

        if self.preamble:
            all_tables.insert(0, PREAMBLE)
            all_tables.append(r'\end{document}')
        else:
            all_tables.insert(0, '\n% \\usepackage{booktabs} % move this to '
                                 'preamble and uncomment')

        final_content = '\n\n'.join(all_tables)
        if self.outfile:
            try:
                save_content(final_content, self.outfile)
            except FileNotFoundError:
                print('{} is not a valid/known path. Could not save there.'.format(self.outfile))
        else:
            print(final_content)

    def create_table(self, file):
        """Creates a table from a given .csv file.

        The method `run` calls this method.
        """
        rows = []
        indent = 4*' ' if not self.no_indent else ''

        try:
            with open(file) as infile:
                for i, columns in enumerate(csv.reader(infile, delimiter=self.sep)):
                    if i < self.skip:
                        continue
                    rows.append(create_row(columns, indent))
        except FileNotFoundError:
            print("File {} doesn't exist!!\n".format(file))
            return ''
        if not rows:
            print("No table created from the {} file. Check if the file is empty "
                  "or you used too high skip value.\n".format(file))
            return ''

        if not self.no_header:
            rows.insert(1, r'{0}{0}\midrule'.format(indent))
            if self.units:
                rows[0] = rows[0] + r'\relax' # fixes problem with \[
                units = get_units(self.units)
                rows.insert(1, r'{0}{0}{1} \\'.format(indent, units))

        header = HEADER.format(
            label=add_label(self.label, indent),
            caption=add_caption(self.caption, indent),
            align=format_alignment(self.align, len(columns)),
            indent=indent,
        )
        content = '\n'.join(rows)
        footer = FOOTER.format(indent=indent)
        return '\n'.join((header, content, footer))


def get_sep(sep):
    if sep.lower() in ['t', 'tab', '\\t']:
        return '\t'
    elif sep.lower() in ['s', 'semi', ';']:
        return ';'
    elif sep.lower() in ['c', 'comma', ',']:
        return ','
    else:
        return sep


def format_alignment(align, length):
    """Makes sure that provided alignment is valid:
    1. the length of alignment is either 1 or the same as the number of columns
    2. valid characters are `l`, `c` and `r`

    If there is an invalid character, all columns are set to centered alignment.
    If alignment length is too long, it is stripped to fit the number of columns.
    If alignment length is too short, it is padded with `c` for the missing
    columns.
    """
    if any(ch not in 'lcr' for ch in align):
        align = 'c'

    if len(align) == 1:
        return length * align
    elif len(align) == length:
        return align
    else:
        return '{:c<{l}.{l}}'.format(align, l=length)


def get_units(units):
    formatted_units = []
    for unit in escaped(units):
        if unit in '-/0':
            formatted_units.append('')
        else:
            formatted_units.append('[{}]'.format(unit))
    return ' & '.join(formatted_units)


def add_label(label, indent):
    """Creates a table label"""
    return LABEL.format(label=label, indent=indent) if label else ''


def add_caption(caption, indent):
    """Creates a table caption"""
    return CAPTION.format(caption=caption, indent=indent) if caption else ''


def escaped(line):
    """Escapes special LaTeX characters by prefixing them with backslash"""
    for char in '#$%&_}{':
        line = [column.replace(char, '\\'+char) for column in line]
    return line


def create_row(line, indent):
    """Creates a row based on `line` content"""
    return r'{indent}{indent}{content} \\'.format(
              indent=indent,
              content=' & '.join(escaped(line)))


def save_content(content, outfile):
    """Saves the content to a file.

    If the existing file is provided, the content is appended to the end
    of the file.
    """
    with open(outfile, 'a') as out:
        out.writelines(content)
    print('The content is added to', outfile)


def arg_parser():
    """Parses command line arguments and provides --help"""
    parser = argparse.ArgumentParser(description="Creates LaTeX tables from .csv files")

    parser.add_argument(
        'files',
        nargs='+',
        help='.csv file(s) containing the data you want to export.'
    )
    parser.add_argument(
        '-a', '--align',
        default='c',
        help='Alignment for the columns of the table. '
             'Use `l`, `c`, and `r` for left, center and right. '
             'Either one character for all columns, or one character per column. '
             'Default: c'
    )
    parser.add_argument(
        '-c', '--caption',
        help='Caption of the table. '
             'Default: None'
    )
    parser.add_argument(
        '-i', '--no-indent',
        action='store_true',
        help='Pass this if you do not want to indent LaTeX source code '
             'with 4 spaces per float. No difference in the final result (pdf). '
             'Default: False'
    )
    parser.add_argument(
        '-k', '--skip',
        type=int,
        default=0,
        help='Number of rows in .csv to skip. Default: 0'
    )
    parser.add_argument(
        '-l', '--label',
        help='Label of the table, for referencing it. Default: None'
    )
    parser.add_argument(
        '-n', '--no-header',
        action='store_true',
        help='By default, the first row of .csv is used as a table header. '
             'Pass this option if there is no header. Default: False'
    )
    parser.add_argument(
        '-o', '--outfile',
        help='Choose an output file to save the results. '
             'The results are appended to the file (added after the last line). '
             'Default: None, prints to console.'
    )
    parser.add_argument(
        '-p', '--preamble',
        action='store_true',
        help='If selected, makes a whole .tex document (including the preamble) '
             'ready to be built as .pdf. Useful when trying to make a quick report. '
             'Default: False'
    )
    parser.add_argument(
        '-s', '--sep',
        default=',',
        help=r'Choose a separator between columns. If a file is tab-separated, '
             r'pass `t` or `tab`. If a file is semicolon-separated, '
             r'pass `s`, `semi` or `\;`.'
             r'Default: `,` (comma-separated)'
    )
    parser.add_argument(
        '-u', '--units',
        nargs='+',
        help='Provide units for each column. If column has no unit, denote it '
             'by passing either `-`, `/` or `0`. If `--no-header` is used, '
             'this argument is ignored.'
    )
    return parser.parse_args()


def main():
    options = arg_parser()
    tably = Tably(options)
    tably.run()


if __name__ == '__main__':
    main()
