#!/usr/bin/env python3
"""
IPC File Parser - Enhanced Version
Removes coordinates, rotation, soldermask fields, and drilling hole identifier from IPC-D-356A files
Provides options to keep or remove pad dimensions
"""

import re
import sys
import os
import argparse

def parse_ipc_file(input_file_path, output_file_path=None, keep_pad_dimensions=True):
    if not os.path.exists(input_file_path):
        print(f"Error: Input file '{input_file_path}' not found.")
        return False

    if output_file_path is None:
        base_name = os.path.splitext(input_file_path)[0]
        suffix = "_parsed"
        output_file_path = f"{base_name}{suffix}.ipc"
    
    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()
        
        cleaned_lines = []
        surface_mount_count = 0
        through_hole_count = 0
        
        for line in lines:
            line = line.rstrip('\n\r')
            
            # Process comment lines and parameter lines as-is
            if line.startswith('C ') or line.startswith('P ') or line.startswith('999'):
                cleaned_lines.append(line)
                continue
            
            # Process surface mount test points (327 prefix)
            if line.startswith('327'):
                cleaned_line = process_surface_mount_line(line, keep_pad_dimensions)
                cleaned_lines.append(cleaned_line)
                surface_mount_count += 1
                continue
            
            # Process through-hole test points (317 prefix)
            if line.startswith('317'):
                cleaned_line = process_through_hole_line(line, keep_pad_dimensions)
                cleaned_lines.append(cleaned_line)
                through_hole_count += 1
                continue
            
            # Keep any other lines as-is
            cleaned_lines.append(line)
        
        # Write cleaned content to output file
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for line in cleaned_lines:
                outfile.write(line + '\n')
        
        print(f"Successfully processed IPC file.")
        print(f"Input:  {input_file_path}")
        print(f"Output: {output_file_path}")
        print(f"Total lines processed: {len(lines)}")
        print(f"Surface mount points: {surface_mount_count}")
        print(f"Through-hole points: {through_hole_count}")
        print(f"Pad dimensions: {'kept' if keep_pad_dimensions else 'removed'}")
        
        return True
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return False

def process_surface_mount_line(line, keep_pad_dimensions=True):
    """
    Process surface mount test point lines (327 prefix)
    Format: 327<net_name> <component> <pin> PA01X <x_coord>Y <y_coord>X<x_size>Y<y_size>R<rotation> S<soldermask>
    Note: The format actually has spaces like "PA01X 029311Y 015709X0709Y0315R270 S0"
    """
    
    # Use regex to parse the entire line accounting for spaces
    pattern = r'^(327\S+)\s+(\S+)\s+(\S+)\s+PA01X\s+\d+Y\s+\d+X(\d+)Y(\d+)R\d+\s+S\d+'
    match = re.match(pattern, line)
    
    if match:
        net_name = match.group(1)  # 327<net_name>
        component = match.group(2)
        pin = match.group(3)
        x_size = match.group(4)
        y_size = match.group(5)
        
        if keep_pad_dimensions:
            # Keep pad dimensions but remove coordinates, rotation, and soldermask
            cleaned_line = f"{net_name} {component} {pin} PA01X{x_size}Y{y_size}"
        else:
            # Remove everything except basic info
            cleaned_line = f"{net_name} {component} {pin} PA01"
            
        return cleaned_line
    else:
        # Fallback parsing - if regex fails, just keep the basic structure
        parts = line.split()
        if len(parts) >= 3:
            cleaned_line = f"{parts[0]} {parts[1]} {parts[2]} PA01"
            return cleaned_line
        else:
            return line

def process_through_hole_line(line, keep_pad_dimensions=True):
    """
    Process through-hole test point lines (317 prefix)
    Format: 317<net_name> <component> <pin> D<drill_size>PA00X <x_coord>Y <y_coord>X0000 S<soldermask>
    Note: Format has spaces like "D0701UA00X 042950Y 047736X0000          S0"
    """
    
    # Parse with regex to extract drill size if we want to keep dimensions
    if keep_pad_dimensions:
        pattern = r'^(317\S+)\s+(\S+)\s+(\S+)\s+D(\d+).*?PA00X\s+\d+Y\s+\d+X\d+.*?S\d+'
        match = re.match(pattern, line)
        
        if match:
            net_name = match.group(1)
            component = match.group(2) 
            pin = match.group(3)
            drill_size = match.group(4)
            
            # Keep drill size but remove coordinates and soldermask
            cleaned_line = f"{net_name} {component} {pin} D{drill_size}PA00"
            return cleaned_line
    
    # Default: just keep basic info
    parts = line.split()
    if len(parts) >= 3:
        cleaned_line = f"{parts[0]} {parts[1]} {parts[2]} PA00"
        return cleaned_line
    else:
        return line

def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(description="Enhanced IPC-D-356A file parser.")
    parser.add_argument("input_file", help="Path to the input IPC file.")
    parser.add_argument("-o", "--output_file", help="Path to the output file. If not provided, it will be auto-generated.", default=None)
    parser.add_argument("--remove-dims", action="store_false", dest="keep_pad_dimensions", help="Remove pad dimensions from the output.")
    
    args = parser.parse_args()

    print(f"Processing input file: {args.input_file}")
    if args.output_file:
        print(f"Output will be saved to: {args.output_file}")
    print(f"Pad dimensions will be: {'kept' if args.keep_pad_dimensions else 'removed'}")
    
    success = parse_ipc_file(args.input_file, args.output_file, args.keep_pad_dimensions)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()