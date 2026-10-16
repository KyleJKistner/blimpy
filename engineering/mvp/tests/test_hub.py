import json, threading, unittest, urllib.request, urllib.error
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from host.hub import Device,make_handler,extract_response_text
TOKEN="a"*32
class MockDevice:
    def __init__(self):self.calls=[]
    def request(self,path,data=None,**kw):
        self.calls.append((path,data))
        return {"/status":(b'{"mode":"bench-only"}',"application/json"),
                "/capture":(b"\xff\xd8fakejpeg","image/jpeg"),
                "/record":(b"RIFFfakewav","audio/wav"),
                "/play":(b"played","text/plain")}[path]
class HubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.device=MockDevice()
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(cls.device,TOKEN,"test-not-a-real-key","test-model"))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f"http://127.0.0.1:{cls.server.server_port}"
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,path,data=None,auth=True):
        headers={"Content-Type":"application/json"}
        if auth:headers["X-Hub-Token"]=TOKEN
        r=urllib.request.Request(self.base+path,data=None if data is None else json.dumps(data).encode(),headers=headers)
        return urllib.request.urlopen(r,timeout=3)
    def test_public_page(self):
        with self.request("/",auth=False) as r:self.assertIn(b"no flight controls",r.read())
    def test_media_auth(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.request("/api/capture",auth=False)
        self.assertEqual(e.exception.code,401)
    def test_status(self):
        with self.request("/api/status") as r:self.assertEqual(json.load(r)["mode"],"bench-only")
    def test_camera(self):
        with self.request("/api/capture") as r:self.assertEqual(r.headers.get_content_type(),"image/jpeg")
    def test_record(self):
        with self.request("/api/record",{}) as r:self.assertTrue(r.read().startswith(b"RIFF"))
    def test_no_cloud_without_consent(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.request("/api/ask",{"text":"test"})
        self.assertEqual(e.exception.code,400)
    @patch("host.hub.ask_cloud",return_value="A foam block is visible.")
    def test_mocked_cloud_question(self,m):
        with self.request("/api/ask",{"text":"What is visible?","cloud_consent":True,"use_camera":True}) as r:
            self.assertIn("foam",json.load(r)["answer"])
        m.assert_called_once()
    @patch("host.hub.synthesize",return_value=b"\0\0"*100)
    @patch("host.hub.ask_cloud",return_value="A block.")
    @patch("host.hub.transcribe",return_value="What is that?")
    def test_mocked_voice_roundtrip(self,stt,llm,tts):
        with self.request("/api/talk",{"cloud_consent":True,"speak":True}) as r:
            data=json.load(r);self.assertEqual(data["transcript"],"What is that?")
        self.assertTrue(any(p=="/play" for p,_ in self.device.calls))
    def test_no_motor_endpoint(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.request("/api/motor",{})
        self.assertEqual(e.exception.code,404)
    def test_device_config(self):
        for base,token in [("file:///tmp/foo",TOKEN),("http://127.0.0.1","short")]:
            with self.assertRaises(ValueError):Device(base,token)
    def test_extract_text(self):
        self.assertEqual(extract_response_text({"output":[{"type":"message","content":[{"type":"output_text","text":"ok"}]}]}),"ok")
