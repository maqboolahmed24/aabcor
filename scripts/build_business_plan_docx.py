#!/usr/bin/env python3
"""
Builds a polished business-plan.docx from business-plan.html with:
- Cover page (title, subtitle, date)
- Table of Contents (Word-updatable field)
- Branded heading styles (Title, Heading 1/2)
- Page header/footer with page numbers
- Styled tables with zebra rows and header shading

Note: Word will finalize TOC after Update Field (F9) inside Word.
"""
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime
import zipfile
import re

ROOT = Path(__file__).resolve().parents[1]
HTML_IN = ROOT / 'business-plan.html'
DOCX_OUT = ROOT / 'business-plan.docx'


class PlanParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.current_tag = None
        self.current_text = []
        self.list_depth = 0
        self.in_table = False
        self.table_rows = []
        self.current_row = None
        self.current_cell = None

    def flush_text(self, tag):
        text = ''.join(self.current_text).strip()
        self.current_text = []
        if not text:
            return
        if tag == 'h1':
            self.blocks.append(('title', text))
        elif tag == 'h2':
            self.blocks.append(('h1', text))
        elif tag == 'h3':
            self.blocks.append(('h2', text))
        elif tag == 'p':
            self.blocks.append(('p', text))
        elif tag == 'li':
            self.blocks.append(('li', text, self.list_depth))

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ('h1', 'h2', 'h3', 'p'):
            self.flush_pending()
            self.current_tag = tag
            self.current_text = []
        elif tag == 'li':
            self.flush_pending()
            self.current_tag = 'li'
            self.current_text = []
        elif tag == 'ul':
            self.flush_pending()
            self.list_depth += 1
        elif tag == 'table':
            self.flush_pending()
            self.in_table = True
            self.table_rows = []
        elif tag == 'tr':
            if self.in_table:
                self.current_row = []
        elif tag in ('td', 'th'):
            if self.in_table:
                self.current_cell = {'text': [] , 'header': tag=='th'}

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ('h1','h2','h3','p') and self.current_tag == tag:
            self.flush_text(tag)
            self.current_tag = None
        elif tag == 'li' and self.current_tag == 'li':
            self.flush_text(tag)
            self.current_tag = None
        elif tag == 'ul':
            self.flush_pending()
            if self.list_depth>0:
                self.list_depth -= 1
        elif tag in ('td','th'):
            if self.in_table and self.current_cell is not None:
                text = ''.join(self.current_cell['text']).strip()
                self.current_row.append({'text': text, 'header': self.current_cell['header']})
                self.current_cell = None
        elif tag == 'tr':
            if self.in_table and self.current_row is not None:
                if any(c['text'] for c in self.current_row):
                    self.table_rows.append(self.current_row)
                self.current_row = None
        elif tag == 'table':
            if self.in_table and self.table_rows:
                self.blocks.append(('table', self.table_rows))
            self.in_table = False
            self.table_rows = []

    def handle_data(self, data):
        if self.in_table and self.current_cell is not None:
            self.current_cell['text'].append(data)
        elif self.current_tag:
            self.current_text.append(data)

    def flush_pending(self):
        if self.current_tag in ('h1','h2','h3','p'):
            self.flush_text(self.current_tag)
            self.current_tag = None
        elif self.current_tag == 'li':
            self.flush_text('li')
            self.current_tag = None


def esc(text: str) -> str:
    return (text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))


def r(text, bold=False, color=None, sz=None):
    rpr = []
    if bold: rpr.append('<w:b/>')
    if color: rpr.append(f'<w:color w:val="{color}"/>')
    if sz: rpr.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    rpr_xml = f'<w:rPr>{"".join(rpr)}</w:rPr>' if rpr else ''
    return f'<w:r>{rpr_xml}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def p(text='', style=None, align=None, before=None, after=None, indent_left=None, hanging=None, runs=None):
    ppr = []
    if style: ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align: ppr.append(f'<w:jc w:val="{align}"/>')
    if before or after:
        before = before or 0
        after = after or 0
        ppr.append(f'<w:spacing w:before="{before}" w:after="{after}"/>')
    if indent_left or hanging:
        attrs = []
        if indent_left: attrs.append(f'w:left="{indent_left}"')
        if hanging: attrs.append(f'w:hanging="{hanging}"')
        ppr.append(f'<w:ind {" ".join(attrs)}/>')
    ppr_xml = f'<w:pPr>{"".join(ppr)}</w:pPr>' if ppr else ''
    run_xml = ''.join(runs) if runs else r(text or '')
    return f'<w:p>{ppr_xml}{run_xml}</w:p>'


def hrule():
    return '<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="cccccc"/></w:pBdr></w:pPr><w:r><w:t/></w:r></w:p>'


def table(rows):
    if not rows:
        return ''
    cols = max(len(rw) for rw in rows)
    grid_cols = ''.join(f'<w:gridCol w:w="{int(9000/cols)}"/>' for _ in range(cols))
    trs = []
    zebra = False
    for i, rw in enumerate(rows):
        tcs = []
        zebra = (i % 2 == 1)
        for cell in rw:
            is_header = cell.get('header', False)
            text = cell['text']
            # detect money/ARR to optionally bold
            bold = bool(re.search(r"\$|ARR|OPEX", text)) and not is_header
            para = p(text, runs=[r(text, bold=bold)])
            shd = ''
            if is_header:
                shd = '<w:shd w:val="clear" w:color="auto" w:fill="f3f4f6"/>'
            elif zebra:
                shd = '<w:shd w:val="clear" w:color="auto" w:fill="fbfdff"/>'
            tcpr = f'<w:tcPr><w:tcW w:w="0" w:type="auto"/>{shd}</w:tcPr>'
            tcs.append(f'<w:tc>{tcpr}{para}</w:tc>')
        trs.append(f'<w:tr>{"".join(tcs)}</w:tr>')
    borders = (
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="dddddd"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="dddddd"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="dddddd"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="dddddd"/>'
        '<w:insideH w:val="single" w:sz="2" w:space="0" w:color="eeeeee"/>'
        '<w:insideV w:val="single" w:sz="2" w:space="0" w:color="eeeeee"/>'
        '</w:tblBorders>'
    )
    tbl_pr = f'<w:tblPr><w:tblW w:w="0" w:type="auto"/>{borders}</w:tblPr>'
    tbl_grid = f'<w:tblGrid>{grid_cols}</w:tblGrid>'
    return f'<w:tbl>{tbl_pr}{tbl_grid}{"".join(trs)}</w:tbl>'


