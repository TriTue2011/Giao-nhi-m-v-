import base64, io, json, shutil, socket, subprocess, sys, tempfile, time, urllib.request
import numpy as np
sys.path.insert(0, "/tmp/claude-0/-opt-claude-c2a/ba994edd-3966-48b1-98dc-16c64d07bc5e/scratchpad/w2a/test")
from ui_chung import CDP
from PIL import Image
with socket.socket() as s: s.bind(("127.0.0.1",0)); cong=s.getsockname()[1]
ho=tempfile.mkdtemp(prefix="cdp-rig-")
p=subprocess.Popen(["/usr/bin/google-chrome","--headless=new","--no-sandbox","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader",f"--remote-debugging-port={cong}",f"--user-data-dir={ho}","about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
mo=urllib.request.build_opener(urllib.request.ProxyHandler({})); ws=None
for _ in range(200):
    try: ws=json.loads(mo.open(f"http://127.0.0.1:{cong}/json/version",timeout=1).read())["webSocketDebuggerUrl"]; break
    except OSError: time.sleep(0.05)
c=CDP(ws); tid=c.goi("Target.createTarget",{"url":"about:blank"})["targetId"]; se=c.goi("Target.attachToTarget",{"targetId":tid,"flatten":True})["sessionId"]
G=lambda m,pa=None:c.goi(m,pa,se)
G("Emulation.setDeviceMetricsOverride",{"width":720,"height":659,"deviceScaleFactor":1,"mobile":False}); G("Page.navigate",{"url":"http://127.0.0.1:8791/cat/rig.html"})
js=lambda e:G("Runtime.evaluate",{"expression":e,"awaitPromise":True,"returnByValue":True})
for _ in range(100):
    if js("window.san===1")["result"].get("value"): break
    time.sleep(0.1)
CK=1.2; N=int(CK*60)*2          # hai chu kỳ ở 60 khung/giây, chu kỳ 1,2 s
fr=[]
for k in range(N):
    js(f"ve({k/60/CK})"); r=G("Page.captureScreenshot",{"format":"png"}); fr.append(np.asarray(Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("L"),dtype=np.float32))
d=np.array([np.abs(fr[i+1]-fr[i]).mean() for i in range(N-1)])
print("khung có đổi hình: %d/%d | TB %.2f | lớn nhất %.2f | hệ số biến thiên %.2f | lớn nhất/trung vị %.2f"%((d>0.05).sum(),N-1,d.mean(),d.max(),d.std()/d.mean(),d.max()/np.median(d)))
print("chu kỳ lặp khít: khung cuối → khung đầu sai khác %.2f (so với TB %.2f)"%(np.abs(fr[-1]-fr[0]).mean(),d.mean()))
c.dong(); p.kill(); p.wait(10); shutil.rmtree(ho,ignore_errors=True)
