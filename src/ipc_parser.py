#!/usr/bin/env python3
"""
IPC File Parser - JSON Output Version
Parses IPC-D-356A files and outputs data in JSON format organized by nets
"""

import re
import sys
import os
import json
from collections import defaultdict

def parse_ipc_to_json(input_file_path, output_file_path=None):
    """
    Parse IPC file and output data in JSON format organized by nets
    
    Args:
        input_file_path (str): Path to input IPC file
        output_file_path (str): Path to output JSON file (optional)
    
    Returns:
        dict: Parsed data organized by nets
    """
    
    if not os.path.exists(input_file_path):
        print(f"Error: Input file '{input_file_path}' not found.")
        return None
    
    # If no output file specified, create one based on input file name
    if output_file_path is None:
        base_name = os.path.splitext(input_file_path)[0]
        output_file_path = f"{base_name}_parsed.json"
    
    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()
        
        # Dictionary to organize data by nets
        nets_data = defaultdict(list)
        surface_mount_count = 0
        through_hole_count = 0
        
        for line in lines:
            line = line.rstrip('\n\r')
            
            # Skip comment lines, parameter lines, and end marker
            if line.startswith('C ') or line.startswith('P ') or line.startswith('999') or not line.strip():
                continue
            
            # Process surface mount test points (327 prefix)
            if line.startswith('327'):
                connection_data = parse_surface_mount_line(line)
                if connection_data:
                    nets_data[connection_data['net']].append({
                        'component': connection_data['component'],
                        'pin': connection_data['pin']
                    })
                    surface_mount_count += 1
                continue
            
            # Process through-hole test points (317 prefix)
            if line.startswith('317'):
                connection_data = parse_through_hole_line(line)
                if connection_data:
                    nets_data[connection_data['net']].append({
                        'component': connection_data['component'],
                        'pin': connection_data['pin']
                    })
                    through_hole_count += 1
                continue
        
        # Convert to the desired JSON format
        result = {
            "nets": [
                {
                    "name": net_name,
                    "connections": connections
                }
                for net_name, connections in sorted(nets_data.items())
            ]
        }
        
        # Write JSON data to output file
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(result, outfile, indent=2, ensure_ascii=False)
        
        print(f"Successfully processed IPC file to JSON format.")
        print(f"Input:  {input_file_path}")
        print(f"Output: {output_file_path}")
        print(f"Total lines processed: {len(lines)}")
        print(f"Surface mount points: {surface_mount_count}")
        print(f"Through-hole points: {through_hole_count}")
        print(f"Total nets found: {len(nets_data)}")
        print(f"Total connections: {sum(len(connections) for connections in nets_data.values())}")
        
        return result
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

def parse_surface_mount_line(line):
    """
    Parse surface mount test point lines (327 prefix) and extract data
    Excludes coordinates, rotation, soldermask, and pad dimensions
    Format: 327<net_name> <component> <pin> PA01X <x_coord>Y <y_coord>X<x_size>Y<y_size>R<rotation> S<soldermask>
    
    Returns:
        dict: Parsed connection data (net, component, pin only) or None if parsing fails
    """
    
    # Use regex to parse the basic components
    pattern = r'^327(\S+)\s+(\S+)\s+(\S+)\s+'
    match = re.match(pattern, line)
    
    if match:
        net_name = match.group(1)  # Net name without 327 prefix
        component = match.group(2)
        pin = match.group(3)
        
        return {
            'net': net_name,
            'component': component,
            'pin': pin
        }
    else:
        # Fallback parsing - try to extract basic info
        parts = line.split()
        if len(parts) >= 3:
            # Extract net name (remove 327 prefix)
            net_name = parts[0][3:] if parts[0].startswith('327') else parts[0]
            return {
                'net': net_name,
                'component': parts[1],
                'pin': parts[2]
            }
        else:
            return None

def parse_through_hole_line(line):
    """
    Parse through-hole test point lines (317 prefix) and extract data
    Excludes coordinates, drill hole size, and soldermask
    Format: 317<net_name> <component> <pin> D<drill_size>PA00X <x_coord>Y <y_coord>X0000 S<soldermask>
    
    Returns:
        dict: Parsed connection data (net, component, pin only) or None if parsing fails
    """
    
    # Use regex to parse the basic components
    pattern = r'^317(\S+)\s+(\S+)\s+(\S+)\s+'
    match = re.match(pattern, line)
    
    if match:
        net_name = match.group(1)  # Net name without 317 prefix
        component = match.group(2)
        pin = match.group(3)
        
        return {
            'net': net_name,
            'component': component,
            'pin': pin
        }
    else:
        # Fallback parsing - try to extract basic info
        parts = line.split()
        if len(parts) >= 3:
            # Extract net name (remove 317 prefix)
            net_name = parts[0][3:] if parts[0].startswith('317') else parts[0]
            return {
                'net': net_name,
                'component': parts[1],
                'pin': parts[2]
            }
        else:
            return None

def main():
    """Main function with hardcoded input/output file paths"""
    
    # Hardcoded file paths
    input_file = "/Users/anivenkat/AeronixHackathon/public/Assembly Testpoint Report for Car-PCB1.ipc"
    output_file = "/Users/anivenkat/AeronixHackathon/public/Assembly Testpoint Report for Car-PCB1_parsed.json"
    
    print(f"Processing hardcoded input file: {input_file}")
    print(f"Output will be saved to: {output_file}")
    print("Converting IPC data to JSON format organized by nets...")
    
    result = parse_ipc_to_json(input_file, output_file)
    
    if result is None:
        print("❌ Failed to process IPC file")
        sys.exit(1)
    else:
        print("✅ Successfully converted IPC to JSON format")
        
        # Display some sample data
        if result["nets"]:
            print("\n📊 Sample of parsed data:")
            for i, net in enumerate(result["nets"][:3]):  # Show first 3 nets
                print(f"  Net '{net['name']}': {len(net['connections'])} connections")
                if net['connections']:
                    conn = net['connections'][0]  # Show first connection
                    print(f"    Example: {conn['component']} pin {conn['pin']}")
            
            if len(result["nets"]) > 3:
                print(f"  ... and {len(result['nets']) - 3} more nets")

if __name__ == "__main__":
    main()
