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

    prompt = f"""
    You are an expert test procedure writer...
    --- BOM (CSV) + TESTPOINT MERGED---
    {bom_content}
    --- END OF FILES ---
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


def generate_document_from_ai(context, board_name=""):
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
                size=style_info['size'] * 2.3
            )
        context['procedure_rt'] = rt

    context['ds_date'] = ''
    context['ds_tester'] = ''
    context['ds_part_num'] = ''
    context['ds_serial_num'] = ''

    print("   -> Filling template with AI-generated data...")

    # Unique filename per board
    filename = f"AI_Generated_Procedure_{board_name}.docx" if board_name else "AI_Generated_Procedure.docx"
    output_path = SCRIPT_DIR / filename

    try:
        doc.render(context)
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
            generate_document_from_ai(radio_context, board_name="radio")
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
        generate_document_from_ai(arduino_context, board_name="arduino")
    else:
        print("❌ Missing GEMINI_API_KEY for Arduino run.")
