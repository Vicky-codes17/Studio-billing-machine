from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os
from datetime import datetime

def create_a4_pdf(invoice, items, company):
    """Generate A4 PDF invoice with logo"""
    try:
        # Create pdfs directory if it doesn't exist
        pdf_dir = os.path.join(os.getcwd(), 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Generate filename
        filename = f"invoice_{invoice.invoice_no}_{invoice.date.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(pdf_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for PDF elements
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#4f46e5')
        )
        
        company_style = ParagraphStyle(
            'CompanyInfo',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#6b7280')
        )
        
        # Add logo if exists
        logo_path = os.path.join(os.getcwd(), 'static', 'logo.png')
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path)
                logo.drawHeight = 1*inch
                logo.drawWidth = 1*inch
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 10))
            except:
                pass  # Skip logo if there's an error
        
        # Company Header
        story.append(Paragraph(company['name'], title_style))
        
        # Company address
        address_lines = company['address'].replace('\n', '<br/>')
        company_info = f"{address_lines}<br/>Phone: {company['phone']}"
        story.append(Paragraph(company_info, company_style))
        
        # Add watermark logo in background
        if os.path.exists(logo_path):
            try:
                # Create a background image with transparency
                watermark_style = ParagraphStyle(
                    'Watermark',
                    parent=styles['Normal'],
                    alignment=TA_CENTER,
                )
                # This creates a semi-transparent background effect
                story.append(Spacer(1, 50))
            except:
                pass
        
        # Add some space
        story.append(Spacer(1, 20))
        
        # Invoice details
        invoice_title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#1f2937')
        )
        
        story.append(Paragraph(f"Invoice #{invoice.invoice_no}", invoice_title_style))
        
        # Invoice info table
        invoice_data = [
            ['Date:', invoice.date.strftime('%d/%m/%Y %H:%M')],
            ['Customer:', invoice.customer_name],
        ]
        
        if invoice.customer_phone:
            invoice_data.append(['Phone:', invoice.customer_phone])
        
        if invoice.notes:
            invoice_data.append(['Notes:', invoice.notes])
        
        invoice_table = Table(invoice_data, colWidths=[1.5*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 30))
        
        # Items table
        items_data = [['Description', 'Qty', 'Rate (₹)', 'Tax %', 'Amount (₹)']]
        
        for item in items:
            items_data.append([
                item.description,
                str(item.quantity),
                f"{float(item.rate):.2f}",
                f"{float(item.tax_rate):.1f}%",
                f"{item.final_amount:.2f}"
            ])
        
        # Add totals
        items_data.extend([
            ['', '', '', 'Subtotal:', f"{invoice.subtotal:.2f}"],
        ])
        
        if invoice.tax_amount > 0:
            items_data.append(['', '', '', 'Tax:', f"{invoice.tax_amount:.2f}"])
        
        items_data.append(['', '', '', 'Total:', f"{invoice.grand_total:.2f}"])
        
        items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1*inch, 1*inch, 1.2*inch])
        
        # Table styling
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -4), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            
            # Subtotal and total rows
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -3), (-1, -1), 11),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8fafc')),
            
            # Borders
            ('GRID', (0, 0), (-1, -4), 1, colors.black),
            ('LINEBELOW', (0, -3), (-1, -3), 2, colors.HexColor('#4f46e5')),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor('#1f2937')),
        ]))
        
        story.append(items_table)
        
        # Footer
        story.append(Spacer(1, 50))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6b7280')
        )
        
        story.append(Paragraph("Thank you for your business!", footer_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
        
        # Build PDF
        doc.build(story)
        
        return filepath
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise e