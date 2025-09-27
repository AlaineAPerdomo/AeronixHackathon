import os
import json
import re
from pathlib import Path
from docxtpl import DocxTemplate, RichText
from google import genai
from google.genai import types
from dotenv import load_dotenv
import docx
from arduino_parse import parse_board_data
from radio_parse import parse_radio_data

# --- CONFIGURATION ---
SCRIPT_DIR = Path(__file__).parent.resolve()
load_dotenv(SCRIPT_DIR / ".env")

# --- SCHEMA DEFINITION ---
# (The GEMINI_OUTPUT_SCHEMA remains the same)
GEMINI_OUTPUT_SCHEMA = genai.types.Schema(
    type=genai.types.Type.OBJECT,
    required=[
        "category_title", "document_title", "document_id", "revision", "document_date",
        "auth_table", "rev_history", "scope_text", "ref_docs", "test_exec_text",
        "ds_reporting_text", "equipment_table", "procedure_rt_markdown", "datasheet_rows"
    ],
    properties={
        "category_title": genai.types.Schema(type=genai.types.Type.STRING),
        "document_title": genai.types.Schema(type=genai.types.Type.STRING),
        "document_id": genai.types.Schema(type=genai.types.Type.STRING),
        "revision": genai.types.Schema(type=genai.types.Type.STRING),
        "document_date": genai.types.Schema(type=genai.types.Type.STRING),
        "auth_table": genai.types.Schema(
            type=genai.types.Type.ARRAY,
            items=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "role": genai.types.Schema(type=genai.types.Type.STRING),
                    "title": genai.types.Schema(type=genai.types.Type.STRING),
                    "name": genai.types.Schema(type=genai.types.Type.STRING),
                }
            )
        ),
        "rev_history": genai.types.Schema(
            type=genai.types.Type.ARRAY,
            items=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "rev": genai.types.Schema(type=genai.types.Type.STRING),
                    "desc": genai.types.Schema(type=genai.types.Type.STRING),
                    "by": genai.types.Schema(type=genai.types.Type.STRING),
                    "cr_num": genai.types.Schema(type=genai.types.Type.STRING),
                    "date": genai.types.Schema(type=genai.types.Type.STRING),
                }
            )
        ),
        "scope_text": genai.types.Schema(type=genai.types.Type.STRING),
        "ref_docs": genai.types.Schema(
            type=genai.types.Type.ARRAY,
            items=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "num": genai.types.Schema(type=genai.types.Type.STRING),
                    "title": genai.types.Schema(type=genai.types.Type.STRING),
                }
            )
        ),
        "test_exec_text": genai.types.Schema(type=genai.types.Type.STRING),
        "ds_reporting_text": genai.types.Schema(type=genai.types.Type.STRING),
        "equipment_table": genai.types.Schema(
            type=genai.types.Type.ARRAY,
            items=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "item": genai.types.Schema(type=genai.types.Type.STRING),
                    "mfg": genai.types.Schema(type=genai.types.Type.STRING),
                    "pn": genai.types.Schema(type=genai.types.Type.STRING),
                    "desc": genai.types.Schema(type=genai.types.Type.STRING),
                }
            )
        ),
        "procedure_rt_markdown": genai.types.Schema(
            type=genai.types.Type.STRING,
            description="The main procedure text. Each line must include an inline style annotation, e.g., '1. Step one (font-size: 12, bold: no)'."
        ),
        "datasheet_rows": genai.types.Schema(
            type=genai.types.Type.ARRAY,
            items=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "section": genai.types.Schema(type=genai.types.Type.STRING),
                    "desc": genai.types.Schema(type=genai.types.Type.STRING),
                    "expected": genai.types.Schema(type=genai.types.Type.STRING),
                }
            )
        )
    }
)


def read_file_content(filepath):
    """Reads content from various file types, specifically handling .docx."""
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"⚠️ Warning: File not found at {filepath}")
        return ""
    try:
        if filepath.suffix == ".docx":
            doc = docx.Document(filepath)
            full_text = [para.text for para in doc.paragraphs]
            return '\n'.join(full_text)
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        print(f"❌ Error reading file {filepath}: {e}")
        return ""


def get_ai_generated_context(bom_content):
    """Calls the Gemini API or loads from cache to get the structured context data."""
    cache_file = SCRIPT_DIR / "api_response_cache.json"
    if cache_file.exists():
        print(f"✅ Found cache file. Loading response from '{cache_file.name}'...")
        with open(cache_file, 'r') as f:
            return json.load(f)

    print("ℹ️ No cache file found. Calling Gemini API...")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model_name = "gemini-2.5-pro"

    # <-- NEW, IMPROVED PROMPT -->
    prompt = f"""
    You are an expert test procedure writer for an aerospace and defense company, tasked with creating a comprehensive bring-up procedure for a new piece of hardware. Your output MUST be a single JSON object that strictly adheres to the provided JSON schema.

    You will be given a Bill of Materials (BOM) in CSV format and a Testpoint Report file. Use these files to generate the content for the test procedure. The final document should be similar in style and structure to a formal hardware test procedure.

    **Input Files Analysis:**

    1.  **BOM (CSV Format):** This file lists all the components on the board. Pay attention to integrated circuits (like microcontrollers), connectors, LEDs, and crystals to understand the board's functionality. The 'Designator' and 'Designation' columns are most important.
    2.  **Testpoint Report (.d356 Format):** This file contains net names and their corresponding test points (e.g., `TP_5V0`, `GND_TP0`, `TP_TX0`). This is your primary source for creating specific, actionable test steps.

    **Procedure Generation Instructions:**

    Based on your analysis of the input files, create the main procedure steps in the `procedure_rt_markdown` field. The procedure must include the following sections:

    1.  **4.1 Visual Inspection:**
        * Create a standard step to visually inspect the PCBA for any obvious defects (e.g., component damage, poor soldering, correct component placement).

    2.  **4.2 Power System Checks:**
        * Identify all main voltage rails and ground nets from the Testpoint Report (e.g., nets named `+5V`, `+3V3`, `GND`).
        * Create a sub-section for continuity checks. Generate a step to verify continuity from the power input connector pins to the identified ground nets using specific test points.
        * Create a sub-section for short checks. For each identified voltage rail, generate a step to measure resistance between that rail's test point and a ground test point, expecting an open circuit.
        * Create a sub-section for voltage verification. After applying power, generate a step for each voltage rail to measure the voltage at its test point and verify it's within an acceptable tolerance (e.g., +/- 5%).

    3.  **4.3 Firmware Programming:**
        * Identify the main microcontroller from the BOM (e.g., ATmega).
        * Identify the programming header from the BOM and Testpoint Report (e.g., "ICSP").
        * Create a step instructing the user to connect a programmer to the appropriate header and flash the firmware.

    4.  **4.4 Functional Verification:**
        * **Power-On Current:** Create a step to measure the UUT's current draw after power-on and check if it's within an expected range (e.g., < 200mA).
        * **On-board LED:** Identify any LEDs from the BOM (e.g., 'ON0'). Create a step to verify this LED illuminates upon power-up.
        * **Serial Communication:** Identify UART test points from the Testpoint Report (e.g., `TP_TX0`, `TP_RX0`). Create steps to connect a serial terminal and verify a welcome message or boot-up log is printed. Use standard serial parameters (Baud Rate: 115200, Parity: None, Stop Bits: 1).
        * **Built-in Self Test (BIST):** Create steps to trigger hypothetical built-in tests via the serial console (e.g., entering commands like `bit.cpu`, `bit.ram`) and verify a "Pass" response.

    **Datasheet Table Generation (`datasheet_rows`):**

    * For every single verification step you created in the procedure (e.g., "Check for solder bridges", "Measure +5V rail", "Verify LED illuminates"), create a corresponding entry in the `datasheet_rows` array.
    * The `section` field should reference the procedure step number (e.g., "4.2.3.a").
    * The `desc` field should be a concise summary of the check.
    * The `expected` field should state the expected result (e.g., "No defects", "Open circuit", "+5V +/- 5%", "LED On", "Pass").

    **General Instructions:**

    * **Document Metadata:** Populate fields like `document_title`, `document_id`, and `revision` with plausible information based on the input file names (e.g., "UNO-TH Rev3e Bring-Up Procedure").
    * **Styling:** Strictly adhere to the styling instructions provided below for the `procedure_rt_markdown` field.

    **Important Styling Instructions for the 'procedure_rt_markdown' field:**
    - For every single line, you MUST specify the font size and bold status using the format: `(font-size: [size], bold: [yes/no])`
    - For lists and sub-lists, use leading spaces to indicate indentation. Use two spaces for each level of indentation.
    - Example Heading: `4.1 Visual Inspection (font-size: 14, bold: yes)`
    - Example List: `1. Visually inspect the PCBA. (font-size: 12, bold: no)`
    - Example Sub-List: `  a. Check for solder bridges. (font-size: 12, bold: no)`
    

    **Analyze the following input files:**
    --- BOM (CSV) + TESTPOINT MERGED---
    {bom_content}
    --- END OF FILES ---
    Based on these files, generate all necessary data.
    """

    print(f"🤖 Calling Gemini API ({model_name}) to generate document context...")
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=GEMINI_OUTPUT_SCHEMA,
    )

    try:
        response = client.models.generate_content(
            model=model_name, contents=contents, config=generate_content_config)
        ai_response_json = json.loads(response.text)
        print(f"✅ AI response received. Caching to '{cache_file.name}'...")
        with open(cache_file, 'w') as f:
            json.dump(ai_response_json, f, indent=4)
        return ai_response_json
    except Exception as e:
        print(f"❌ An error occurred with the Gemini API call: {e}")
        return None


