from copy import deepcopy
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.oxml.ns import qn

root=Path(__file__).resolve().parent
source=Path('/home/balarakeshg16/Documents/Projects/IDP_Project/Patent.docx')
doc=Document(source)
paragraphs={
3:'Title: Smart Safety Tag: A Wearable-Assisted Personal Safety System',
5:'Smart Safety Tag is a personal-safety prototype combining a mobile app, backend service, administrative portal and a wearable electronics design. The app allows a user to initiate an SOS alert and manage trusted guardians. When configured for remote operation, the backend records emergency events and can attempt to notify accepted guardians. The wearable design includes a physical SOS button, sensors, feedback and Bluetooth Low Energy (BLE), with the phone intended to supply location and network access. The wearable-to-phone emergency connection is planned and has not yet been implemented or physically validated.',
6:'At a high level, Smart Safety Tag brings together the following components (Fig. 1):',
8:'Fig. 1: Smart Safety Tag system overview. The dashed connection is planned.',
9:'Wearable design. A compact board contains a physical SOS button, motion and audio peripherals, battery monitoring, and visual and vibration feedback.',
10:'Mobile application. The app provides sign-in, guardian management, an in-app SOS action and phone-location functions. Demo mode uses simulated data.',
11:'Backend and contacts. The server records emergencies and can attempt to notify accepted guardians; an administrative portal supports authorized monitoring.',
13:'The prototype combines established safety-app and wearable technologies in one project. It provides an app-originated emergency workflow and a separate wearable fabrication design. The project does not claim that SOS buttons, Bluetooth, phone location, guardian alerts or their general combination are new. The particular implementation and any potential distinctions require review against prior art.',
14:'Smart Safety Tag processing and alert workflow',
15:'The app and backend follow the stages below. Figures 1 and 2 show the overall design and the current app-originated SOS path.',
17:'Fig. 2: App-originated emergency alert flow.',
18:'Set up the account. A user signs in and can invite trusted guardians. A guardian must accept an invitation before receiving the corresponding access.',
19:'Initiate an alert. In remote mode, the app asks for confirmation, attempts to obtain a phone location when available and submits an app-button emergency to the server.',
21:'Record the emergency. The backend stores the alert and its status event. Location may be absent if no fix is available.',
22:'Notify the audience. With a configured provider and valid tokens, the server attempts to send notifications to the owner and accepted guardians. Mock mode logs the notification rather than delivering it.',
23:'Monitor status. Authorized users can view or update an emergency subject to the server’s access and status-transition rules. The administrative portal can receive live event updates.',
24:'Planned wearable link. The current hardware-test firmware advertises over BLE and checks peripherals, but does not send a wearable SOS event to the app.',
26:'Wearable input and feedback. The board design combines a physical button, RGB indicator and vibration motor in a small tag intended to support a discreet emergency action.',
27:'Phone-assisted operation. The design relies on a phone for location and Internet access instead of placing cellular and GPS modules on the tag.',
28:'Guardian consent. Guardian invitations and acceptance are represented in the backend, with access limited to accepted guardians.',
29:'Recorded status. The backend maintains emergency records and status events, and the administrative interface supports monitoring.',
30:'Protected charging design. A separate adapter and a temperature-sensing charging inhibit are specified in the electronics package. Their actual performance remains unmeasured. These features are candidate aspects for prior-art review, not established inventions.',
33:'The practical purpose is to make an alert easier to initiate and provide trusted contacts with useful context. The repository does not demonstrate faster response, guaranteed message delivery or improved safety outcomes.',
35:'Potential uses include personal alerts while travelling, campus safety and support within a consenting group of trusted contacts. The app provides a demonstration of an SOS workflow; the proposed wearable may offer a physical input after integration and validation. These benefits are prospective and have not been measured in user studies.',
36:'Potential applications and users are summarized below; these are prospective uses, not validated customer demand:',
39:'Prototype status. The software and electronics require further security, reliability, privacy and operational review before production use.',
40:'External dependencies. Remote alerts depend on the phone, network, backend configuration, push provider, valid tokens and available guardian devices.',
41:'Wearable integration. The hardware-test firmware does not implement the emergency BLE service or a phone-side wearable alert workflow.',
42:'Physical validation. No assembled tag was available for the documented design run; radio range, battery life, charging response and enclosure fit remain unmeasured.',
43:'Detection limits. The microphone and accelerometer are included in the design, but keyword inference, fall detection and product sleep/wake behavior are not implemented in the hardware-test firmware.',
44:'Delivery and location. Push and WebSocket delivery are best effort. Location may be missing, delayed or inaccurate, and an alert does not guarantee a guardian response.',
45:'Demo limitations. Simulated locations, device connection and alerts in the demo do not demonstrate a working physical tag or real-world emergency delivery.',
47:'Figures 1–4 describe the system, the app-originated SOS flow, the hardware design and the available verification evidence. Screenshots 1–5 show demo-mode app screens; displayed names, locations and device status are illustrative.',
49:'Fig. 3: Wearable hardware and hardware-test firmware. End-to-end emergency integration remains pending.',
51:'Screenshots of the prototype in demo mode',
53:'Screenshot 1: Smart Safety Tag home screen. The shown location and connected-device status are simulated.',
55:'Screenshot 2: Sign-in screen; no credentials are entered.',
57:'Screenshot 3: Account-creation screen; fields show placeholder text.',
59:'Screenshot 4: Guardians screen with demonstration contacts.',
61:'Screenshot 5: Tracking screen with a demonstration location.',
63:'The available evidence consists of isolated software checks, saved CAD reports, a firmware build record and engineering calculations. No assembled wearable was available for the recorded design run. The following tables distinguish results from the limits of each check.',
64:'On 29 October 2026, the mobile unit suite passed 24 tests, ten selected backend tests passed using in-memory repositories and mock providers, and the admin TypeScript check passed. An authentication-based backend test timed out after 15 seconds; the complete backend suite was not established as passing.',
66:'The design register reports zero PCB design-rule violations, unconnected items and schematic parity findings for both boards. Four electrical-rule diagnostic categories are ignored by KiCad’s default configuration.',
68:'The hardware-test firmware build record reports a successful ESP-IDF v5.5 build and a 582,816-byte application image. The record states that the image was not flashed to a physical tag. Power and thermal figures are calculations rather than measurements.',
72:'Fig. 4: Summary of software checks, design evidence and remaining physical validation.',
73:'Planned physical checks include charging and thermal response, battery runtime, sensor and microphone operation, BLE range and reconnection, emergency integration and enclosure fit. Record actual conditions, measurements and failures when those checks are performed.',
75:'To be confirmed by the team: list any publications, posters, presentations, public demonstrations, public repositories or patent applications concerning Smart Safety Tag, including dates and circumstances. The available project files do not establish this history.',
77:'Smart Safety Tag is intended to help people request assistance and share emergency context with trusted contacts. Possible markets include individual users, families, campuses and organizations supporting consenting users.',
78:'Commercial potential has not been validated: the repository contains no customer interviews, paying-user evidence, pricing study or market-size estimate. No revenue or market-size figure is claimed.',
79:'Possible user groups and applications are listed below; no company-specific interest has been established.',
81:'Search date: 29 October 2026. Search terms included “wearable personal safety device Bluetooth smartphone emergency location guardian alert” and “wearable safety device GSM GPS”. Representative prior work includes:',
82:'• US20240412619A1, “Wearable personal safety device with a real time crisis response smart phone application” (2024) — wearable button communicating with a smartphone to alert contacts and share location. https://patents.google.com/patent/US20240412619A1/en',
83:'• Purnima et al., “An IoT-based Smart Wearable Safety Device using GSM, GPS, and ESP32-CAM,” IEEE ICSCDS 2025 — related wearable safety system using GPS and cellular messaging. https://doi.org/10.1109/ICSCDS65426.2025.11167200',
84:'• US20200074838A1, “Wearable multi-functional personal security device” (2020) — related wearable alert and location disclosure. https://patents.google.com/patent/US20200074838A1/en',
85:'• US9848312B2, “Personal safety monitoring” — related location-aware safety monitoring. https://patents.google.com/patent/US9848312B2/en',
86:'• Espressif Systems, ESP32-S3-MINI-1 datasheet — technical documentation for the selected wireless module. https://documentation.espressif.com/esp32-s3-mini-1_mini-1u_datasheet_en.pdf',
87:'• Texas Instruments, BQ25185 datasheet — technical documentation for the charging component. https://www.ti.com/lit/ds/symlink/bq25185.pdf',
88:'This is a preliminary search, not an exhaustive patent search, claim chart, novelty opinion or freedom-to-operate analysis. A patent professional should review the specific invention and official records before filing.',
90:'The three student team members and their identifiers are listed below; the project guide appears in a separate row. Project-specific contributions should be confirmed by the named contributors.',
}
def replace_text(p,text):
 first=next((r for r in p.runs if r.text),None)
 props=deepcopy(first._r.rPr) if first is not None and first._r.rPr is not None else None
 old_label=first.text.strip() if first is not None else ''
 split=None
 if first is not None and first.bold is True and len([r for r in p.runs if r.text]) > 1:
  delimiter=': ' if old_label.endswith(':') else '. ' if old_label.endswith('.') else None
  if delimiter and delimiter in text: split=text.index(delimiter)+len(delimiter)
 p.clear();r=p.add_run(text if split is None else text[:split])
 if props is not None:r._r.insert(0,props)
 if split is not None:
  rest=p.add_run(text[split:])
  if props is not None:rest._r.insert(0,deepcopy(props))
  rest.bold=False
