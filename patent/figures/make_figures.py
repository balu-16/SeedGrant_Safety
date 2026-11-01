import fitz
from pathlib import Path
out=Path(__file__).parent
figs=[
 ('fig1.png','Smart Safety Tag system overview',['Wearable design\nSOS, sensors, BLE','Phone application\nSOS and location','Backend\nrecords and access','Guardians / admin\nnotifications and view'],'Wearable-to-phone emergency integration is planned, not implemented.'),
 ('fig2.png','App-originated SOS workflow',['User confirms SOS\nin the mobile app','Location attempt\nwhen available','API records\nemergency','Best-effort push\nand live events'],'A demo alert is simulated. Real delivery depends on configuration and connectivity.'),
 ('fig3.png','Wearable hardware and test firmware',['SOS button and\nmotion sensor','ESP32-S3\ntest firmware','BLE advertising;\nfeedback and audio','Battery, charger\nand protection'],'Board validation, emergency BLE service and keyword inference remain pending.'),
 ('fig4.png','Verification evidence and limitations',['24 mobile\nunit tests passed','10 selected backend\ntests passed','CAD checks and\nfirmware build','Physical board and\nintegration pending'],'Software tests use mocks; CAD and build checks are not field measurements.')]
for name,title,boxes,note in figs:
 d=fitz.open();p=d.new_page(width=850,height=340)
 p.insert_textbox(fitz.Rect(20,18,830,56),title,fontsize=19,fontname='hebo',align=1)
 xs=[32,238,444,650]
 for x,label in zip(xs,boxes):
  rect=fitz.Rect(x,116,x+168,200);p.draw_rect(rect,color=(0.15,0.15,0.15),width=1.5)
  p.insert_textbox(fitz.Rect(x+6,137,x+162,190),label,fontsize=12,fontname='hebo',align=1,lineheight=1.3)
 for i in range(3):
  x=xs[i]+168; y=158
  p.draw_line((x,y),(x+37,y),color=(0,0,0),width=1.4,dashes='[4 3] 0' if name=='fig1.png' and i==0 else None)
  p.draw_line((x+30,y-5),(x+37,y),color=(0,0,0));p.draw_line((x+30,y+5),(x+37,y),color=(0,0,0))
 p.insert_textbox(fitz.Rect(25,260,825,315),note,fontsize=11,align=1)
 p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(out/name)
