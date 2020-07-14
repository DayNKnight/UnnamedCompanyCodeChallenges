"""
Author: Zack Knight
Date: 5/5/2020

Level 1 Python Script for a coding challenge for one of the interviews I was doing

Instructions:
Your solution must include a design and working code.

Level 1
    1.Create a program that reads an ELF file, finds all the strings in it, and writes them neatly to a log file.
"""
import argparse
import os
import re
import string

chars = b"A-Za-z0-9/\-:.,_$%\'\"\(\)\[\]<> "
shortest_run = 4

regexp = b'[%s]{%d,}' % (chars, shortest_run)
pattern = re.compile(regexp)
printable = set(string.printable)

# Combination of code from https://stackoverflow.com/questions/6804582/extract-strings-from-a-binary-file-in-python and 
# the fireeye flarestrings https://github.com/fireeye/stringsifter/blob/master/stringsifter/flarestrings.py

def main(inFile,outFile):
    # Read in the bytes of the file
    k = inFile.read()
    string_list = []
    # Iterate through the matches and decode them to ascii to be appended to the strings list
    for m in pattern.finditer(k):
        string_list.append(m.group().decode('ascii'))
    
    # Write the strings list to the output file
    with open(outFile,'w') as outF:
        for string in string_list:
            outF.write(string + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reads in ELF files and outputs the strings to an output file")
    parser.add_argument('--in',dest='inFile',help="The file to be parsed", required=True,type=argparse.FileType('rb'))
    parser.add_argument("--out",dest='out',help="The log file name to be outputted to. WARNING: THIS WILL OVERWRITE AN EXISTING FILE",default="Results.txt")

    args = parser.parse_args()
    main(args.inFile,args.out)