def build():
    html = HTML_IN.read_text(encoding='utf-8')
    parser = PlanParser()
    parser.feed(html)
    parser.flush_pending()

    # Build document body
    body = []

    # Cover page
    today = datetime.utcnow().strftime('%d %b %Y')
    body.append(p('Aabcor – AI-Powered NRW Detection', style='Title'))
    body.append(p('Business Plan', style='Subtitle'))
    body.append(p(today, style='Subtitle'))
    body.append(hrule())
    body.append(p())

    # TOC placeholder (Word-updatable)
    body.append('<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve">TOC \\o "1-2" \\h \\z \\u</w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>Table of Contents (right-click & Update Field in Word)</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    body.append(p())

    # Content
    for block in parser.blocks:
        if block[0] == 'title':
            # Skip original big H1 (we made a cover already)
            continue
        if block[0] == 'h1':
            body.append(p(block[1], style='Heading1', before=240, after=60))
        elif block[0] == 'h2':
            body.append(p(block[1], style='Heading2', before=160, after=40))
        elif block[0] == 'p':
            body.append(p(block[1], before=40, after=80))
        elif block[0] == 'li':
            text, depth = block[1], block[2]
            indent = 360 + (depth-1)*360
            body.append(p('• ' + text, indent_left=indent, hanging=360))
        elif block[0] == 'table':
            body.append(table(block[1]))
            body.append(p())

    # Section properties with header/footer refs
    sect_pr = (
        '<w:sectPr>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
        '<w:cols w:space="708"/>'
        '<w:docGrid w:linePitch="360"/>'
        '<w:headerReference w:type="default" r:id="rIdHeader1"/>'
        '<w:footerReference w:type="default" r:id="rIdFooter1"/>'
        '</w:sectPr>'
    )
    body_xml = ''.join(body) + sect_pr

    # Build document.xml
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<w:body>{body_xml}</w:body>'
        '</w:document>'
    )

    # Styles: Title, Subtitle, Heading1/2, Normal
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/>'
        '<w:qFormat/>'
        '<w:rPr><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
        '</w:style>'
        '<w:style w:type="paragraph" w:styleId="Title">'
        '<w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:sz w:val="48"/><w:szCs w:val="48"/><w:color w:val="0B0F19"/><w:b/></w:rPr>'
        '<w:pPr><w:jc w:val="center"/><w:spacing w:after="240"/></w:pPr>'
        '</w:style>'
        '<w:style w:type="paragraph" w:styleId="Subtitle">'
        '<w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:sz w:val="28"/><w:szCs w:val="28"/><w:color w:val="0F3D62"/></w:rPr>'
        '<w:pPr><w:jc w:val="center"/></w:pPr>'
        '</w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1">'
        '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:b/><w:sz w:val="30"/><w:szCs w:val="30"/><w:color w:val="0F3D62"/></w:rPr>'
        '</w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading2">'
        '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:b/><w:sz w:val="26"/><w:szCs w:val="26"/><w:color w:val="1E8E5A"/></w:rPr>'
        '</w:style>'
        '</w:styles>'
    )

    # Header/footer parts
    header_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:p><w:pPr><w:jc w:val="both"/></w:pPr>'
        f'{r("Aabcor Business Plan", bold=True, color="0B0F19")}'
        '</w:p>'
        '</w:hdr>'
    )

    footer_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        '<w:r><w:t>1</w:t></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        '<w:r><w:t xml:space="preserve"> / </w:t></w:r>'
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> NUMPAGES </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        '<w:r><w:t>1</w:t></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        '</w:p>'
        '</w:ftr>'
    )

    # Relationships
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>'
    )

    doc_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '<Relationship Id="rIdHeader1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>'
        '<Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
        '</Relationships>'
    )

    # Core/app props
    now = datetime.utcnow().replace(microsecond=0).isoformat()+'Z'
    core_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>Aabcor AI NRW Detection – Business Plan</dc:title>'
        '<dc:subject>Aabcor Business Plan</dc:subject>'
        '<dc:creator>aabcor.com</dc:creator>'
        '<cp:lastModifiedBy>aabcor.com</cp:lastModifiedBy>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        '</cp:coreProperties>'
    )
    app_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<Application>aabcor.com</Application>'
        '</Properties>'
    )

    # Content types
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
        '</Types>'
    )

    # Write zip
    with zipfile.ZipFile(DOCX_OUT, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels_xml)
        zf.writestr('word/document.xml', document_xml)
        zf.writestr('word/styles.xml', styles_xml)
        zf.writestr('word/_rels/document.xml.rels', doc_rels_xml)
        zf.writestr('word/header1.xml', header_xml)
        zf.writestr('word/footer1.xml', footer_xml)
        zf.writestr('docProps/core.xml', core_xml)
        zf.writestr('docProps/app.xml', app_xml)

    print('Wrote', DOCX_OUT)


if __name__ == '__main__':
    build()
