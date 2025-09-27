# generate_from_template.py
from docxtpl import DocxTemplate, RichText
import re

def parse_markdown_with_styles(markdown_text):
    """
    Parses markdown text with inline font-size and bold annotations and returns
    a list of dicts: [{'text': ..., 'bold': ..., 'size': ...}, ...]
    """
    styled_lines = []
    # Match (font-size: XX, bold: yes/no) anywhere in the line
    style_pattern = re.compile(r'\(font-size:\s*(\d+),\s*bold:\s*(yes|no)\)', re.IGNORECASE)

    for line in markdown_text.split('\n'):
        match = style_pattern.search(line)
        if match:
            size = int(match.group(1))
            bold = match.group(2).strip().lower() == 'yes'
            # Remove the style annotation from the line text
            clean_line = style_pattern.sub('', line).strip()
        else:
            # Default values if no annotation is present
            size = 12
            bold = False
            clean_line = line.strip()
        
        if clean_line:  # Only add non-empty lines
            styled_lines.append({
                'text': clean_line + '\n',  # Keep the newline
                'bold': bold,
                'size': size
            })
    return styled_lines

def generate_final_document(styled_lines):
    """
    Loads the .docx template, fills it with the complete and accurate context,
    and saves the final, perfectly formatted document.
    """
    try:
        doc = DocxTemplate("procedure_template.docx")
        print("📄 Template 'procedure_template.docx' loaded successfully.")
    except Exception as e:
        print(f"❌ Error: Could not load 'procedure_template.docx'. Make sure it's in the same folder.")
        print(e)
        return

    # This context dictionary contains all variables needed for the template.
    # The keys perfectly match the placeholder list.
    context = {
        'category_title' : "Clemson Student Design",
        'document_title': "LoRa Car Radio Bring-Up Procedure",
        'document_id': "AE304196-001",
        'revision': "-",
        'document_date': "26 August 2025",

        'auth_table': [
            {'role': 'Originator:', 'title': '', 'name': 'D. Kaisner'},
            {'role': 'Approved By:', 'title': 'Engineering', 'name': 'D. Kaisner'},
            {'role': 'Approved By:', 'title': 'Quality Assurance', 'name': 'J. Finn'},
            {'role': 'Approved By:', 'title': 'Configuration Management', 'name': 'D. Franks'},
            {'role': 'Approved By:', 'title': 'Project Manager', 'name': 'T. Jandreau'},
        ],

        'rev_history': [
            {'rev': '-', 'desc': 'Initial Release', 'by': 'D. Kaisner', 'cr_num': 'SP-XXXX', 'date': '8/26/25'},
        ],

        'scope_text': ("""This documentation outlines the hardware specifications and priorities for the design work done by the Clemson Senior design team in creating the LoRa Base Station Evaluation Board and the LoRa Car Radio Evaluation Board. 
The purpose of these designs is to facilitate research into how LoRa radios can be used to create mesh networks for utilization on trains for various signaling and data monitoring applications. 
"""),

        'ref_docs': [
            {'num': 'AE304193-001', 'title': 'LoRa Radio Evaluation Design Hardware Requirements'},
            {'num': 'AE304194-001', 'title': 'LoRa Radio Evaluation Design Software Requirements'},
            {'num': 'AE304195-001', 'title': 'LoRa Car Radio Programming Procedure'},
            {'num': 'AE104079-001', 'title': 'Car Radio Schematic'},
            {'num': 'AE104077-001', 'title': 'Car Radio PCB'},
        ],

        'test_exec_text': (
            "The procedure is to be run in the document order. If any failure is observed, the test is to be halted, "
            "marked as a failure, and the issue remedied before restarting the test from the beginning."),

        'ds_reporting_text': (
            "The data sheets are indexed to the corresponding test procedure paragraphs. Record actual test data on the "
            "applicable entry line on the test datasheet. Where directed, verify a satisfactory completion of an "
            "action or satisfactory observation by marking a “P” (for pass) on theapplicable data sheet. If completion "
            "of an action or an observation is unsatisfactory, mark an 'F' (for fail) on theapplicable data sheet. "
            "No entry line should beis left blank. If the specific test does not apply, write 'N/A' for the entry."),

        'equipment_table': [
            {'item': '1', 'mfg': 'BK Precision', 'pn': '9202', 'desc': 'Benchtop Power Supply'},
            {'item': '2', 'mfg': 'BK Precision', 'pn': '2860A', 'desc': 'Multimeter'},
            {'item': '3', 'mfg': 'Aeronix', 'pn': 'AE10XXXX-001', 'desc': 'Power Cable'},
            {'item': '4', 'mfg': 'Segger', 'pn': 'J-Link', 'desc': 'JTAG Programmer'},
            {'item': '5', 'mfg': 'Any', 'pn': 'Windows', 'desc': 'Test PC with programming software and firmware'},
            {'item': '6', 'mfg': 'Adafruit', 'pn': '954', 'desc': 'USB to TTL Serial Cable'},
            {'item': '7', 'mfg': 'Keysight', 'pn': 'DSO2024A', 'desc': 'Oscilloscope'},
        ],

        'ai_gen_revision' : "gemini-2.5-pro v1.0",

        'ds_date': '', 'ds_tester': '', 'ds_part_num': '', 'ds_serial_num': '',

        'datasheet_rows': [
            {'section': '4.1.1', 'desc': 'Visual Inspection', 'expected': 'Pass', 'obs': '', 'pf': ''},
            {'section': '4.2.2.a', 'desc': 'Ground Net Check', 'expected': 'Connected', 'obs': '', 'pf': ''},
            {'section': '4.2.3.a', 'desc': 'PWR_JACK not shorted', 'expected': 'Open', 'obs': '', 'pf': ''},
            # ... Add all other datasheet rows here
        ],
    }

    # Create the RichText object for the main procedure.
    # The AI will generate this content in the future.
    rt = RichText()
    for i in styled_lines:
        rt.add(i['text'], bold=i['bold'], size=i['size'])
    context['procedure_rt'] = rt

    # --- Render and Save ---
    print("   -> Filling template with data...")
    doc.render(context)
    output_filename = "Generated_Procedure.docx"
    try:
        doc.save(output_filename)
        print(f"✅ Success! Document saved as '{output_filename}'")
    except Exception as e:
        print(f"❌ Error saving the document: {e}")


if __name__ == "__main__":
    generate_final_document()