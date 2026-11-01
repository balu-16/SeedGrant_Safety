from html.parser import HTMLParser
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

root = Path(__file__).resolve().parent
class Builder(HTMLParser):
    def __init__(self):
        super().__init__(); self.doc=Document(); self.tag=None; self.text=[]; self.table=None; self.row=None; self.cell=None; self.link=None; self.skip=0
        self.doc.styles['Normal'].font.name='Calibri'; self.doc.styles['Normal'].font.size=Pt(10)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag in ('head','style'): self.skip+=1; return
        if self.skip: return
        if tag=='table': self.table=[]
        elif tag=='tr' and self.table is not None: self.row=[]
        elif tag in ('th','td') and self.row is not None: self.cell=[]
        elif tag in ('h1','h2','h3','p','li') and self.cell is None: self.tag=tag; self.text=[]
        elif tag=='a': self.link=a.get('href')
        elif tag=='img':
            self.doc.add_picture(str(root/a['src']), width=Inches(6.1))
    def handle_data(self,data):
        if self.skip: return
        if self.cell is not None: self.cell.append(data)
        elif self.tag: self.text.append(data)
    def handle_endtag(self,tag):
        if tag in ('head','style'): self.skip-=1; return
        if self.skip: return
        if tag=='a' and self.link:
            (self.cell if self.cell is not None else self.text).append(' ('+self.link+')'); self.link=None
        elif tag in ('th','td') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell=None
        elif tag=='tr' and self.row is not None: self.table.append(self.row); self.row=None
        elif tag=='table' and self.table is not None:
            if self.table:
                t=self.doc.add_table(rows=0, cols=max(map(len,self.table))); t.style='Table Grid'
                for row in self.table:
                    cells=t.add_row().cells
                    for i,value in enumerate(row): cells[i].text=value
            self.table=None
        elif tag==self.tag:
            s=' '.join(''.join(self.text).split())
            if s:
                if tag=='h1': p=self.doc.add_heading(s,0); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                elif tag in ('h2','h3'): self.doc.add_heading(s,1 if tag=='h2' else 2)
                else: self.doc.add_paragraph(s,style='List Bullet' if tag=='li' else None)
            self.tag=None; self.text=[]
parser=Builder(); parser.feed((root/'invention_disclosure.html').read_text()); parser.doc.save(root/'invention_disclosure.docx')
