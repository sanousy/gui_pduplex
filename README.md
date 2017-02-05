# pduplex - Manual Dual Sided Printing for Linux

Simple python script for manual dual sided printing of PDF files on linux. Can be configured to work on any printer as long as you find out how the pages need to be transformed.

## Dependencies
- PyPDF2

## Instructions
- Make the file executable: `chmod +x pduplex.py`
- Edit config.xml
    - Set the name of your printer as reported by `lpstat -a`
    - Set the paper size
    -  Set the transformations. The the two `out` tags define how the odd/even pages will be transformed in order for the dual sided print to be correct. The existing settings work for my laser printer (HP LarseJet P1006) which has the paper tray at the bottom. For different printers you might want to take a look [here](http://duramecho.com/ComputerInformation/HowToDoTwoSidedPrinting/).
- Print by executing `./pduplex.py your_file_name.pdf`
