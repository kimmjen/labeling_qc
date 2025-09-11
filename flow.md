# 1.파일업로드후 파일 페이지확인

## Headers

"""
Request URL
http://172.19.2.164/studio-lite/api/v1/dl/files/upload
Request Method
POST
Status Code
200 OK
Remote Address
172.19.2.164:80
Referrer Policy
strict-origin-when-cross-origin
cache-control
no-cache
connection
keep-alive
content-type
application/json
date
Thu, 11 Sep 2025 04:25:57 GMT
server
nginx/1.29.1
transfer-encoding
chunked
accept
application/json, text/plain, */*
accept-encoding
gzip, deflate
accept-language
ko-KR,ko;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6
connection
keep-alive
content-length
1986508
content-type
multipart/form-data; boundary=----WebKitFormBoundaryohySaivtG4W8CUS8
host
172.19.2.164
origin
http://172.19.2.164
referer
http://172.19.2.164/studio-lite/
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
"""

## Payload

"""
Form Data

file
(binary)
"""

## Preview
"""
{codeNum: 0, code: "file.upload.success",…}
code
: 
"file.upload.success"
codeNum
: 
0
data
: 
{fileId: "0d39727e-3cfe-3e8f-ba85-8e9da428eaee", fileName: "TLAW1202000180_TP.PDF",…}
status
: 
200
timestamp
: 
"2025-09-11T04:25:57.378Z"
"""

## Response

"""
{
    "codeNum": 0,
    "code": "file.upload.success",
    "data": {
        "fileId": "0d39727e-3cfe-3e8f-ba85-8e9da428eaee",
        "fileName": "TLAW1202000180_TP.PDF",
        "created": "2025-09-11T04:25:57.378336417Z",
        "createdEpoch": "1757564757378",
        "fileSize": 1986308,
        "numOfPages": 120
    },
    "timestamp": "2025-09-11T04:25:57.378Z",
    "status": 200
}
"""

# 2. 페이지수에 대한 OCR

## Headers
"""
http://172.19.2.164/studio-lite/api/v1/dl/files/0d39727e-3cfe-3e8f-ba85-8e9da428eaee/extract-page?range=1-120
Request Method
POST
Status Code
200 OK
Remote Address
172.19.2.164:80
Referrer Policy
strict-origin-when-cross-origin
cache-control
no-cache
connection
keep-alive
content-type
application/json
date
Thu, 11 Sep 2025 04:27:10 GMT
server
nginx/1.29.1
transfer-encoding
chunked
accept
application/json, text/plain, */*
accept-encoding
gzip, deflate
accept-language
ko-KR,ko;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6
connection
keep-alive
content-length
0
host
172.19.2.164
origin
http://172.19.2.164
referer
http://172.19.2.164/studio-lite/
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
"""

## Payload

"""
range
1-120
"""

## Preview
"""
{codeNum: 0, code: "extract.pdf.pages.success",…}
code
: 
"extract.pdf.pages.success"
codeNum
: 
0
data
: 
{fileId: "0d39727e-3cfe-3e8f-ba85-8e9da428eaee", fileName: "TLAW1202000180_TP.PDF",…}
created
: 
"2025-09-11T04:25:57.378336417Z"
createdEpoch
: 
"1757564757378"
fileId
: 
"0d39727e-3cfe-3e8f-ba85-8e9da428eaee"
fileName
: 
"TLAW1202000180_TP.PDF"
fileSize
: 
1986308
numOfPages
: 
120
status
: 
200
timestamp
: 
"2025-09-11T04:27:10.068Z"
"""

## Response
"""
{
    "codeNum": 0,
    "code": "extract.pdf.pages.success",
    "data": {
        "fileId": "0d39727e-3cfe-3e8f-ba85-8e9da428eaee",
        "fileName": "TLAW1202000180_TP.PDF",
        "created": "2025-09-11T04:25:57.378336417Z",
        "createdEpoch": "1757564757378",
        "fileSize": 1986308,
        "numOfPages": 120
    },
    "timestamp": "2025-09-11T04:27:10.068Z",
    "status": 200
}
"""

# 3. 웹에서 확인하기?

## Headers
"""
Request URL
http://172.19.2.164/studio-lite/api/v1/dl/files/0d39727e-3cfe-3e8f-ba85-8e9da428eaee/visualinfo?engine=pdf_ai_dl&ocrMode=AUTO
Request Method
GET
Status Code
200 OK
Remote Address
172.19.2.164:80
Referrer Policy
strict-origin-when-cross-origin
cache-control
no-cache
connection
keep-alive
content-type
application/json
date
Thu, 11 Sep 2025 04:31:47 GMT
server
nginx/1.29.1
transfer-encoding
chunked
accept
application/json, text/plain, */*
accept-encoding
gzip, deflate
accept-language
ko-KR,ko;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6
connection
keep-alive
host
172.19.2.164
referer
http://172.19.2.164/studio-lite/0d39727e-3cfe-3e8f-ba85-8e9da428eaee/pdf_ai_dl?ocrMode=AUTO
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
"""

## Payload
"""
engine
pdf_ai_dl
ocrMode
AUTO
"""

## Preview
"""
"""

## Response
"""
파일이 너무커서

result.json에 저장해두었어
"""


# 4. 내보내기

## Headers
"""
Request URL
http://172.19.0.35/studio-lite/api/v1/dl/files/3136218e-3349-3042-8608-5f588446b26a/visualinfo-filltext?engine=pdf_ai_dl&ocrMode=AUTO
Request Method
POST
Status Code
200 OK
Remote Address
172.19.0.35:80
Referrer Policy
strict-origin-when-cross-origin
cache-control
no-cache
connection
keep-alive
content-type
application/json
date
Thu, 11 Sep 2025 08:32:25 GMT
server
nginx/1.29.1
transfer-encoding
chunked
accept
application/json, text/plain, */*
accept-encoding
gzip, deflate
accept-language
ko-KR,ko;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6
connection
keep-alive
content-length
1509792
content-type
application/json
host
172.19.0.35
origin
http://172.19.0.35
referer
http://172.19.0.35/studio-lite/3136218e-3349-3042-8608-5f588446b26a/pdf_ai_dl?ocrMode=AUTO
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
"""

## Payload

"""
engine
pdf_ai_dl
ocrMode
AUTO
{"elementIds":[],"visualinfo":{"runtime":282402,"version":"1.0.0","metadata":{"fileId":"3136218e-3349-3042-8608-5f588446b26a","fileName":"TLAW1202000182_TP.PDF","created":"2025-09-11T07:55:37.895107543Z","updated":"2025-09-11T08:00:20.343991110Z","createdEpoch":"1757577337895","fileSize":2323010,"numOfPages":145,"engine":"pdf_ai_dl","ocrMode":"AUTO"},"elements":[{"id":"0","category":{"label":"PageHeader","type":"HEADER"},"level":1,"confidence":0.895335853099823,"content":{"text":"폭발위험물질에 관한 법률 [독일]","html":"<header>폭발위험물질에 관한 법률 [독일]</header>","markdown":"폭발위험물질에 관한 법률 [독일]"},"bbox":{"left":71.66889,"top":23.769583,"width":180.43274,"height":13.325373},"pageIndex":0},{"id":"1","category":{"label":"DocTitle","type":"HEADING"},"level":1,"confidence":0.9991416335105896,"content":{"text":"Gesetz über \nexplosionsgefährliche Stoffe \n(Sprengstoffgesetz - SprengG)","html":"<h1>Gesetz über explosionsgefährliche Stoffe (Sprengstoffgesetz - SprengG)</h1>","markdown":"# Gesetz über \nexplosionsgefährliche Stoffe \n(Sprengstoffgesetz - SprengG)"},"bbox":{"left":65.546425,"top":87.51528,"width":217.16754,"height":66.626854},"pageIndex":0},{"id":"2","category":{"label":"OtherText","type":"PARAGRAPH"},"level":2,"confidence":0.6143710613250732,"content":{"text":"usfertigungsdatum: 13.09.1976","html":"<p>usfertigungsdatum: 13.09.1976</p>","markdown":"usfertigungsdatum: 13.09.1976"},"bbox":{"left":61.944973,"top":175.03056,"width":166.38707,"height":11.884781},"pageIndex":0},{"id":"3","category":{"label":"ParaText","type":"PARAGRAPH"},"level":2,"confidence":0.993221879005432,"content":{"text":"Vollzitat:","html":"<p>Vollzitat:</p>","markdown":"Vollzitat:"},"bbox":{"left":61.584827,"top":205.6429,"width":44.658,"height":10.804352},"pageIndex":0},{"id":"4","category":{"label":"ParaText","type":"PARAGRAPH"},"level":2,"confidence":0.999877393245697,"content":{"text":"\"Sprengstoffgesetz in der Fassung der \nBekanntmachung vom 10. September 2002 \n(BGBl. I S. 3518), das zuletzt durch Artikel\n4a des Gesetzes vom 17. Februar 2020 \n(BGBl. I S. 166) geändert worden ist\"","html":"<p>\"Sprengstoffgesetz in der Fassung der Bekanntmachung vom 10. September 2002 (BGBl. I S. 3518), das zuletzt durch Artikel 4a des Gesetzes vom 17. Februar 2020 (BGBl. I S. 166) geändert worden ist\"</p>","markdown":"\"Sprengstoffgesetz in der Fassung der \nBekanntmachung vom 10. September 2002 \n(BGBl. I S. 3518), das zuletzt durch Artikel\n4a des Gesetzes vom 17. Februar 2020 \n(BGBl. I S. 166) geändert worden ist\""},"bbox":{"left":61.584827,"top":235.8951,"width":222.20958,"height":86.07469},"pageIndex":0},{"id":"5","category":{"label":"ParaText","type":"PARAGRAPH"},"level":2,"confidence":0.99983549118042,"content":{"text":"Stand: Neugefasst durch Bek. v. 10.9.2002 \nI 3518;","html":"<p>Stand: Neugefasst durch Bek. v. 10.9.2002 I 3518;</p>","markdown":"Stand: Neugefasst durch Bek. v. 10.9.2002 \nI 3518;"},"bbox":{"left":61.584827,"top":341.0575,"width":218.24797,"height":29.171753},"pageInShow more
"""

Response

"""

"""