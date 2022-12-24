# Import Libraries
from typing import Tuple
from io import BytesIO
import os
import argparse
import re
import fitz

def main():
    # Parsing command line arguments entered by user
    args = parse_args()
    # If File Path
    if os.path.isfile(args['input_path']):
        # Extracting File Info
        extract_info(input_file=args['input_path'])
        # Process a file
        process_file(
            input_file=args['input_path'], output_file=args['output_file'], 
            search_str=args['search_str'] if 'search_str' in (args.keys()) else None, 
            pages=args['pages'], action=args['action']
        )
    # If Folder Path
    elif os.path.isdir(args['input_path']):
        # Process a folder
        process_folder(
            input_folder=args['input_path'], 
            search_str=args['search_str'] if 'search_str' in (args.keys()) else None, 
            action=args['action'], pages=args['pages'], recursive=args['recursive']
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
        # results = []
        # found = False
        # temp = ""
        # for c in line:
        #     if ord(c) == ord(search_str):
        #         found = True
        #         results.append(c)
        #         # temp += c
        #     elif found and (c == "."):
        #         # temp += c
        #         results.append(c)
        #     else:
        #         found = False
        #         # if temp:
        #         #     results.append(temp)
        # # In case multiple matches within one line
        # # print("line:", i, "result:",results)
        # i += 1
        for result in results:
            yield result
            
def highlight_matching_data(page, matched_values, type):
    """
    Highlight matching values
    """
    matches_found = 0
    # Loop throughout matching values
    for val in matched_values:
        matches_found += 1
        matching_val_area = page.get_text("words",sort=False)
        print(val)
        print(matching_val_area)
        for word in matching_val_area:
            if val in word[4]:
                rect_comp = create_rectangle(word, val)
                # rect_comp = fitz.Rect(word[0],word[1],word[2],word[3])
                highlight = page.add_highlight_annot(rect_comp)
                highlight.update()
        # matching_val_area = page.search_for(val)
        # for coordinate in matching_val_area:
        #     if not isExactMatch(page, val, coordinate, False, True):
        #         matching_val_area.remove(coordinate)
        # print("matching_val_area",matching_val_area)
        # highlight = None
        # if type == 'Highlight':
        #     highlight = page.add_highlight_annot(matching_val_area)
        # elif type == 'Squiggly':
        #     highlight = page.add_squiggly_annot(matching_val_area)
        # elif type == 'Underline':
        #     highlight = page.add_underline_annot(matching_val_area)
        # elif type == 'Strikeout':
        #     highlight = page.add_strikeout_annot(matching_val_area)
        # else:
        #     highlight = page.add_highlight_annot(matching_val_area)
        # # To change the highlight colar
        # # highlight.setColors({"stroke":(0,0,1),"fill":(0.75,0.8,0.95) })
        # # highlight.setColors(stroke = fitz.utils.getColor('white'), fill = fitz.utils.getColor('red'))
        # # highlight.setColors(colors= fitz.utils.getColor('red'))
        # highlight.update()
    return matches_found

def process_data(input_file: str, output_file: str, search_str: str, pages: Tuple = None, action: str = 'Highlight'):
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
        matched_values = search_for_text(page_lines, search_str)
        if matched_values:
            matches_found = highlight_matching_data(
                page, matched_values, 'Highlight')
            total_matches += matches_found
    print(f"{total_matches} Match(es) Found of Search String {search_str} In Input File: {input_file}")
    # Save to output
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
    search_str = kwargs.get('search_str')
    pages = kwargs.get('pages')
    # Redact, Frame, Highlight, Squiggly, Underline, Strikeout, Remove
    action = kwargs.get('action')
    if action == "Remove":
        # Remove the Highlights except Redactions
        remove_highlght(input_file=input_file,
                        output_file=output_file, pages=pages)
    else:
        process_data(input_file=input_file, output_file=output_file,
                     search_str=search_str, pages=pages, action=action)

def process_folder(**kwargs):
    """
    Redact, Frame, Highlight... all PDF Files within a specified path
    Remove Highlights from all PDF Files within a specified path
    """
    input_folder = kwargs.get('input_folder')
    search_str = kwargs.get('search_str')
    # Run in recursive mode
    recursive = kwargs.get('recursive')
    #Redact, Frame, Highlight, Squiggly, Underline, Strikeout, Remove
    action = kwargs.get('action')
    pages = kwargs.get('pages')
    # Loop though the files within the input folder.
    for foldername, dirs, filenames in os.walk(input_folder):
        for filename in filenames:
            # Check if pdf file
            if not filename.endswith('.pdf'):
                continue
             # PDF File found
            inp_pdf_file = os.path.join(foldername, filename)
            print("Processing file =", inp_pdf_file)
            process_file(input_file=inp_pdf_file, output_file=None,
                         search_str=search_str, action=action, pages=pages)
        if not recursive:
            break

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

def isExactMatch(page, term, clip, fullMatch=False, caseSensitive=False):
# clip is an item from page.search_for(term, quads=True)

    termLen = len(term)
    termBboxLen = max(clip.height, clip.width)
    termfontSize = termBboxLen/termLen
    f = termfontSize*2

    # clip = clip.rect

    validate = page.get_text("blocks", clip = clip + (-f, -f, f, f), flags=0)[0][4]
    flag = 0
    if not caseSensitive:
        flag = re.IGNORECASE

    matches = len(re.findall(f'{term}', validate, flags=flag)) > 0
    if fullMatch:
        matches = len(re.findall(f'\\b{term}\\b', validate))>0
    return matches

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