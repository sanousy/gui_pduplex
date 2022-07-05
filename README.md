# pduplex - Manual Dual Sided Printing for Linux

Simple python script for manual dual sided printing of PDF files on linux. Can be configured to work on any printer as long as you find out how the pages need to be transformed.
This version has gpduplex.py, which wraps the same original functionality of command line, but using gui.

below how it should look like:

![Screenshot at 2022-07-06 00-54-49](https://user-images.githubusercontent.com/19352122/177423538-d2670e6b-07a9-403c-9eb8-b04b9085c8bd.png)


all you need, is to print the first face, and then take the printed papers, and put them back into the printer feeder, then click the second print button, happy printing.

## Dependencies
- PyPDF2
- PyGtk

## Instructions
- Make the file executable: `chmod +x pduplex.py`
- Edit config.xml
    - Set the name of your printer as reported by `lpstat -a`
    - Set the paper size
    -  Set the transformations. The the two `out` tags define how the odd/even pages will be transformed in order for the dual sided print to be correct. The existing settings work for my laser printer (HP LarseJet P1006) which has the paper tray at the bottom. For different printers you might want to take a look [here](http://duramecho.com/ComputerInformation/HowToDoTwoSidedPrinting/).
- To Print you have 2 choices:
    - Using Command line: by executing > `./pduplex.py your_file_name.pdf`
    - Using Graphical User Interface: print by double clicking running pduplex.sh
        - remark you can make link to anywhere (on your desktop for exampe) of pduplex.sh).

