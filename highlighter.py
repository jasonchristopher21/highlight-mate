# Import Libraries
from typing import Tuple
from io import BytesIO
import os
import argparse
import re
import fitz
import shutil

def main():

    print("##############################################")
    print("Hi there! Please specify the file path")
    while True:
        path = input("Path: ")
        if os.path.isfile(path):
            break
        print("Invalid path provided! Please provide a correct file path:")
    print("Please specify an optional name to be appended to the new file")
    opt_name = input("Name: ")
    dest = path.strip()[:len(path) - 4] + opt_name + ".pdf"
    # if not os.path.isfile(path):
    shutil.copyfile(path, dest)
    print("Please specify notes to be highlighted, separated by spaces")
    notes = input("Notes: ")
    notes = notes.strip().split()
    print("Processing: ------------------------------------------------")

    process_file(
        input_file = dest, output_file = dest, words = notes, pages = None, action = None
    )

def extract_info(input_file: str):
    """
    Extracts file info
    """
    # Open the PDF
    pdfDoc = fitz.open(input_file)
    output = {
        "File": input_file, "Encrypted": ("True" if pdfDoc.isEncrypted else "False")
    }
    # If PDF is encrypted the file metadata cannot be extracted
    if not pdfDoc.isEncrypted:
        for key, value in pdfDoc.metadata.items():
            output[key] = value
    # To Display File Info
    print("## File Information ##################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in output.items()))
    print("######################################################################")
    return True, output

def search_for_text(lines, search_str):
    """
    Search for the search string within the document lines
    """
    i = 0
    for line in lines:
        # Find all matches within one line
        results = re.findall(search_str, line, re.UNICODE)
        for result in results:
            yield result
            
def highlight_matching_data(page, matched_values, color):
    """
    Highlight matching values
    """
    matches_found = 0
    # Loop throughout matching values
    for val in matched_values:
        matches_found += 1
        matching_val_area = page.get_text("words",sort=False)
        print(color)
        for word in matching_val_area:
            if val in word[4]:
                rect_comp = create_rectangle(word, val)
                # rect_comp = fitz.Rect(word[0],word[1],word[2],word[3])
                highlight = page.add_highlight_annot(rect_comp)
                if color == 1:
                    print("this set")
                    highlight.set_colors({"stroke":(0,1,0),"fill":None})
                elif color == 2:
                    highlight.set_colors({"stroke":(0,1,1),"fill":None})
                elif color == 3:
                    highlight.set_colors(colors=fitz.utils.getColor('pink'))
                highlight.update()
    return matches_found

def process_data(input_file: str, output_file: str, words, pages: Tuple = None, action: str = 'Highlight'):
    """
    Process the pages of the PDF File
    """
    # Open the PDF
    pdfDoc = fitz.open(input_file)
    # Save the generated PDF to memory buffer
    output_buffer = BytesIO()
    total_matches = 0
    # Iterate through pages
    for pg in range(pdfDoc.page_count):
        # If required for specific pages
        if pages:
            if str(pg) not in pages:
                continue
        # Select the page
        page = pdfDoc[pg]
        # Get Matching Data
        # Split page by lines
        page_lines = page.get_text("text").split('\n')
        counter = -1
        for word in words:
            matched_values = search_for_text(page_lines, word)
            counter += 1
            if matched_values:
                print(counter)
                matches_found = highlight_matching_data(
                    page, matched_values, counter)
                total_matches += matches_found
            # print(f"{total_matches} Match(es) Found of Search String {word} In Input File: {input_file}")
    # Save to output
    print(f"Highlighting done! File can be found in {input_file}")
    pdfDoc.save(output_buffer)
    pdfDoc.close()
    # Save the output buffer to the output file
    with open(output_file, mode='wb') as f:
        f.write(output_buffer.getbuffer())

def process_file(**kwargs):
    """
    To process one single file
    Redact, Frame, Highlight... one PDF File
    Remove Highlights from a single PDF File
    """
    input_file = kwargs.get('input_file')
    output_file = kwargs.get('output_file')
    if output_file is None:
        output_file = input_file
    words = kwargs.get('words')
    pages = kwargs.get('pages')
    action = kwargs.get('action')
    process_data(input_file=input_file, output_file=output_file,
                    words=words, pages=pages, action=action)

def is_valid_path(path):
    """
    Validates the path inputted and checks whether it is a file path or a folder path
    """
    if not path:
        raise ValueError(f"Invalid Path")
    if os.path.isfile(path):
        return path
    elif os.path.isdir(path):
        return path
    else:
        raise ValueError(f"Invalid Path {path}")


def parse_args():
    """Get user command line parameters"""
    parser = argparse.ArgumentParser(description="Available Options")
    parser.add_argument('-i', '--input_path', dest='input_path', type=is_valid_path,
                        required=True, help="Enter the path of the file or the folder to process")
    parser.add_argument('-a', '--action', dest='action', choices=['Redact', 'Frame', 'Highlight', 'Squiggly', 'Underline', 'Strikeout', 'Remove'], type=str,
                        default='Highlight', help="Choose whether to Redact or to Frame or to Highlight or to Squiggly or to Underline or to Strikeout or to Remove")
    parser.add_argument('-p', '--pages', dest='pages', type=tuple,
                        help="Enter the pages to consider e.g.: [2,4]")
    action = parser.parse_known_args()[0].action
    if action != 'Remove':
        parser.add_argument('-s', '--search_str', dest='search_str'                            # lambda x: os.path.has_valid_dir_syntax(x)
                            , type=str, required=True, help="Enter a valid search string")
    path = parser.parse_known_args()[0].input_path
    if os.path.isfile(path):
        parser.add_argument('-o', '--output_file', dest='output_file', type=str  # lambda x: os.path.has_valid_dir_syntax(x)
                            , help="Enter a valid output file")
    if os.path.isdir(path):
        parser.add_argument('-r', '--recursive', dest='recursive', default=False, type=lambda x: (
            str(x).lower() in ['true', '1', 'yes']), help="Process Recursively or Non-Recursively")
    args = vars(parser.parse_args())
    # To Display The Command Line Arguments
    print("## Command Arguments #################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in args.items()))
    print("######################################################################")
    return args

def create_rectangle(word, val):
    text = word[4]
    x0 = word[0]
    y0 = word[1]
    x1 = word[2]
    y1 = word[3]
    word_length = len(text)
    distance = (x1 - x0) // word_length
    for i in range(word_length):
        if text[i] == val:
            new_x0 = x0 + i * distance
            new_x1 = new_x0 + distance
            return fitz.Rect(new_x0, y0, new_x1, y1)


if __name__ == "__main__":
    main()