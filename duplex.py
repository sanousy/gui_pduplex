#!/usr/bin/python
"""duplex.py - Manual duplex printing for linux
"""
from __future__ import print_function
import argparse
import PyPDF2
import subprocess
import os
import xml.etree.ElementTree as ET


def read_config(configuration):
    """
    Read the transforms that are to be applied to the pdf
    :param configuration: The filename of the configuration xml
    :return: (transforms, printer, size), where:
        transforms is a dictionary of the transforms. The keys are the print order of each part.
        printer is the name of the printer
        size is the size of the paper, or 'a4' if none was defined in the configuration
    """
    tree = ET.parse(configuration)
    root = tree.getroot()
    transforms = []
    printer = ''
    size = 'a4'
    for child in root:
        if child.tag == 'out':
            transforms.append(child.attrib)
        elif child.tag == 'printer':
            printer = child.text
        elif child.tag == 'size':
            size = child.text
        else:
            raise NotImplementedError('Unknwon configuration option: {}'.format(child.tag))
        transforms.sort(key=lambda x: x['order'])
    return transforms, printer, size


def transform_pdf(filepath, transforms):
    """
    Apply the given transformations, in order, to the PDF given
    :param filepath: The path of the PDF
    :param transforms: The transformations to be applied, already ordered
    :return: The names of the PDF files created through the transforms.
    """
    output_files = []
    with open(filepath, 'rb') as pdf:
        reader = PyPDF2.PdfFileReader(pdf)

        # bypass 0-based indexing, because all UI pdf readers start from 1
        odd_pages = [i for i in range(reader.getNumPages()) if (i + 1) % 2 != 0]
        even_pages = [i for i in range(reader.getNumPages()) if (i + 1) % 2 == 0]

        for idx, transform in enumerate(transforms):
            page_nums = list(odd_pages) if transform['pages'] == 'odd' else list(even_pages)
            pages = [reader.getPage(page) for page in page_nums]
            # Rotate if requested
            rotation = int(transform.get('rotate', 0))
            # Reverse order of pages if requested
            reverse = bool(transform.get('reverse', False))
            # Append blank page before/after the pages
            add_blank = transform.get('addBlank', '').lower()
            if add_blank and add_blank not in ['before', 'after']:
                raise NotImplementedError('Invalid value "{}" for addBlank attribute.'
                                          'Can only be "before" or "after"'.format(add_blank))
            output_pdf = output_name(filepath, idx)
            save_pages(output_pdf, pages, rotation, reverse, add_blank)
            output_files.append(output_pdf)
    return output_files


def save_pages(filepath, pages, rotation=0, reverse_order=False, add_blank=None):
    """
    Save a list of PDF pages after transforming them
    :param filepath: The path to save the file to
    :param pages: The list of pages to be saved
    :param rotation: Amount of rotation of each page, in degrees
    :param reverse_order: True if the order of the pages must be reversed
    :param add_blank: 'before', 'after' or None, based on whether a blank page must be added before or after the other
    pages
    :return: None. A PDF file will be saved in the directory of the program
    """
    writer = PyPDF2.PdfFileWriter()
    pages = reversed(pages) if reverse_order else pages
    if add_blank == 'before':
        writer.addBlankPage()
    for page in pages:
        if rotation != 0:
            page.rotateClockwise(rotation)
        writer.addPage(page)
    if add_blank == 'after':
        writer.addBlankPage()
    with open(filepath, 'wb') as output:
        writer.write(output)


def is_valid_file(filepath):
    """
    Check whether the path given points to an existing file
    :param filepath: A string of the file path
    :return: The filepath, if it was valid. If not, an IOError is raised.
    """
    if not os.path.exists(filepath):
        raise IOError('File {} does not exist'.format(filepath))
    else:
        return filepath  # return an open file handle


def output_name(filepath, suffix):
    """
    Get the name of the pdf plus a suffix for output purposes
    :param filepath: The path to the pdf
    :param suffix: A suffix that helps differentiate output files
    :return: the output file with the desired suffix, based on the given filepath
    """
    base = os.path.basename(filepath)
    name = os.path.splitext(base)[0]
    return '{}_{}.pdf'.format(name, suffix)


def printer_list():
    """Get a list of the available printers in the system, as reported by lp
    """
    lp_raw_output = subprocess.check_output('lpstat -a', shell=True)
    printer_entries = lp_raw_output.decode('utf-8').strip().split('\n')
    printer_names = [x.split()[0] for x in printer_entries]
    return printer_names


def duplex_print(files, printer, size):
    """
    Run a manual dual sided print
    :param files: The list of filenames to print. Must have length equal to 2
    :param printer: The name of the printer
    :param size: The paper size, e.g. a4
    :return: None
    """
    if not printer:
        raise RuntimeError('Printer was not defined in config. Will not print')
    if len(files) != 2:
        raise RuntimeError('Unexpected number of output files: {}'.format(len(output_files)))
    print('[*] Printing first side. Please wait...')
    print_pdf(printer, files[0], size)
    try:
        input('[-] When the first side has finished printing, place the pages back into the paper tray'
              'and press [ENTER]: ')
    except:
        pass
    print('[*] Printing first side. Please wait...')
    print_pdf(printer, files[1], size)
    print('[*] Removing temporary files...')
    for file in files:
        os.remove(file)
    print('[*] Done!')


def print_pdf(printer, filepath, size):
    """
    Print a PDF file using lp
    :param printer: The printer that will be used
    :param filepath: The path to the PDF
    :return: None
    """
    subprocess.call(['lp', '-o', 'size', '-o', 'fit-to-page', '-d', printer, filepath])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manual Duplex Printing for Linux')
    parser.add_argument(help='input PDF file',
                        dest='filename', metavar='FILE',
                        type=lambda x: is_valid_file(x))
    parser.add_argument('-d', '--dry', help='do not print the PDF. Just create the files corresponding to each side in'
                                            'the directory of the program', action='store_true')
    # Parse the CLI arguments
    args = parser.parse_args()
    # Read the configuration
    transforms, printer, size = read_config('config.xml')
    # If not printer was set in the configuration
    if not args.dry and not printer:
        print('[*] No printer was set in the configuration.')
        print('[*] The following printers were detected: ')
        for printer in printer_list():
            print('====> {}'.format(printer))
        print('[*] Please copy the name of the printer you want to use into the configuration file')
        print('[*] or launch the program using the parameter -d for a dry run')
        exit(0)
    # Create temporary PDFs
    output_files = transform_pdf(args.filename, transforms)
    print('[*] Created PDFs for each side: {}'.format(output_files))
    # If print requested, do print
    if not args.dry:
        duplex_print(output_files, printer, size)
