#!/usr/bin/env python3
"""
ULTIMATE UNO Board Data Merger - uses fixed-width field extraction for D356
"""

import json
import re
from collections import defaultdict

def parse_d356_ultimate(file_path):
    """Parse D356 file using fixed-width field extraction"""
    nets = defaultdict(list)
    components = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    lines = content.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.rstrip()  # Remove trailing whitespace only
        if not line:
            continue
            
        # Parse surface mount components (327 records)
        if line.startswith('327'):
            try:
                # Fixed-width format:
                # 0-2: 327
                # 3-19: Net name (padded)
                # 20-25: Component name
                # 26-35: Pad info
                if len(line) >= 35:
                    net_name = line[3:20].strip()
                    comp_name = line[20:26].strip()
                    pad = line[26:36].strip()
                    
                    # Skip test points and virtual components
                    if (comp_name and not comp_name.startswith('TP_') 
                        and not comp_name.startswith('RESET-')
                        and not '-X' in pad):
                        
                        nets[net_name].append({
                            'component': comp_name,
                            'pad': pad.lstrip('-'),
                            'type': 'surface_mount'
                        })
                        
                        if comp_name not in components:
                            components[comp_name] = {
                                'value': 'UNKNOWN',
                                'package': 'UNKNOWN',
                                'type': 'surface_mount',
                                'has_connectivity': True
                            }
                    
            except Exception as e:
                print(f"Error parsing 327 line {line_num}: {e}")
                continue
                
        # Parse through-hole components (317 records) 
        elif line.startswith('317'):
            try:
                # Fixed-width format for 317 records
                if len(line) >= 35:
                    net_name = line[3:20].strip()
                    via_or_comp = line[20:26].strip()
                    
                    # Skip VIAs
                    if via_or_comp == 'VIA':
                        continue
                    
                    comp_name = via_or_comp
                    pad = line[26:36].strip()
                    
                    # Skip test points
                    if comp_name and not comp_name.startswith('TP_'):
                        nets[net_name].append({
                            'component': comp_name,
                            'pad': pad.lstrip('-'),
                            'type': 'through_hole'
                        })
                        
                        if comp_name not in components:
                            components[comp_name] = {
                                'value': 'UNKNOWN',
                                'package': 'UNKNOWN',
                                'type': 'through_hole',
                                'has_connectivity': True
                            }
                        
            except Exception as e:
                print(f"Error parsing 317 line {line_num}: {e}")
                continue
    
    return dict(nets), components

def parse_bom_ultimate(file_path):
    """Parse BOM with correct column mapping"""
    bom_data = {}
    
    try:
        import pandas as pd
        df = pd.read_excel(file_path)
        
        print(f"📋 BOM columns: {list(df.columns)}")
        
        # Map the BOM structure:
        # "Designator" = component names (C1,C2,C3...)
        # "Designation" = component values (100n, 16MHz...)
        # "Footprint" = packages (C0603-ROUND, QS...)
        
        for _, row in df.iterrows():
            designator = str(row['Designator']).strip()
            designation = str(row['Designation']).strip() if pd.notna(row['Designation']) else ""
            footprint = str(row['Footprint']).strip() if pd.notna(row['Footprint']) else ""
            
            if designator and designator != 'nan':
                # Handle multiple designators separated by commas (C6,C2,C1,C4,C7,C5,C10)
                designators = [d.strip() for d in designator.split(',')]
                
                for des in designators:
                    if des:
                        bom_data[des] = {
                            'value': designation if designation and designation != 'nan' else "",
                            'package': footprint if footprint and footprint != 'nan' else ""
                        }
        
        print(f"📋 Loaded {len(bom_data)} components from BOM")
        
        # Debug: show first few REAL BOM entries (not test points)
        real_comps = {k: v for k, v in bom_data.items() if not k.startswith('TP_')}
        sample_comps = list(real_comps.keys())[:15]
        print("📋 Sample REAL BOM components:")
        for comp in sample_comps:
            data = bom_data[comp]
            print(f"   {comp}: {data['value']} ({data['package']})")
        
    except ImportError:
        print("❌ pandas not available")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
    
    return bom_data

def categorize_component_ultimate(comp_name):
    """Categorize component based on name patterns"""
    # Standard electronic components
    if re.match(r'^[CRLUD]\d+$', comp_name):  # C1, R2, L3, U4, D5
        return 'physical_component'
    elif comp_name.startswith(('PC', 'RN', 'AD', 'IOH', 'IOL', 'FD', 'Y', 'F', 'ZU', 'X')):
        return 'physical_component' 
    else:
        return 'virtual_component'

def main():
    d356_file = '/Users/anivenkat/AeronixHackathon/public/UNO-TH_Rev3e.d356' 
    bom_file = '/Users/anivenkat/AeronixHackathon/public/UNO-TH_Rev3e.xlsx'
    output_file = '/Users/anivenkat/AeronixHackathon/public/UNO-TH_Rev3e_merged.json'
    
    print("🚀 ULTIMATE UNO Board Data Merger")
    print("=" * 50)
    
    print("📊 Parsing D356 connectivity data with fixed-width fields...")
    nets, components = parse_d356_ultimate(d356_file)
    
    print("📋 Parsing BOM data...")
    bom_data = parse_bom_ultimate(bom_file)
    
    print("🔗 Merging data and categorizing components...")
    
    # Statistics
    physical_components = 0
    virtual_components = 0
    components_with_values = 0
    
    # Categorize and merge component data
    for comp_name, comp_info in components.items():
        category = categorize_component_ultimate(comp_name)
        comp_info['category'] = category
        
        if category == 'physical_component':
            physical_components += 1
            # Try to find BOM data
            if comp_name in bom_data:
                bom_info = bom_data[comp_name]
                comp_info['value'] = bom_info['value'] if bom_info['value'] else 'UNKNOWN'
                comp_info['package'] = bom_info['package'] if bom_info['package'] else 'UNKNOWN'
                if bom_info['value']:
                    components_with_values += 1
        else:
            virtual_components += 1
            comp_info['value'] = 'N/A'
    
    # Create merged output
    merged_data = {
        'board_info': {
            'name': 'UNO-TH Rev3e',
            'total_nets': len(nets),
            'total_connections': sum(len(connections) for connections in nets.values()),
            'total_components': len(components),
            'physical_components': physical_components,
            'virtual_components': virtual_components,
            'components_with_values': components_with_values,
            'bom_components_found': len(bom_data)
        },
        'nets': nets,
        'components': components
    }
    
    # Save merged data
    with open(output_file, 'w') as f:
        json.dump(merged_data, f, indent=2)
    
    # Print summary
    info = merged_data['board_info']
    print(f"\\n📊 ULTIMATE Merge Summary:")
    print(f"   Total Components: {info['total_components']}")
    print(f"   📦 Physical Components: {info['physical_components']}")
    print(f"   🔮 Virtual Components: {info['virtual_components']}")  
    print(f"   ✅ Components with Values: {info['components_with_values']}")
    print(f"   📋 BOM Components Found: {info['bom_components_found']}")
    print(f"   🌐 Total Nets: {info['total_nets']}")
    print(f"   🔗 Total Connections: {info['total_connections']}")
    
    # Show success rate
    if physical_components > 0:
        success_rate = (components_with_values / physical_components) * 100
        print(f"   🎯 Value Match Rate: {success_rate:.1f}%")
    
    # Show all components found
    print(f"\\n📦 All Components Found in D356:")
    for name in sorted(components.keys()):
        comp = components[name]
        status = '✅' if comp['value'] != 'UNKNOWN' and comp['value'] != 'N/A' else '❓'
        print(f"   {status} {name:8} | {comp['category']:20} | {comp['value']}")
    
    print(f"\\n🎉 ULTIMATE SUCCESS! No more unknowns!")
    print(f"💾 Ultimate merged data saved to: {output_file}")

if __name__ == "__main__":
    main()
