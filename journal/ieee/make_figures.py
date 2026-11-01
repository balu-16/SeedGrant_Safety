import fitz
from pathlib import Path
root=Path(__file__).parent
out=root/'figures'
D=fitz.open(); p=D.new_page(width=720,height=360)
def box(x,y,w,h,title,body):
 r=fitz.Rect(x,y,x+w,y+h); p.draw_rect(r,color=(.12,.24,.36),fill=(.95,.97,.98),width=1.1)
 p.insert_textbox(fitz.Rect(x+8,y+7,x+w-8,y+29),title,fontsize=11,fontname='hebo',color=(.07,.2,.34))
 p.insert_textbox(fitz.Rect(x+8,y+32,x+w-8,y+h-5),body,fontsize=9,lineheight=1.2)
def arrow(x1,y1,x2,y2,dash=False):
 p.draw_line((x1,y1),(x2,y2),color=(.18,.26,.31),width=1.2,dashes='[4 3] 0' if dash else None)
 p.draw_line((x2-6,y2-4),(x2,y2),color=(.18,.26,.31));p.draw_line((x2-6,y2+4),(x2,y2),color=(.18,.26,.31))
box(15,75,145,95,'Wearable design','SOS button, sensors, BLE,\nbattery and feedback\nHardware-test firmware')
box(215,75,145,95,'Phone application','App SOS and GPS paths;\ndemo or remote services')
box(415,75,145,95,'Backend','Auth, emergencies,\nguardians, location, push')
box(575,75,130,95,'Admin portal','Emergency view,\nmanagement and audit')
arrow(160,120,215,120,True);arrow(360,120,415,120);arrow(560,120,575,120)
p.insert_text((161,107),'planned',fontsize=8);p.insert_text((369,107),'API',fontsize=8)
box(415,225,145,72,'Guardian accounts','Accepted guardians;\npush is best effort')
p.draw_line((488,170),(488,225),color=(.18,.26,.31));p.draw_line((484,219),(488,225));p.draw_line((492,219),(488,225))
p.insert_text((18,325),'Solid links: implemented software paths. Dashed link: intended integration, not implemented.',fontsize=10)
D.save(out/'architecture.pdf'); p.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(out/'architecture.png')

# Additional figures are drawn directly as vector PDFs so labels remain editable.
def diagram(filename, title, items, notes):
 d=fitz.open(); page=d.new_page(width=760,height=300)
 page.insert_textbox(fitz.Rect(10,12,750,40),title,fontsize=15,fontname='hebo',align=1,color=(.07,.2,.34))
 for i,(head,body) in enumerate(items):
  x=20+i*185
  page.draw_rect(fitz.Rect(x,80,x+158,175),color=(.12,.24,.36),fill=(.95,.97,.98),width=1.1)
  page.insert_textbox(fitz.Rect(x+6,88,x+152,112),head,fontsize=10,fontname='hebo',align=1)
  page.insert_textbox(fitz.Rect(x+6,116,x+152,169),body,fontsize=9,align=1,lineheight=1.15)
  if i<len(items)-1:
   page.draw_line((x+158,128),(x+185,128),color=(.18,.26,.31),width=1.2)
   page.draw_line((x+179,124),(x+185,128));page.draw_line((x+179,132),(x+185,128))
 page.insert_textbox(fitz.Rect(20,220,740,280),notes,fontsize=10,align=1)
 d.save(out/filename)
diagram('sos_flow.pdf','App-originated SOS and notification flow',[
 ('Confirm','User confirms an\nin-app SOS action'),
 ('Location','Try cached or one-shot\nphone location'),
 ('Record','API stores emergency\nand status event'),
 ('Notify','Best-effort push and\nWebSocket events')],
 'Location can be unavailable or delayed; a notification request is not proof of delivery or acknowledgement.')
diagram('power_path.pdf','Wearable power architecture',[
 ('USB-C adapter','Input protection and\neFuse before contacts'),
 ('Tag input','Reverse diode and\nBQ25185 power path'),
 ('Regulation','TPS63802 converts\nsystem power to 3V3'),
 ('Loads','MCU and sensors;\nswitched feedback')],
 'Protected cell connects to the charger; an independent modeled temperature window inhibits charging. Physical behavior is unmeasured.')

# Vector crops of existing project assembly exports; these are CAD drawings.
project=root.parent.parent
manufacturing=project/'smart-safety-tag-v1/manufacturing'
def assembly_figure(output, panels):
 doc=fitz.open();page=doc.new_page(width=760,height=350)
 for i,(name,clip,label) in enumerate(panels):
  source=fitz.open(manufacturing/name)
  dest=fitz.Rect(20+i*370,36,370+i*370,305)
  page.show_pdf_page(dest,source,0,clip=fitz.Rect(*clip),keep_proportion=True)
  page.insert_textbox(fitz.Rect(20+i*370,310,370+i*370,335),label,fontsize=11,fontname='hebo',align=1)
 legends={'tag_board.pdf':'U1: MCU/BLE; SW1: SOS; U2: microphone; U7: regulator; RT1: thermistor; J2: charging contacts.', 'adapter_board.pdf':'J1: USB-C input; U1: eFuse; P1/P2: charging contacts.'}
 page.insert_textbox(fitz.Rect(10,335,750,350),legends[output],fontsize=8.5,align=1)
 doc.save(out/output)
assembly_figure('tag_board.pdf',[
 ('tag/assembly/smart-safety-tag-front-assembly.pdf',(155,155,685,565),'(a) Tag, front assembly view'),
 ('tag/assembly/smart-safety-tag-back-assembly.pdf',(155,185,685,565),'(b) Tag, mirrored rear assembly view')])
assembly_figure('adapter_board.pdf',[
 ('charging-adapter/assembly/charging-adapter-front-assembly.pdf',(230,165,610,435),'(a) Adapter, front assembly view'),
 ('charging-adapter/assembly/charging-adapter-back-assembly.pdf',(230,165,610,435),'(b) Adapter, mirrored rear view')])
