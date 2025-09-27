#!/usr/bin/env python3
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# DATA MODELS 

class ComponentType(str, Enum):
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    TRANSISTOR = "transistor"
    IC = "ic"
    CONNECTOR = "connector"
    CRYSTAL = "crystal"
    SWITCH = "switch"
    LED = "led"
    FUSE = "fuse"
    TRANSFORMER = "transformer"
    VIA = "via"
    TEST_POINT = "test_point"
    OTHER = "other"

class NetClass(str, Enum):
    POWER = "power"
    GROUND = "ground"
    SIGNAL = "signal"
    CLOCK = "clock"
    DIFFERENTIAL = "differential"
    HIGH_SPEED = "high_speed"
    ANALOG = "analog"
    OTHER = "other"

@dataclass
class Component:
    reference: str
    value: Optional[str] = None
    package: Optional[str] = None
    footprint: Optional[str] = None
    part_number: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    component_type: ComponentType = ComponentType.OTHER
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    rotation: Optional[float] = None
    layer: Optional[str] = None

@dataclass
class NetConnection:
    net_name: str
    component_ref: str
    pin_number: str
    pin_name: Optional[str] = None
    access_type: Optional[str] = None
    drill_size: Optional[float] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None

@dataclass
class Net:
    net_name: str
    connections: List[NetConnection]
    net_class: Optional[NetClass] = None

@dataclass
class ParsedNetlist:
    file_path: str
    file_format: str
    parse_timestamp: datetime
    nets: List[Net]
    components: List[Component]
    metadata: Dict[str, Any]
    
    @property
    def total_nets(self) -> int:
        return len(self.nets)
    
    @property
    def total_nodes(self) -> int:
        return sum(len(net.connections) for net in self.nets)

# HELPER FUNCTIONS

def infer_component_type(reference: str) -> ComponentType:
    """Infer component type from reference designator"""
    if not reference:
        return ComponentType.OTHER
        
    ref_upper = reference.upper()
    
    type_map = {
        'R': ComponentType.RESISTOR,
        'C': ComponentType.CAPACITOR,
        'L': ComponentType.INDUCTOR,
        'D': ComponentType.DIODE,
        'Q': ComponentType.TRANSISTOR,
        'U': ComponentType.IC,
        'IC': ComponentType.IC,
        'J': ComponentType.CONNECTOR,
        'P': ComponentType.CONNECTOR,
        'X': ComponentType.CRYSTAL,
        'Y': ComponentType.CRYSTAL,
        'S': ComponentType.SWITCH,
        'SW': ComponentType.SWITCH,
        'LED': ComponentType.LED,
        'F': ComponentType.FUSE,
        'T': ComponentType.TRANSFORMER,
        'TP': ComponentType.TEST_POINT,
        'VIA': ComponentType.VIA,
        'PTH': ComponentType.TEST_POINT,
    }
    
    for prefix, comp_type in type_map.items():
        if ref_upper.startswith(prefix):
            return comp_type
    
    return ComponentType.OTHER

def infer_net_class(net_name: str) -> NetClass:
    """Infer net class from net name"""
    if not net_name:
        return NetClass.OTHER
        
    name_upper = net_name.upper()
    
    # Power nets
    if any(power in name_upper for power in ['VCC', 'VDD', 'VIN', '+5V', '+3V3', '+12V', 'VBAT', 'VREF']):
        return NetClass.POWER
    
    # Ground nets  
    if any(gnd in name_upper for gnd in ['GND', 'VSS', 'GROUND', 'EARTH']):
        return NetClass.GROUND
        
    # Clock signals
    if any(clk in name_upper for clk in ['CLK', 'CLOCK', 'OSC', 'XTAL']):
        return NetClass.CLOCK
        
    # Differential pairs
    if any(diff in name_upper for diff in ['_P', '_N', '+', '-']) and ('USB' in name_upper or 'DIFF' in name_upper):
        return NetClass.DIFFERENTIAL
        
    # High speed signals
    if any(hs in name_upper for hs in ['USB', 'ETHERNET', 'HDMI', 'PCIE']):
        return NetClass.HIGH_SPEED
        
    # Analog signals
    if any(analog in name_upper for analog in ['ADC', 'DAC', 'ANALOG', 'AREF', 'VREF']):
        return NetClass.ANALOG
    
    return NetClass.SIGNAL

# D356 PARSER

class D356Parser:
    """D356 test file format parser"""
    
    def __init__(self):
        self.format_name = "D356"
        self.NET_RECORD = "317"
        self.ACCESS_RECORD = "327"
        self.PARAMETER = "P"
        self.COMMENT = "C"
    
    def parse_file(self, file_path: Union[str, Path]) -> ParsedNetlist:
        """Parse D356 test file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"D356 file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        nets, components, metadata = self._parse_d356_content(content)
        
        return ParsedNetlist(
            file_path=str(file_path),
            file_format="D356",
            parse_timestamp=datetime.now(),
            nets=nets,
            components=components,
            metadata=metadata
        )
    
    def _parse_d356_content(self, content: str):
        """Parse D356 file content"""
        lines = content.strip().split('\n')
        nets_dict = {}
        components = {}
        metadata = {}
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            try:
                if line.startswith(self.NET_RECORD):
                    self._parse_net_record(line, nets_dict, components)
                elif line.startswith(self.ACCESS_RECORD):
                    self._parse_access_record(line, nets_dict, components)
                elif line.startswith(self.COMMENT):
                    self._parse_comment(line, metadata)
                elif line.startswith(self.PARAMETER):
                    self._parse_parameter(line, metadata)
            except Exception as e:
                print(f"Warning: Error parsing line {line_num}: {e}")
                continue
        
        # Convert to Net objects
        nets = []
        for net_name, connections in nets_dict.items():
            if connections:
                nets.append(Net(
                    net_name=net_name,
                    connections=connections,
                    net_class=infer_net_class(net_name)
                ))
        
        return nets, list(components.values()), metadata
    
    def _parse_net_record(self, line: str, nets_dict: Dict, components: Dict):
        """Parse D356 317 record"""
        try:
            data = line[3:].strip()
            parts = re.split(r'\s{2,}', data)
            
            if len(parts) < 2:
                return
            
            net_name = parts[0].strip()
            if not net_name:
                return
            
            if net_name not in nets_dict:
                nets_dict[net_name] = []
            
            second_field = parts[1].strip()
            
            if second_field == "VIA":
                # VIA record
                self._parse_via_record(net_name, parts[2:], nets_dict, components)
            else:
                # Component record
                self._parse_component_net_record(net_name, parts[1:], nets_dict, components)
                
        except Exception as e:
            print(f"Warning: Failed to parse net record: {e}")
    
    def _parse_via_record(self, net_name: str, drill_parts: List[str], nets_dict: Dict, components: Dict):
        """Parse VIA-based record"""
        if not drill_parts:
            return
            
        drill_info = ' '.join(drill_parts)
        pos_match = re.search(r'X([+-]?\d+)Y([+-]?\d+)', drill_info)
        
        if pos_match:
            try:
                x_pos = float(pos_match.group(1)) / 10000.0
                y_pos = float(pos_match.group(2)) / 10000.0
                
                via_ref = f"VIA_{net_name}_{len(nets_dict[net_name]) + 1}"
                
                connection = NetConnection(
                    net_name=net_name,
                    component_ref=via_ref,
                    pin_number="1",
                    access_type="via",
                    x_position=x_pos,
                    y_position=y_pos
                )
                
                nets_dict[net_name].append(connection)
                
                if via_ref not in components:
                    components[via_ref] = Component(
                        reference=via_ref,
                        component_type=ComponentType.VIA,
                        x_position=x_pos,
                        y_position=y_pos,
                        description=f"Via for {net_name}"
                    )
                    
            except (ValueError, TypeError):
                pass
    
    def _parse_component_net_record(self, net_name: str, comp_parts: List[str], nets_dict: Dict, components: Dict):
        """Parse component-based record"""
        if not comp_parts:
            return
            
        comp_pin_field = comp_parts[0].strip()
        comp_pin_match = re.match(r'([A-Z0-9]+)\s*-\s*(\w*)', comp_pin_field)
        
        if comp_pin_match:
            component_ref = comp_pin_match.group(1)
            pin_number = comp_pin_match.group(2) if comp_pin_match.group(2) else "1"
            
            connection = NetConnection(
                net_name=net_name,
                component_ref=component_ref,
                pin_number=pin_number,
                access_type="component_pin"
            )
            
            nets_dict[net_name].append(connection)
            
            if component_ref not in components:
                components[component_ref] = Component(
                    reference=component_ref,
                    component_type=infer_component_type(component_ref)
                )
    
    def _parse_access_record(self, line: str, nets_dict: Dict, components: Dict):
        """Parse D356 327 record"""
        try:
            data = line[3:].strip()
            parts = re.split(r'\s{2,}', data)
            
            if len(parts) < 2:
                return
            
            net_name = parts[0].strip()
            comp_pin_field = parts[1].strip()
            
            comp_pin_match = re.match(r'([A-Z0-9]+)\s*-\s*(\w*)', comp_pin_field)
            if comp_pin_match:
                component_ref = comp_pin_match.group(1)
                pin_number = comp_pin_match.group(2) if comp_pin_match.group(2) else "1"
                
                if net_name not in nets_dict:
                    nets_dict[net_name] = []
                
                connection = NetConnection(
                    net_name=net_name,
                    component_ref=component_ref,
                    pin_number=pin_number,
                    access_type="access_point"
                )
                
                nets_dict[net_name].append(connection)
                
                if component_ref not in components:
                    components[component_ref] = Component(
                        reference=component_ref,
                        component_type=infer_component_type(component_ref)
                    )
                    
        except Exception as e:
            print(f"Warning: Failed to parse access record: {e}")
    
    def _parse_comment(self, line: str, metadata: Dict):
        """Parse comment lines"""
        comment_text = line[1:].strip()
        if "Project Name" in comment_text:
            metadata['project_name'] = comment_text.split(':')[-1].strip()
        elif "Board Name" in comment_text:
            metadata['board_name'] = comment_text.split(':')[-1].strip()
        elif "Date" in comment_text:
            metadata['date'] = comment_text.split(':')[-1].strip()
    
    def _parse_parameter(self, line: str, metadata: Dict):
        """Parse parameter lines"""
        param_data = line[1:].strip()
        parts = param_data.split(None, 1)
        if len(parts) >= 2:
            metadata[f'param_{parts[0].lower()}'] = parts[1].strip()

# IPC PARSER

# IPC PARSER (ENHANCED)

class IPCParser:
    """IPC netlist/assembly test file parser with robust handling for tabular or CSV-like files."""

    def __init__(self):
        self.format_name = "IPC"

    def parse_file(self, file_path: Union[str, Path]) -> ParsedNetlist:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"IPC file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        nets, components, metadata = self._parse_ipc_content(content)

        return ParsedNetlist(
            file_path=str(file_path),
            file_format="IPC",
            parse_timestamp=datetime.now(),
            nets=nets,
            components=components,
            metadata=metadata
        )

    def _parse_ipc_content(self, content: str):
        """Parse IPC file content (whitespace-separated, CSV, or fixed-width)."""
        lines = content.strip().split('\n')
        nets_dict = {}
        components = {}
        metadata = {}

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith(('#', ';', '!')):
                # Comment or empty line
                continue

            # Try to parse metadata lines
            if ':' in line:
                key, value = map(str.strip, line.split(':', 1))
                metadata[key.lower().replace(' ', '_')] = value
                continue

            # Split line by whitespace (or tab)
            parts = re.split(r'\s+|,', line)
            if len(parts) < 3:
                continue  # Not enough info for net/component

            net_name = parts[0]
            comp_ref = parts[1]
            pin_number = parts[2]

            # Optional coordinates
            x_pos = float(parts[3]) if len(parts) > 3 and parts[3].replace('.', '', 1).isdigit() else None
            y_pos = float(parts[4]) if len(parts) > 4 and parts[4].replace('.', '', 1).isdigit() else None

            # Add to nets_dict
            if net_name not in nets_dict:
                nets_dict[net_name] = []

            conn = NetConnection(
                net_name=net_name,
                component_ref=comp_ref,
                pin_number=pin_number,
                access_type="ipc_point",
                x_position=x_pos,
                y_position=y_pos
            )
            nets_dict[net_name].append(conn)

            # Add component if not already present
            if comp_ref not in components:
                components[comp_ref] = Component(
                    reference=comp_ref,
                    component_type=infer_component_type(comp_ref),
                    x_position=x_pos,
                    y_position=y_pos
                )

        # Convert dicts to Net objects
        nets = [
            Net(net_name=net_name, connections=conns, net_class=infer_net_class(net_name))
            for net_name, conns in nets_dict.items()
        ]

        return nets, list(components.values()), metadata


# MAIN PARSING FUNCTION

def parse_your_files():
    """Parse both of your specific files"""
    print("PARSING YOUR PCB FILES")
    
    # Your file paths
    D356_FILE = "/Users/alaineperdomo/Desktop/IgniteHackathon/app/parser/UNO-TH_Rev3e.d356"
    IPC_FILE = "app/parser/Assembly Testpoint Report for Car-PCB1.ipc"
    
    results = {
        'd356_data': None,
        'ipc_data': None,
        'analysis': {},
        'errors': []
    }
    
    # Parse D356 file
    print(f"\n📁 Parsing D356 file: {D356_FILE}")
    print("-" * 50)
    try:
        if Path(D356_FILE).exists():
            d356_parser = D356Parser()
            d356_data = d356_parser.parse_file(D356_FILE)
            results['d356_data'] = d356_data
            
            print(f"SUCCESS: Parsed D356 file")
            print(f"   - Total nets: {len(d356_data.nets)}")
            print(f"   - Total components: {len(d356_data.components)}")
            
            # Show top nets
            sorted_nets = sorted(d356_data.nets, key=lambda x: len(x.connections), reverse=True)
            print(f"   - Top nets:")
            for net in sorted_nets[:5]:
                net_class = net.net_class.value if net.net_class else "unknown"
                print(f"     • {net.net_name}: {len(net.connections)} connections ({net_class})")
                
        else:
            error_msg = f"D356 file not found: {D356_FILE}"
            results['errors'].append(error_msg)
            print(f"ERROR: {error_msg}")
            
    except Exception as e:
        error_msg = f"Failed to parse D356 file: {e}"
        results['errors'].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    # Parse IPC file
    print(f"\nParsing IPC file: {Path(IPC_FILE).name}")
    print("-" * 50)
    try:
        if Path(IPC_FILE).exists():
            ipc_parser = IPCParser()
            ipc_data = ipc_parser.parse_file(IPC_FILE)
            results['ipc_data'] = ipc_data
            
            print(f"SUCCESS: Parsed IPC file")
            print(f"   - Total nets: {len(ipc_data.nets)}")
            print(f"   - Total components: {len(ipc_data.components)}")
            
            # Show top nets
            sorted_nets = sorted(ipc_data.nets, key=lambda x: len(x.connections), reverse=True)
            print(f"   - Top nets:")
            for net in sorted_nets[:5]:
                net_class = net.net_class.value if net.net_class else "unknown"
                print(f"     • {net.net_name}: {len(net.connections)} connections ({net_class})")
                
        else:
            error_msg = f"IPC file not found: {IPC_FILE}"
            results['errors'].append(error_msg)
            print(f"ERROR: {error_msg}")
            
    except Exception as e:
        error_msg = f"Failed to parse IPC file: {e}"
        results['errors'].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    # Analysis
    print(f"\nANALYSIS")
    print("-" * 50)
    
    all_components = []
    all_nets = []
    
    if results['d356_data']:
        all_components.extend(results['d356_data'].components)
        all_nets.extend(results['d356_data'].nets)
    
    if results['ipc_data']:
        all_components.extend(results['ipc_data'].components)
        all_nets.extend(results['ipc_data'].nets)
    
    if all_components or all_nets:
        # Component type breakdown
        component_types = {}
        for comp in all_components:
            comp_type = comp.component_type.value
            component_types[comp_type] = component_types.get(comp_type, 0) + 1
        
        print("Component Types:")
        for comp_type, count in sorted(component_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {comp_type}: {count}")
        
        # Net classes
        net_classes = {}
        for net in all_nets:
            net_class = net.net_class.value if net.net_class else "unknown"
            net_classes[net_class] = net_classes.get(net_class, 0) + 1
        
        print("\nNet Classes:")
        for net_class, count in sorted(net_classes.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {net_class}: {count}")
        
        # Test recommendations
        print(f"\nTEST RECOMMENDATIONS:")
        power_nets = [net for net in all_nets if net.net_class == NetClass.POWER]
        ground_nets = [net for net in all_nets if net.net_class == NetClass.GROUND]
        complex_nets = [net for net in all_nets if len(net.connections) > 2]
        
        print(f"   HIGH: Power supply tests ({len(power_nets)} nets)")
        print(f"   HIGH: Ground continuity tests ({len(ground_nets)} nets)")
        print(f"   MED: Signal continuity tests ({len(complex_nets)} multi-point nets)")
        
        results['analysis'] = {
            'total_components': len(all_components),
            'total_nets': len(all_nets),
            'component_types': component_types,
            'net_classes': net_classes,
            'power_nets': len(power_nets),
            'ground_nets': len(ground_nets),
            'complex_nets': len(complex_nets)
        }
    
    # Export results
    print(f"\nEXPORTING RESULTS")
    print("-" * 50)
    
    try:
        export_data = {}
        
        if results['d356_data']:
            # Convert dataclass to dict manually
            export_data['d356'] = {
                'file_path': results['d356_data'].file_path,
                'file_format': results['d356_data'].file_format,
                'parse_timestamp': results['d356_data'].parse_timestamp.isoformat(),
                'total_nets': results['d356_data'].total_nets,
                'total_nodes': results['d356_data'].total_nodes,
                'metadata': results['d356_data'].metadata,
                'nets': [
                    {
                        'net_name': net.net_name,
                        'net_class': net.net_class.value if net.net_class else None,
                        'connections': [
                            {
                                'component_ref': conn.component_ref,
                                'pin_number': conn.pin_number,
                                'access_type': conn.access_type,
                                'x_position': conn.x_position,
                                'y_position': conn.y_position
                            } for conn in net.connections
                        ]
                    } for net in results['d356_data'].nets
                ],
                'components': [
                    {
                        'reference': comp.reference,
                        'component_type': comp.component_type.value,
                        'value': comp.value,
                        'description': comp.description,
                        'x_position': comp.x_position,
                        'y_position': comp.y_position
                    } for comp in results['d356_data'].components
                ]
            }
        
        if results['ipc_data']:
            # Same for IPC data
            export_data['ipc'] = {
                'file_path': results['ipc_data'].file_path,
                'file_format': results['ipc_data'].file_format,
                'parse_timestamp': results['ipc_data'].parse_timestamp.isoformat(),
                'total_nets': results['ipc_data'].total_nets,
                'total_nodes': results['ipc_data'].total_nodes,
                'metadata': results['ipc_data'].metadata,
                'nets': [
                    {
                        'net_name': net.net_name,
                        'net_class': net.net_class.value if net.net_class else None,
                        'connections': [
                            {
                                'component_ref': conn.component_ref,
                                'pin_number': conn.pin_number,
                                'access_type': conn.access_type,
                                'x_position': conn.x_position,
                                'y_position': conn.y_position
                            } for conn in net.connections
                        ]
                    } for net in results['ipc_data'].nets
                ],
                'components': [
                    {
                        'reference': comp.reference,
                        'component_type': comp.component_type.value,
                        'value': comp.value,
                        'description': comp.description,
                        'x_position': comp.x_position,
                        'y_position': comp.y_position
                    } for comp in results['ipc_data'].components
                ]
            }
        
        export_data['analysis'] = results['analysis']
        export_data['errors'] = results['errors']
        
        with open('parsed_results.json', 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Results exported to 'parsed_results.json'")
        
    except Exception as e:
        print(f"Export failed: {e}")
    
  
    print("SUMMARY ")

    
    if results['d356_data']:
        print(f"Arduino UNO D356: {len(results['d356_data'].nets)} nets, {len(results['d356_data'].components)} components")
    else:
        print("Arduino UNO D356: Failed to parse")
    
    if results['ipc_data']:
        print(f"Car PCB IPC: {len(results['ipc_data'].nets)} nets, {len(results['ipc_data'].components)} components")
    else:
        print("Car PCB IPC: Failed to parse")
    
    if results['errors']:
        print(f"Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"   • {error}")
    
    return results

if __name__ == "__main__":
    parse_your_files()