for i,s in paragraphs.items():replace_text(doc.paragraphs[i],s)

tables={
0:[['Stage','Current implementation','Output'],['Wearable design','Button, sensors, BLE and feedback on a designed board','Prototype fabrication package'],['Mobile app','In-app SOS, guardian management and location paths','User interface and API request'],['Backend','Authenticated emergency records and guardian access','Emergency state and event'],['Notifications','Configured push provider and WebSocket events','Best-effort delivery and monitoring']],
1:[['Aspect','Established approaches','Smart Safety Tag project'],['Emergency input','Wearable buttons and phone apps are established.','App SOS exists; wearable input is designed but not integrated.'],['Connectivity','Devices may use a phone or their own cellular module.','The design relies on a phone for location and Internet.'],['Trusted contacts','Many systems alert designated contacts.','Guardian invitations and acceptance are represented in the backend.'],['Monitoring','Safety platforms may offer incident dashboards.','An admin portal provides authorized emergency views.'],['Validation','Claims require relevant measurements.','Software checks and CAD/build records are available.'],['Physical status','Performance requires a tested device.','No assembled board or end-to-end wearable trial is documented.']],
2:[['Potential application','Potential user group','Possible value'],['Personal SOS assistance','Individuals and families','Request help from trusted contacts.'],['Campus safety','Students and campus communities','Explore a consent-based safety workflow.'],['Support for a group','Guardians and support teams','Review an alert and available location context.'],['Research and teaching','Students and engineers','Study a safety-system prototype.']],
3:[['Check','Scope','Result','Limit'],['Mobile units','Local tests','24 passed','Includes mocks'],['Backend subset','Isolated tests','10 passed','No live database']],
4:[['Area','Method','Result','Evidence','Limit'],['Mobile','Unit tests','24 passed','Local run','No native delivery test'],['Backend','Selected tests','10 passed','In-memory fakes','Full suite incomplete'],['Admin','Type check','Passed','TypeScript','Not an end-to-end test'],['Tag PCB','KiCad DRC','No violations','Saved report','No physical build'],['Adapter PCB','KiCad DRC','No violations','Saved report','No physical build'],['Firmware','ESP-IDF build','582,816 bytes','Build record','Not flashed to board']],
5:[['Area','Method','Status','Evidence','Limit'],['Charging window','Thermal model','Calculated','Design register','Requires measurement'],['Battery runtime','Power budget','Estimated','Design assumptions','Not measured']],
6:[['Item','Current status'],['Public disclosure','To be confirmed by the team.'],['Patent application','To be confirmed by the team.'],['Internal manuscript','Draft exists; sharing and publication status to be confirmed.']],
7:[['Potential application','Potential user group','Possible value'],['Personal alerts','Individuals and families','Share an alert with trusted contacts.'],['Campus or community safety','Educational institutions','Explore an authorized safety workflow.'],['Incident monitoring','Support organizations','Review available emergency status.'],['Research and training','Students and educators','Examine the prototype and its limitations.']],
}
for index,rows in tables.items():
 t=doc.tables[index]
 assert len(t.rows)==len(rows)
 for row,data in zip(t.rows,rows):
  assert len(row.cells)==len(data)
  for cell,value in zip(row.cells,data):
   replace_text(cell.paragraphs[0],value)
   for p in cell.paragraphs[1:]: p._element.getparent().remove(p._element)
