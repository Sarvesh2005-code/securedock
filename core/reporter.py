import csv
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .models import RecoveredMessage

def export_to_csv(messages: list[RecoveredMessage], output_path: str):
    """Exports a list of RecoveredMessage objects to a CSV file."""
    if not messages:
        return
        
    keys = messages[0].to_dict().keys()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        for msg in messages:
            dict_writer.writerow(msg.to_dict())

def export_forensic_report_pdf(case_id: str, investigator_name: str, 
                               evidence_hash: str, filepath: str, 
                               messages: list[RecoveredMessage], 
                               output_path: str):
    """Generates a formal forensic PDF summary of findings."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("<b>SecureDock Forensic Recovery Report</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Metadata
    elements.append(Paragraph(f"<b>Case ID:</b> {case_id}", styles['Normal']))
    elements.append(Paragraph(f"<b>Investigator:</b> {investigator_name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Generated On:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Evidence Details
    elements.append(Paragraph("<b>Evidence Information</b>", styles['Heading2']))
    elements.append(Paragraph(f"<b>Source File:</b> {os.path.basename(filepath)}", styles['Normal']))
    elements.append(Paragraph(f"<b>SHA-256 Hash:</b> {evidence_hash}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Stats
    active_count = sum(1 for m in messages if not m.is_deleted)
    deleted_count = sum(1 for m in messages if m.is_deleted)
    elements.append(Paragraph("<b>Recovery Statistics</b>", styles['Heading2']))
    elements.append(Paragraph(f"Total Messages: {len(messages)}", styles['Normal']))
    elements.append(Paragraph(f"Active Records: {active_count}", styles['Normal']))
    elements.append(Paragraph(f"Carved/Deleted Records: {deleted_count}", styles['Normal']))
    elements.append(Spacer(1, 24))
    
    # Sample Table (limit to first 100 for PDF to avoid massive files)
    elements.append(Paragraph("<b>Top Forensic Findings (Preview)</b>", styles['Heading2']))
    
    table_data = [["Timestamp", "Sender", "Receiver", "Status"]]
    for msg in messages[:100]:
        time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if msg.timestamp else "Unknown"
        status_str = "Deleted" if msg.is_deleted else "Active"
        table_data.append([time_str, msg.sender[:15], msg.receiver[:15], status_str])
        
    t = Table(table_data, colWidths=[120, 120, 120, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    
    elements.append(t)
    
    # Disclaimer
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("<i>This report was generated using SecureDock. All hashes have been verified. The tool acts strictly on provided database extractions and performs no live decryption.</i>", styles['Italic']))

    doc.build(elements)
