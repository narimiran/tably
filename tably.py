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


def add_label(label, indent):
    """Creates a table label"""
    return LABEL.format(label=label, indent=indent) if label else ''


def add_caption(caption, indent):
    """Creates a table caption"""
    return CAPTION.format(caption=caption, indent=indent) if caption else ''


def create_row(line, indent):
    """Creates a row based on `line` content"""
    def escape(line):
        for char in '#$%&_}{':
            line = [column.replace(char, '\\'+char) for column in line]
        return line

    return r'{indent}{indent}{content} \\'.format(
              indent=indent,
              content=' & '.join(escape(line)))


def create_table(file, no_header, label, caption, align, indent, skip):
    """Creates a table from a given .csv file.

    The function `run` calls this function. See its docstring for more
    information about the arguments.
    """
    rows = []
    indent = 4*' ' if indent else ''

    try:
        with open(file) as infile:
            for i, line in enumerate(csv.reader(infile)):
                if i < skip:
                    continue
                rows.append(create_row(line, indent))
    except FileNotFoundError:
        print("File {} doesn't exist!!\n".format(file))
        return ''

    if not no_header:
        rows.insert(1, r'{0}{0}\midrule'.format(indent))

    header = HEADER.format(
        label=add_label(label, indent),
        caption=add_caption(caption, indent),
        align=format_alignment(align, len(line)),
        indent=indent,
    )
    content = '\n'.join(rows)
    footer = FOOTER.format(indent=indent)
    return '\n'.join((header, content, footer))


def save_content(content, outfile):
    """Saves the content to a file.

    If the existing file is provided, the content is appended to the end
    of the file.
    """
    with open(outfile, 'a') as out:
        out.writelines(content)
    print('The content is added to', outfile)


def run(files, no_header, label, caption, align, indent, outfile, skip, preamble):
    """The main function.

    For each file in `files`, calls `create_table` funtion.
    If `outfile` is provided, calls `save_content` function,
    otherwise prints to the console.

    Args:
        file (string): name of the .csv file
        no_header (bool): if the .csv contains only content, without a
            header (names for the columns)
        label (string): a label by which the table can be referenced
        caption (string): the name of the table, printed above it
        align (string): wanted alignment of the columns
        indent (bool): should a LaTeX code be indented with 4 spaces per
            code block. Doesn't affect the final looks of the table.
        outfile (string): name of the file where to save the results.
        skip (int): number of rows in .csv to skip
        whole (bool): creating of a whole .tex document (including the preamble)
    """
    if preamble:
        all_tables = [PREAMBLE]
    else:
        all_tables = ['\n% \\usepackage{booktabs} % move this to preamble and uncomment']
    if label and len(files) > 1:
        all_tables.append("% don't forget to manually re-label the tables")
    for file in files:
        table = create_table(file, no_header, label, caption, align, indent, skip)
        all_tables.append(table)
    if preamble:
        all_tables.append(r'\end{document}')

    final_content = '\n\n'.join(all_tables)
    if outfile:
        try:
            save_content(final_content, outfile)
        except FileNotFoundError:
            print('{} is not a valid/known path. Could not save there.'.format(outfile))
    else:
        print(final_content)


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
        '-i', '--indent',
        action='store_true',
        help='Indents LaTeX source code with 4 spaces per float. '
             'No difference in the final result, just LaTeX code is '
             'slightly more readable. Default: False'
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
        '-s', '--skip',
        type=int,
        default=0,
        help='Number of rows in .csv to skip. Default: 0'
    )
    return parser.parse_args()

def main():
    options = arg_parser()
    run(**vars(options))
    
if __name__ == '__main__':
    main()
