// CalmCompanion Voice PWA
const q = new URLSearchParams(location.search);
const sid = q.get("sid") || "demo1";
const backend = q.get("api") || "http://localhost:8000";
document.getElementById("sid").textContent = sid;
document.getElementById("backend").textContent = (new URL(backend)).host;

const micBtn = document.getElementById("mic");
const transcriptEl = document.getElementById("transcript");
const riskbar = document.getElementById("riskbar");
const triggersEl = document.getElementById("triggers");
const tipsEl = document.getElementById("tips");

let recog;
let listening = false;

function initSTT(){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){ alert("SpeechRecognition not supported in this browser."); return; }
  recog = new SR();
  recog.lang = "en-US";
  recog.interimResults = true;
  recog.continuous = true;
  recog.onresult = (e)=>{
    let text = "";
    for(let i= e.resultIndex; i< e.results.length; i++){
      text += e.results[i][0].transcript;
    }
    transcriptEl.textContent = text.trim();
  };
  recog.onerror = (e)=> console.warn("STT error", e);
}

function speak(text){
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 0.95;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

async function sendToAPI(text){
  const body = { sid, text, timestamp: new Date().toISOString() };
  const res = await fetch(`${backend}/api/voice_chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  const pct = Math.max(0, Math.min(1, data.risk)) * 100;
  riskbar.style.width = `${pct}%`;
  triggersEl.innerHTML = "";
  Object.entries(data.triggers || {}).forEach(([k,v])=>{
    if(v){
      const span = document.createElement("span");
      span.className = "badge";
      span.textContent = k;
      triggersEl.appendChild(span);
    }
  });
  tipsEl.innerHTML = "";
  (data.tips || []).forEach(t=>{
    const s = document.createElement("span");
    s.className = "badge";
    s.textContent = t.title;
    tipsEl.appendChild(s);
  });
  speak(data.reply || "I'm here with you.");
}

micBtn.addEventListener("mousedown", ()=>{
  if(!recog) initSTT();
  listening = true;
  transcriptEl.textContent = "Listening…";
  try{ recog.start(); } catch(e){}
});
async function stopAndSend(){
  if(recog){ try{ recog.stop(); } catch(e){} }
  listening = false;
  const text = transcriptEl.textContent.trim();
  if(text){ await sendToAPI(text); }
}
micBtn.addEventListener("mouseup", stopAndSend);
micBtn.addEventListener("mouseleave", ()=>{ if(listening) stopAndSend(); });
micBtn.addEventListener("touchstart", (e)=>{ e.preventDefault(); micBtn.dispatchEvent(new Event("mousedown")); });
micBtn.addEventListener("touchend", (e)=>{ e.preventDefault(); micBtn.dispatchEvent(new Event("mouseup")); });

if("speechSynthesis" in window){
  speak("Hello. I am here with you.");
} else {
  alert("Speech Synthesis not supported.");
}
