#!/usr/bin/python
"""duplex.py - Manual duplex printing for linux
"""
from __future__ import print_function
import argparse
import PyPDF2
import subprocess
import os
import xml.etree.ElementTree as ET
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

#some global variables 
current_printer = ""
size = "A4"
output_files = []
printers = []
config_file = 'config.xml'
isRotateFirstFace = False
isReverseFirstFace = False
filepath = ""

def read_config():
    """
    Read the transforms that are to be applied to the pdf
    :param configuration: The filename of the configuration xml
    :return: (transforms, printer, size), where:
        transforms is a dictionary of the transforms. The keys are the print order of each part.
        printer is the name of the printer
        size is the size of the paper, or 'a4' if none was defined in the configuration
    """
    tree = ET.parse('config.xml')
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

def write_config():
    global current_printer
    global size
    global isReverseFirstFace
    global isRotateFirstFace
    tree = ET.parse('config.xml')
    root = tree.getroot()
    for item in root.findall("printer"):
        print( item.tag )
        print( item.text )
        item.text = current_printer
    for item in root.findall("size"):
        print( item.tag )
        print( item.text )
        item.text = size

    with open('config.xml', 'wb') as f:
        tree.write(f, encoding='utf-8')


def transform_pdf(transforms):
    global filepath
    global isRotateFirstFace
    global isReverseFirstFace
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
#            rotation = int(transform.get('rotate', 0))
            rotation = 0
            reverse = False
            if transform['pages'] == 'even':
                if isRotateFirstFace :
                    rotation = 180
                reverse = isReverseFirstFace 

            print(rotation)
            print(isReverseFirstFace)
            # Reverse order of pages if requested
            #reverse = bool(transform.get('reverse', False))
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

def print_pdf(printer, filepath, size):
    """
    Print a PDF file using lp
    :param printer: The printer that will be used
    :param filepath: The path to the PDF
    :return: None
    """
    subprocess.call(['lp', '-o', 'media='+size, '-o', 'fit-to-page', '-d', printer, filepath])

def fcDialog_onFileset(P1, P2):
    global output_files
    global filepath
    filepath = fcDialog.get_filename()
    btnPrint1.set_sensitive(True)
    return

def btnPrinters_onChanged(P1):
    global size
    global current_printer
    index = btnPrinters.get_active()
    current_printer = printers[index]
    write_config()
    return

def btnSizes_onChanged(P1):
    global size
    global current_printer
    index = btnSizes.get_active()
    size= sizes[index]
    write_config()
    return

def btnPrint1_onClicked(P1, P2):
    global output_files
    global current_printer
    global filepath
    global size
    output_files = transform_pdf(transforms)
    print_pdf(current_printer, output_files[0], size)
    btnPrint2.set_sensitive(True)
    return

def btnPrint2_onClicked(P1, P2):
    global output_files
    global current_printer
    print_pdf(current_printer, output_files[1], size)
    return
def cbRotate_onChecked(P1, P2):
    global isRotateFirstFace 
    isRotateFirstFace = cbRotate.get_active()
    return
def cbReverse_onChecked(P1, P2):
    global isReverseFirstFace
    isReverseFirstFace = cbReverse.get_active()
    return
def btnClose_onClicked(P1, P2):
    for file in output_files:
        os.remove(file)
    Gtk.main_quit()
    quit()


if __name__ == '__main__':
    transforms, current_printer, size = read_config()
    for printer in printer_list():
        print('====> {}'.format(printer))
    builder = Gtk.Builder()
    builder.add_from_file("duplex.glade")
    window = builder.get_object("window1")
    fcDialog = builder.get_object("fcDialog")
    btnPrint1 = builder.get_object("btnPrint1")
    btnPrint2 = builder.get_object("btnPrint2")
    btnClose = builder.get_object("btnClose")
    btnPrinters = builder.get_object("btnPrinters")
    btnSizes = builder.get_object("btnSizes")
    cbRotate = builder.get_object("cbRotate")
    cbReverse = builder.get_object("cbReverse")
    window.connect("destroy", Gtk.main_quit)
    fcDialog.connect("file-set",fcDialog_onFileset,None)
    btnPrint1.connect("clicked",btnPrint1_onClicked,None)
    btnPrint2.connect("clicked",btnPrint2_onClicked,None)
    btnClose.connect("clicked",btnClose_onClicked,None)
    cbRotate.connect("toggled",cbRotate_onChecked, None)
    cbReverse.connect("toggled",cbReverse_onChecked, None)
    
    printer_store = Gtk.ListStore(str)
    active = 0
    ix = 0
    
    for printer in printer_list():
        if printer == current_printer:
            active = ix
        ix+=1
        printer_store.append([printer])
        printers.append(printer)
    
    btnPrinters.set_model(printer_store)
    btnPrinters.connect("changed", btnPrinters_onChanged)
    renderer_text = Gtk.CellRendererText()
    btnPrinters.pack_start(renderer_text, True)
    btnPrinters.add_attribute(renderer_text, "text", 0)
    
    btnPrinters.set_active(active)
 
    sizes = ['Letter','Legal','Ledger','Executive','A1','A2','A3','A4','A5','A6','B1','B2','B3','B4','B5','B6']
    size_store = Gtk.ListStore(str)
    active = 0
    ix = 0
    
    for sz in sizes:
        if sz == size:
            active = ix
        ix+=1
        size_store.append([sz])

    
    btnSizes.set_model(size_store)
    btnSizes.connect("changed", btnSizes_onChanged)
    renderer_text2 = Gtk.CellRendererText()
    btnSizes.pack_start(renderer_text2, True)
    btnSizes.add_attribute(renderer_text2, "text", 0)
    
    btnSizes.set_active(active)

 
    window.show_all()
    Gtk.main()