for row in doc.tables[8].rows[1:]:replace_text(row.cells[4].paragraphs[0],'To be confirmed for Smart Safety Tag.')
for c in doc.tables[9].rows[2].cells:replace_text(c.paragraphs[0],'Date: 29.10.2026')

# Replace only the nine project illustrations; signature drawings remain untouched.
imgs=[root/'figures/fig1.png',root/'figures/fig2.png',root/'figures/fig3.png']
app=root/'figures'
imgs += [app/'home.png',app/'login.png',app/'signup.png',app/'guardians.png',app/'track.png',root/'figures/fig4.png']
for i,path in enumerate(imgs):
 shape=doc.inline_shapes[i];blip=shape._inline.xpath('.//a:blip')[0];old=blip.get(qn('r:embed'))
 rid,image=doc.part.get_or_add_image(str(path));blip.set(qn('r:embed'),rid)
 if i in range(3,8): shape.width=Inches(2.15)
 shape.height=int(shape.width*image.height/image.width)
 desc=['System overview showing planned wearable link','App-originated SOS workflow','Wearable hardware and test firmware','Demo home screen with simulated device status','Sign-in screen','Account-creation screen','Guardians demo screen','Tracking demo screen','Verification evidence summary'][i]
 for element in shape._inline.xpath('.//wp:docPr | .//pic:cNvPr'):
  element.set('name',path.name);element.set('descr',desc)
 if old != rid and not doc.part._element.xpath('.//a:blip[@r:embed="%s"]'%old): doc.part.drop_rel(old)

# Remove unused external relationships left by rewritten QubitChat paragraphs.
xml=doc.part._element.xml
for rid,rel in list(doc.part.rels.items()):
 if rel.is_external and rid not in xml: doc.part.drop_rel(rid)

doc.core_properties.author='Smart Safety Tag project team'
doc.core_properties.title='Smart Safety Tag invention disclosure'
doc.core_properties.subject='Personal safety prototype'
doc.save(root/'Patent.docx')
