import os
import win32com.client

# Root folder with all Altium project files
#modify to match your own paths
FOLDER = r"C:\Users\anivenkat\AeronixHackathon\public\PCB-Car-Radio-main"
OUTPUT = r"C:\Users\anivenkat\AeronixHackathon\exports"

# Connect to Altium
altium = win32com.client.Dispatch("AD.Application")

os.makedirs(OUTPUT, exist_ok=True)

for root, _, files in os.walk(FOLDER):
    for file in files:
        path = os.path.join(root, file)
        name, ext = os.path.splitext(file)

        ext = ext.lower()

        if ext == ".pcbdoc":
            print(f"[PCB] Exporting IPC-2581: {file}")
            pcb_doc = altium.OpenDocument("PCB", path)
            exporter = pcb_doc.CreateExportObject("IPC2581")
            out_file = os.path.join(OUTPUT, f"{name}.xml")
            exporter.Destination = out_file
            exporter.Export()

        elif ext == ".schdoc":
            print(f"[SCH] Exporting PDF: {file}")
            sch_doc = altium.OpenDocument("SCH", path)
            exporter = sch_doc.CreateExportObject("PDF")
            out_file = os.path.join(OUTPUT, f"{name}.pdf")
            exporter.Destination = out_file
            exporter.Export()

        elif ext == ".bomdoc":
            print(f"[BOM] Exporting CSV: {file}")
            bom_doc = altium.OpenDocument("BomDoc", path)
            exporter = bom_doc.CreateExportObject("CSV")
            out_file = os.path.join(OUTPUT, f"{name}.csv")
            exporter.Destination = out_file
            exporter.Export()

        elif ext == ".prjpcb":
            print(f"[PRJ] Found project file: {file} (no direct export)")

        else:
            print(f"[SKIP] Unknown file type: {file}")

print("✅ All exports complete!")
