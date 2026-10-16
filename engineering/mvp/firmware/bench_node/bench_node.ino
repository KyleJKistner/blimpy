/*
 * Camera / microphone / speaker BENCH NODE.
 * Target: XIAO ESP32S3 Sense; Arduino-ESP32 3.x; PSRAM enabled.
 * DRAFT: source-reviewed, NOT compiled or tested on physical hardware.
 * No motors. Private trusted LAN only: token authentication, but HTTP has no TLS.
 * SD slot MUST be empty: speaker pins share the SD bus.
 */
#include <WiFi.h>
#include <esp_camera.h>
#include <ESP_I2S.h>
#include <math.h>
#include "config.h"

WiFiServer server(80);
constexpr int LED_PIN=21; // XIAO user LED, active low; check actual board revision.
constexpr int AMP_SD=2;   // D1 to MAX98357A SD; add external 100k pull-down.
constexpr size_t MAX_PCM=24000*2*12; // 12 s, 24kHz, PCM16 mono.
constexpr size_t MAX_HEADERS=4096;
bool camera_ready=false;

void indicator(bool on) { digitalWrite(LED_PIN,on?LOW:HIGH); }
bool sendBytes(WiFiClient &c,const uint8_t *p,size_t n) {
  uint32_t deadline=millis()+10000;
  while(n && c.connected() && (int32_t)(deadline-millis())>0) {
    size_t w=c.write(p,n>1024?1024:n);
    if(w) {p+=w;n-=w;deadline=millis()+10000;} else delay(1);
  }
  return n==0;
}
void headers(WiFiClient &c,int code,const char *type,size_t len) {
  const char* reason=(code==200)?"OK":"Error";
  c.printf("HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %u\r\n"
           "Cache-Control: no-store\r\nConnection: close\r\n\r\n",
           code,reason,type,(unsigned)len);
}
void message(WiFiClient &c,int code,const char* text) {
  headers(c,code,"text/plain; charset=utf-8",strlen(text));
  sendBytes(c,(const uint8_t*)text,strlen(text));
}
bool initCamera() {
  camera_config_t cfg={};
  cfg.ledc_channel=LEDC_CHANNEL_0;cfg.ledc_timer=LEDC_TIMER_0;
  cfg.pin_d0=15;cfg.pin_d1=17;cfg.pin_d2=18;cfg.pin_d3=16;
  cfg.pin_d4=14;cfg.pin_d5=12;cfg.pin_d6=11;cfg.pin_d7=48;
  cfg.pin_xclk=10;cfg.pin_pclk=13;cfg.pin_vsync=38;cfg.pin_href=47;
  cfg.pin_sccb_sda=40;cfg.pin_sccb_scl=39;cfg.pin_pwdn=-1;cfg.pin_reset=-1;
  cfg.xclk_freq_hz=20000000;cfg.pixel_format=PIXFORMAT_JPEG;
  cfg.frame_size=FRAMESIZE_VGA;cfg.jpeg_quality=14;cfg.fb_count=1;
  cfg.fb_location=CAMERA_FB_IN_PSRAM;cfg.grab_mode=CAMERA_GRAB_WHEN_EMPTY;
  return esp_camera_init(&cfg)==ESP_OK;
}
void capture(WiFiClient &c) {
  if(!camera_ready){message(c,503,"Camera unavailable");return;}
  indicator(true);
  // Discard one queued frame so successive snapshots are not stale.
  camera_fb_t *old=esp_camera_fb_get();
  if(old)esp_camera_fb_return(old);
  camera_fb_t *fb=esp_camera_fb_get();
  if(!fb){indicator(false);message(c,503,"Capture failed");return;}
  headers(c,200,"image/jpeg",fb->len);
  sendBytes(c,fb->buf,fb->len);
  esp_camera_fb_return(fb);indicator(false);
}
void record(WiFiClient &c) {
  I2SClass mic;
  digitalWrite(AMP_SD,LOW);indicator(true);
  mic.setPinsPdmRx(42,41);
  if(!mic.begin(I2S_MODE_PDM_RX,16000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_MONO)){
    indicator(false);message(c,503,"Microphone initialization failed");return;
  }
  size_t len=0;
  uint8_t *wav=mic.recordWAV(4,&len);
  mic.end();indicator(false);
  if(!wav || len==0){if(wav)free(wav);message(c,503,"Recording failed");return;}
  headers(c,200,"audio/wav",len);sendBytes(c,wav,len);free(wav);
}
bool readExact(WiFiClient &c,uint8_t *out,size_t n) {
  uint32_t deadline=millis()+5000;
  size_t pos=0;
  while(pos<n && c.connected() && (int32_t)(deadline-millis())>0){
    int a=c.available();
    if(a>0){size_t want=n-pos;if(want>(size_t)a)want=a;
      int r=c.read(out+pos,want);
      if(r>0){pos+=(size_t)r;deadline=millis()+5000;}
    }else delay(1);
  }
  return pos==n;
}
void play(WiFiClient &c,size_t len) {
  if(len==0 || len>MAX_PCM || len%2){message(c,413,"PCM size invalid");return;}
  I2SClass audio;
  audio.setPins(7,8,9); // D8 BCLK, D9 LRCLK, D10 DIN
  if(!audio.begin(I2S_MODE_STD,24000,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_MONO)){
    message(c,503,"Speaker initialization failed");return;
  }
  uint8_t buffer[1024];
  digitalWrite(AMP_SD,HIGH);
  size_t remaining=len;bool ok=true;
  while(remaining && ok){
    size_t n=remaining>sizeof(buffer)?sizeof(buffer):remaining;
    ok=readExact(c,buffer,n);
    if(!ok)break;
    // Conservative amplitude attenuation. Still measure actual speaker power.
    for(size_t i=0;i<n;i+=2){
      int16_t sample=(int16_t)((uint16_t)buffer[i]|((uint16_t)buffer[i+1]<<8));
      sample/=8;buffer[i]=(uint8_t)sample;buffer[i+1]=(uint8_t)(sample>>8);
    }
    ok=audio.write(buffer,n)==n;remaining-=n;
  }
  digitalWrite(AMP_SD,LOW);audio.end();
  message(c,ok?200:408,ok?"played":"audio timeout/write failure");
}
void process(WiFiClient &c) {
  String head;head.reserve(1024);
  uint32_t deadline=millis()+5000;
  while(c.connected() && !head.endsWith("\r\n\r\n")){
    if(head.length()>=MAX_HEADERS){message(c,413,"Headers too large");return;}
    if((int32_t)(deadline-millis())<=0){message(c,408,"Header timeout");return;}
    if(c.available())head+=(char)c.read();else delay(1);
  }
  int lineend=head.indexOf("\r\n");
  if(lineend<0){message(c,400,"Malformed request");return;}
  String first=head.substring(0,lineend);
  int a=first.indexOf(' '), b=first.indexOf(' ',a+1);
  if(a<0||b<0){message(c,400,"Malformed request line");return;}
  String method=first.substring(0,a),path=first.substring(a+1,b),token="";
  long length=0;bool bad_length=false;bool saw_length=false;bool transfer_encoding=false;
  int pos=lineend+2;
  while(pos<(int)head.length()-2){
    int end=head.indexOf("\r\n",pos);if(end<0)break;
    String line=head.substring(pos,end);int colon=line.indexOf(':');
    if(colon>0){
      String key=line.substring(0,colon);key.toLowerCase();
      String value=line.substring(colon+1);value.trim();
      if(key=="x-device-token")token=value;
      if(key=="transfer-encoding")transfer_encoding=true;
      if(key=="content-length"){
        if(saw_length)bad_length=true;saw_length=true;
        if(value.length()==0)bad_length=true;
        for(unsigned i=0;i<value.length();i++)if(!isDigit(value[i]))bad_length=true;
        length=value.toInt();
        if(length<0||length>(long)MAX_PCM)bad_length=true;
      }
    }
    pos=end+2;
  }
  if(token!=DEVICE_TOKEN){message(c,401,"Unauthorized");return;}
  if(bad_length||transfer_encoding){message(c,400,"Unsupported body framing");return;}
  if(method=="GET" && path=="/status"){
    char body[192];
    snprintf(body,sizeof(body),
      "{\"mode\":\"bench-only\",\"camera_ready\":%s,\"rssi\":%d,\"free_heap\":%u}",
      camera_ready?"true":"false",WiFi.RSSI(),(unsigned)ESP.getFreeHeap());
    headers(c,200,"application/json",strlen(body));sendBytes(c,(uint8_t*)body,strlen(body));
  } else if(method=="GET" && path=="/capture")capture(c);
  else if(method=="POST" && path=="/record" && length==0)record(c);
  else if(method=="POST" && path=="/play")play(c,(size_t)length);
  else message(c,404,"No such bench endpoint");
}
void setup(){
  pinMode(AMP_SD,OUTPUT);digitalWrite(AMP_SD,LOW);
  pinMode(LED_PIN,OUTPUT);indicator(false);
  Serial.begin(115200);delay(1000);
  if(strlen(DEVICE_TOKEN)<24 || String(DEVICE_TOKEN).startsWith("REPLACE")){
    Serial.println("Set a private device token (24+ chars).");while(true)delay(1000);
  }
  if(!psramFound()){Serial.println("Enable PSRAM before use.");while(true)delay(1000);}
  camera_ready=initCamera();
  WiFi.mode(WIFI_STA);WiFi.setAutoReconnect(true);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  uint32_t start=millis();
  while(WiFi.status()!=WL_CONNECTED && millis()-start<30000)delay(250);
  server.begin();
  Serial.println("BENCH ONLY. No motors.");
  if(WiFi.status()==WL_CONNECTED)Serial.println(WiFi.localIP());
  else Serial.println("Wi-Fi not connected; automatic reconnection enabled.");
}
void loop(){
  WiFiClient client=server.available();
  if(client){process(client);digitalWrite(AMP_SD,LOW);indicator(false);client.stop();}
  delay(2);
}