def parse_markdown_with_styles(markdown_text):
    """
    Parses markdown text with inline styles and leading spaces for indentation.
    Returns a list of dicts: [{'text': ..., 'bold': ..., 'size': ..., 'indent': ...}, ...]
    """
    styled_lines = []
    style_pattern = re.compile(r'\s*\((font-size:\s*(\d+),\s*bold:\s*(yes|no))\)', re.IGNORECASE)

    for line in markdown_text.split('\n'):
        match = style_pattern.search(line)
        if match:
            size = int(match.group(2))
            bold = match.group(3).strip().lower() == 'yes'
            clean_line = style_pattern.sub('', line).rstrip()
        else:
            size = 11
            bold = False
            clean_line = line.rstrip()

        if clean_line.strip():
            leading_spaces = len(clean_line) - len(clean_line.lstrip(' '))
            indent_level = leading_spaces // 2

            styled_lines.append({
                'text': clean_line.lstrip(' ') + '\n',
                'bold': bold,
                'size': size,
                'indent': indent_level
            })
    return styled_lines


def generate_document_from_ai(context):
    """Loads the .docx template and fills it with the AI-generated context."""
    if not context:
        print("❌ Cannot generate document: No context provided.")
        return

    try:
        template_path = SCRIPT_DIR / "procedure_template.docx"
        doc = DocxTemplate(template_path)
        print(f"📄 Template '{template_path.name}' loaded.")
    except Exception as e:
        print(f"❌ Error: Could not load '{template_path.name}'. {e}")
        return

    if 'procedure_rt_markdown' in context:
        rt = RichText()
        styled_lines = parse_markdown_with_styles(context['procedure_rt_markdown'])
        for style_info in styled_lines:
            rt.add(
                style_info['text'],
                bold=style_info['bold'],
                size=style_info['size']*2.3
            )
        context['procedure_rt'] = rt

    context['ds_date'] = ''
    context['ds_tester'] = ''
    context['ds_part_num'] = ''
    context['ds_serial_num'] = ''

    print("   -> Filling template with AI-generated data...")
    doc.render(context)
    output_path = SCRIPT_DIR / "AI_Generated_Procedure.docx"
    try:
        doc.save(output_path)
        print(f"✅ Success! Document saved as '{output_path}'")
    except Exception as e:
        print(f"❌ Error saving the document: {e}")


if __name__ == "__main__":
    # Define input files
    arduino_d356_file = SCRIPT_DIR.parent / "public" / "UNO-TH_Rev3e.d356"
    arduino_bom_file = SCRIPT_DIR.parent / "public" / "UNO-TH_Rev3e.xlsx"
    
    radio_ipc_file = SCRIPT_DIR / "Assembly Testpoint Report for Car-PCB1.ipc"
    radio_csv_file = SCRIPT_DIR.parent / "public" / "PCB-Car-Radio-main" / "BOM_Car Radio.csv"

    # 🚀 1. Process RADIO board
    print("\n" + "="*60)
    print("📻 Generating Radio Board Test Procedure")
    print("="*60)

    if radio_ipc_file.exists() and radio_csv_file.exists():
        radio_data = {
            "ipc_file_path": str(radio_ipc_file),
            "csv_file_path": str(radio_csv_file),
            "status": "radio_files_identified",
            "file_types": ["IPC", "CSV"]
        }
        bom_file_content = json.dumps(radio_data, indent=2, default=str)

        if os.environ.get("GEMINI_API_KEY"):
            radio_context = get_ai_generated_context(bom_file_content)
            generate_document_from_ai(radio_context)
        else:
            print("❌ Missing GEMINI_API_KEY for Radio run.")
    else:
        print("❌ Radio files not found, skipping.")

    # 🚀 2. Process ARDUINO board
    print("\n" + "="*60)
    print("🛠️ Generating Arduino Board Test Procedure")
    print("="*60)

    arduino_data = parse_board_data(
        d356_file=str(arduino_d356_file),
        bom_file=str(arduino_bom_file),
        verbose=False
    )
    bom_file_content = json.dumps(arduino_data, indent=2, default=str)

    if os.environ.get("GEMINI_API_KEY"):
        arduino_context = get_ai_generated_context(bom_file_content)
        generate_document_from_ai(arduino_context)
    else:
        print("❌ Missing GEMINI_API_KEY for Arduino run.")
