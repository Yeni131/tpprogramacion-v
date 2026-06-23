from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from django.utils.timezone import localtime


def generate_invoice(order):
    """
    Genera el PDF de la orden en memoria y devuelve los bytes.
    FIX: corregidos 2 bugs que rompían esta función:
      1. item.get_subtotal() ahora existe como método en OrderItem (alias de subtotal)
      2. order.get_final_total() ahora existe en el modelo Order
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles  = getSampleStyleSheet()
    brand   = colors.HexColor('#6366f1')
    gray    = colors.HexColor('#6b7280')
    light   = colors.HexColor('#f3f4f6')

    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        fontSize=22, textColor=brand, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'Sub', parent=styles['Normal'],
        fontSize=10, textColor=gray
    )
    value_style = ParagraphStyle(
        'Value', parent=styles['Normal'],
        fontSize=11, textColor=colors.black
    )

    elements = []

    # ── Encabezado ───────────────────────────────────────────────
    elements.append(Paragraph('MYA', title_style))
    elements.append(Paragraph('Comprobante de compra', sub_style))
    elements.append(Spacer(1, 0.4*cm))
    elements.append(HRFlowable(width='100%', thickness=2, color=brand))
    elements.append(Spacer(1, 0.5*cm))

    fecha = localtime(order.created).strftime('%d/%m/%Y %H:%M')

    # Nombre a mostrar: usa first_name/last_name del Order (datos del shipping),
    # con fallback al username del usuario logueado.
    cliente_nombre = f'{order.first_name} {order.last_name}'.strip() or order.user.username

    info_data = [
        [
            Paragraph('<b>FACTURA</b>', styles['Normal']),
            Paragraph('<b>CLIENTE</b>', styles['Normal']),
        ],
        [
            Paragraph(f'Orden #{order.id}', value_style),
            Paragraph(cliente_nombre, value_style),
        ],
        [
            Paragraph(f'Fecha: {fecha}', sub_style),
            Paragraph(f'Email: {order.email or order.user.email or "—"}', sub_style),
        ],
        [
            Paragraph(f'Estado: <b>{order.get_status_display()}</b>', sub_style),
            Paragraph(f'Dirección: {order.address or "—"}, {order.city or ""}', sub_style),
        ],
    ]

    # ── Datos de facturación (si el cliente solicitó factura) ─────
    if order.wants_invoice and hasattr(order, 'billing'):
        billing = order.billing
        info_data.append([
            Paragraph('<b>FACTURACIÓN</b>', styles['Normal']),
            Paragraph('', styles['Normal']),
        ])
        info_data.append([
            Paragraph(f'Razón social: {billing.business_name}', sub_style),
            Paragraph(f'RUC/CI: {billing.ruc}', sub_style),
        ])
        if billing.fiscal_address:
            info_data.append([
                Paragraph(f'Dirección fiscal: {billing.fiscal_address}', sub_style),
                Paragraph('', sub_style),
            ])

    info_table = Table(info_data, colWidths=[9*cm, 9*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN',      (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.6*cm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 0.4*cm))

    # ── Tabla de productos ───────────────────────────────────────
    elements.append(Paragraph('<b>Detalle de productos</b>', styles['Normal']))
    elements.append(Spacer(1, 0.3*cm))

    header = ['Producto', 'Variante', 'Precio unit.', 'Cant.', 'Subtotal']
    rows   = [header]

    for item in order.items.all():
        variant_str = ''
        if item.variant:
            parts = [item.variant.size, item.variant.color]
            variant_str = ' / '.join(p for p in parts if p)

        rows.append([
            item.product.name,
            variant_str or '—',
            f'Gs. {item.price:,.0f}',
            str(item.quantity),
            f'Gs. {item.get_subtotal():,.0f}',   # FIX: ahora existe como método
        ])

    col_widths = [7*cm, 3.5*cm, 2.5*cm, 1.5*cm, 2.5*cm]
    prod_table = Table(rows, colWidths=col_widths, repeatRows=1)
    prod_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), brand),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,0), 9),
        ('TOPPADDING',    (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('FONTSIZE',      (0,1), (-1,-1), 9),
        ('TOPPADDING',    (0,1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, light]),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor('#e5e7eb')),
        ('ALIGN',         (2,0), (-1,-1), 'RIGHT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(prod_table)
    elements.append(Spacer(1, 0.6*cm))

    # ── Totales ──────────────────────────────────────────────────
    totals_data = []

    if order.discount and order.discount > 0:
        coupon_label = f'Descuento ({order.coupon.code})' if order.coupon else 'Descuento'
        totals_data.append(['', coupon_label, f'-Gs. {order.discount:,.0f}'])

    totals_data.append(['', 'TOTAL', f'Gs. {order.get_final_total():,.0f}'])  # FIX: ahora existe

    totals_table = Table(totals_data, colWidths=[10.5*cm, 4*cm, 2.5*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN',       (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME',    (1,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 10),
        ('TEXTCOLOR',   (1,-1), (-1,-1), brand),
        ('FONTSIZE',    (1,-1), (-1,-1), 13),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(totals_table)

    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        'Gracias por tu compra — MYA',
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=gray, alignment=1)
    ))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf