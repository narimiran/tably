#!/usr/bin/env python3

# To directly call tably from shell, set a symbolic link by running
# ln -sf $PWD/tably.py /usr/local/bin/tably

import argparse
import csv
import os


PREAMBLE = r"""\documentclass[11pt, a4paper]{article}
\usepackage{booktabs}
\begin{document}"""

HEADER = r"""\begin{{table}}[htb]
{indent}\centering{caption}{label}
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
        run: selects the appropriate methods to generate LaTeX code/files
        create_table: for each specified file, creates a LaTeX table
        create_row: creates a row based on `line` content
        combine_tables: combines all tables from input files together
        save_single_table: creates and saves a single LaTeX table
        get_units: writes the units as a row of the LaTeX table
    """

    def __init__(self, args):
        """
        Attributes:
            files (string): name(s) of the .csv file(s)
            no_header (bool): if the .csv contains only content, without a
                header (names for the columns)
            caption (string): the name of the table, printed above it
            label (string): a label by which the table can be referenced
            align (string): wanted alignment of the columns
            no_indent (bool): should a LaTeX code be indented with 4 spaces per
                code block. Doesn't affect the final looks of the table.
            outfile (string): name of the file where to save the results.
            separate_outfiles (list): names of the files where each table is saved
            skip (int): number of rows in .csv to skip
            preamble(bool): create a preamble
            sep (string): column separator
            units (list): units for each column
            fragment (bool): only output content in tabular environment
            fragment_skip_header (bool): shortcut of passing -k 1 -n -f
            replace (bool): replace existing output file if -o is passed
            tex_str (function): escape LaTeX special characters or do nothing
        """
        self.files = args.files
        self.no_header = args.no_header
        self.caption = args.caption
        self.label = args.label
        self.align = args.align
        self.no_indent = args.no_indent
        self.outfile = args.outfile
        self.separate_outfiles = args.separate_outfiles
        self.skip = args.skip
        self.preamble = args.preamble
        self.sep = get_sep(args.sep)
        self.units = args.units
        self.fragment = args.fragment
        self.fragment_skip_header = args.fragment_skip_header
        self.replace = args.replace
        self.tex_str = escape if not args.no_escape else lambda x: x

    def run(self):
        """The main method.

        If all tables need to be put into a single file,
        calls `combine_tables` method to generate LaTeX code
        and then calls `save_content` function if `outfile` is provided;
        otherwise, prints to the console.
        If each table needs to be put into a separate file,
        calls `save_single_table` method to create and save each table separately.
        """

        if self.fragment_skip_header:
            self.skip = 1
            self.no_header = True
            self.fragment = True

        if self.fragment:
            self.no_indent = True
            self.label = None
            self.preamble = False

        # if all tables need to be put into one file
        if self.outfile or self.separate_outfiles is None:
            final_content = self.combine_tables()
            if not final_content:
                return
            if self.outfile:
                try:
                    save_content(final_content, self.outfile, self.replace)
                except FileNotFoundError:
                    print('{} is not a valid/known path. Could not save there.'.format(self.outfile))
            else:
                print(final_content)

        # if -oo is passed (could be [])
        if self.separate_outfiles is not None:
            outs = self.separate_outfiles
            if len(outs) == 0:
                outs = [ os.path.splitext(file)[0]+'.tex' for file in self.files ]
            elif os.path.isdir(outs[0]):
                outs = [ os.path.join(outs[0], os.path.splitext(os.path.basename(file))[0])+'.tex' for file in self.files ]
            elif len(outs) != len(self.files):
                print('WARNING: Number of .csv files and number of output files do not match!')
            for file, out in zip(self.files, outs):
                self.save_single_table(file, out)

    def create_table(self, file):
        """Creates a table from a given .csv file.

        This method gives the procedure of converting a .csv file to a LaTeX table.
        Unless -f is specified, the output is a ready-to-use LaTeX table environment.
        All other methods that need to obtain a LaTeX table from a .csv file call this method.
        """
        rows = []
        indent = 4*' ' if not self.no_indent else ''

        try:
            with open(file) as infile:
                for i, columns in enumerate(csv.reader(infile, delimiter=self.sep)):
                    if i < self.skip:
                        continue
                    rows.append(self.create_row(columns, indent))
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
                units = self.get_units()
                rows.insert(1, r'{0}{0}{1} \\'.format(indent, units))

        content = '\n'.join(rows)
        if not self.fragment:
            header = HEADER.format(
            label=add_label(self.label, indent),
            caption=add_caption(self.caption, indent),
            align=format_alignment(self.align, len(columns)),
            indent=indent,
            )
            footer = FOOTER.format(indent=indent)
            return '\n'.join((header, content, footer))
        else:
            return content

    def create_row(self, line, indent):
        """Creates a row based on `line` content"""
        return r'{indent}{indent}{content} \\'.format(
             indent=indent,
             content=' & '.join(self.tex_str(line)))

    def combine_tables(self):
        """Combine all tables together and add a preamble if required.

        Unless -oo is specified, this is how input tables are arranged.
        """
        all_tables = []
        if self.label and len(self.files) > 1:
            all_tables.append("% don't forget to manually re-label the tables")

        for file in self.files:
            table = self.create_table(file)
            if table:
                all_tables.append(table)
        if not all_tables:
            return None
        if self.preamble:
            all_tables.insert(0, PREAMBLE)
            all_tables.append('\\end{document}\n')
        return '\n\n'.join(all_tables)

    def save_single_table(self, file, out):
        """Creates and saves a single LaTeX table"""
        table = [self.create_table(file)]
        if table:
            if self.preamble:
                table.insert(0, PREAMBLE)
                table.append('\\end{document}\n')
            final_content = '\n\n'.join(table)
            try:
                save_content(final_content, out, self.replace)
            except FileNotFoundError:
                print('{} is not a valid/known path. Could not save there.'.format(out))

    def get_units(self):
        """Writes the units as a row of the LaTeX table"""
        formatted_units = []
        for unit in self.tex_str(self.units):
            if unit in '-/0':
                formatted_units.append('')
            else:
                formatted_units.append('[{}]'.format(unit))
        return ' & '.join(formatted_units)


