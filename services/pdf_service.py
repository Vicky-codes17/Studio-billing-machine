from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import tempfile
from datetime import datetime

def create_a4_pdf(invoice, items, company):
    """Create A4 PDF invoice"""
    try:
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        filename = f"invoice_{invoice.invoice_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(temp_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Company header
        company_style = ParagraphStyle(
            'CompanyName',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.HexColor('#4f46e5')
        )
        
        story.append(Paragraph(company['name'], company_style))
        story.append(Paragraph(company['address'].replace('\n', '<br/>'), styles['Normal']))
        story.append(Paragraph(f"Phone: {company['phone']}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Invoice details
        invoice_data = [
            ['Invoice #:', invoice.invoice_no],
            ['Date:', invoice.date.strftime('%d/%m/%Y %I:%M %p')],
            ['Customer:', invoice.customer_name],
        ]
        
        if invoice.customer_phone:
            invoice_data.append(['Phone:', invoice.customer_phone])
        
        if invoice.notes:
            invoice_data.append(['Notes:', invoice.notes])
        
        invoice_table = Table(invoice_data, colWidths=[1.5*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 30))
        
        # Items table
        table_data = [['Description', 'Qty', 'Rate (₹)', 'Tax (%)', 'Amount (₹)']]
        
        for item in items:
            table_data.append([
                item.description,
                str(item.quantity),
                f"₹{item.rate:.2f}",
                f"{item.tax_rate:.1f}%",
                f"₹{item.final_amount:.2f}"
            ])
        
        # Add totals
        table_data.append(['', '', '', 'Subtotal:', f"₹{invoice.subtotal:.2f}"])
        if invoice.tax_amount > 0:
            table_data.append(['', '', '', 'Tax:', f"₹{invoice.tax_amount:.2f}"])
        table_data.append(['', '', '', 'Grand Total:', f"₹{invoice.grand_total:.2f}"])
        
        items_table = Table(table_data, colWidths=[3*inch, 0.8*inch, 1.2*inch, 1*inch, 1.2*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Description left-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Highlight totals
            ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = "Thank you for your business!"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return file_path
        
    except Exception as e:
        raise Exception(f"Error creating PDF: {str(e)}")