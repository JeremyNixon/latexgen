import tarfile
import gzip
import json
import os
import tempfile
import shutil
import requests

CONTEXT_LENGTH_APPROX_CHARS = 3000

def process_tarball(tar_filename, jsonl_filename):
    # Create a temporary directory to hold the initial tar extraction
    temp_dir_initial = tempfile.mkdtemp()
    
    # Open the tar file and extract it to the initial temporary directory
    with tarfile.open(tar_filename, 'r') as tar:
        tar.extractall(path=temp_dir_initial)
    
    # Assume the first directory is the one containing all .gz files
    root_folder = os.path.join(temp_dir_initial, os.listdir(temp_dir_initial)[0])
    
    # Open the output .jsonl file
    with open(jsonl_filename, 'w') as jsonl_out:
        # Loop through each item in the root folder
        for item in os.listdir(root_folder):
            item_filepath = os.path.join(root_folder, item)
            
            # Skip if the item is a directory
            if os.path.isdir(item_filepath):
                continue
            
            # Create a temporary directory to extract the .gz file
            temp_dir_extract = tempfile.mkdtemp()
            
            # Extract .gz file to temporary directory
            with gzip.open(item_filepath, 'rb') as f_in:
                extracted_dir = os.path.join(temp_dir_extract, item.replace('.gz', ''))
                os.mkdir(extracted_dir)
                try:
                    with tarfile.open(fileobj=f_in, mode='r|') as tar:
                        tar.extractall(path=extracted_dir)
                except:
                    print ("ERROR READING GZ", f_in)
                    continue
            
            # Recursively find all .tex files in the extracted directory
            for root, _, files in os.walk(extracted_dir):
                for file in files:
                    if file.endswith('.tex'):
                        tex_filepath = os.path.join(root, file)
                        try:
                            with open(tex_filepath, 'r', encoding='utf-8') as f_in:
                                content = ""
                                for indiv_line_in_content in f_in.readlines():
                                    new_content = content + indiv_line_in_content
                                    if len(new_content) > CONTEXT_LENGTH_APPROX_CHARS:
                                        json_line = json.dumps({'text': content})
                                        jsonl_out.write(json_line + '\n')
                                        content = indiv_line_in_content
                                    else: 
                                        content = new_content
                                if content:
                                    json_line = json.dumps({'text': content})
                                    jsonl_out.write(json_line + '\n')

                        except:
                            print ("ERROR READING TEX", tex_filepath)
                            continue
            
            # Clean up temporary extraction directory
            shutil.rmtree(temp_dir_extract)
            
    # Clean up initial extraction directory
    shutil.rmtree(temp_dir_initial)

if __name__ == '__main__':
    tar_filename = 'src/arXiv_src_0002_001.tar'  # Replace with the path to your .tar file
    jsonl_filename = 'datasets/arXiv_src_0002_001_context3k.jsonl'  # Replace with the desired output .jsonl filename
    process_tarball(tar_filename, jsonl_filename)