def get_sep(sep):
    if sep.lower() in ['t', 'tab', '\\t']:
        return '\t'
    elif sep.lower() in ['s', 'semi', ';']:
        return ';'
    elif sep.lower() in ['c', 'comma', ',']:
        return ','
    else:
        return sep


def escape(line):
    """Escapes special LaTeX characters by prefixing them with backslash"""
    for char in '#$%&_}{':
        line = [column.replace(char, '\\'+char) for column in line]
    return line


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


def save_content(content, outfile, replace):
    """Saves the content to a file.

    If an existing file is provided, the content is appended to the end
    of the file by default. If -r is passed, the file is overwritten.
    """
    if replace:
        with open(outfile, 'w') as out:
            out.writelines(content)
        print('The content is written to', outfile)
    else:
        with open(outfile, 'a') as out:
            out.writelines(content)
        print('The content is appended to', outfile)



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
        '-oo', '--separate-outfiles',
        metavar='PATH',
        nargs='*',
        help='When multiple .csv files need to be processed, '
             'pass -oo to save each individual table in a separate .tex file. '
             'To specifiy each individual output file, '
             'pass a list of filenames after -oo. '
             'Alternatively, pass a directory that will store all the output files. '
             'If no filename/directory is passed after -oo, '
             'filenames of .csv files will be used (with .tex extension).'
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
    parser.add_argument(
        '-e', '--no-escape',
        action='store_true',
        help='If selected, do not escape special LaTeX characters.'
    )
    parser.add_argument(
        '-f', '--fragment',
        action='store_true',
        help='If selected, only output content inside tabular environment '
             '(no preamble, table environment, etc.).'
    )
    parser.add_argument(
        '-ff', '--fragment-skip-header',
        action='store_true',
        help='Equivalent to passing -k 1 -n -f '
             '(suppress header when they are on the first row of .csv and pass -f).'
    )
    parser.add_argument(
        '-r', '--replace',
        action='store_true',
        help='If selected and -o or -oo is passed, overwrite any existing output file.'
    )
    return parser.parse_args()


def main():
    options = arg_parser()
    tably = Tably(options)
    tably.run()


if __name__ == '__main__':
    main()
