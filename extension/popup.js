document.getElementById("start").addEventListener("click", async () => {
  // 1. Inject mic capture into Meet tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["content.js"]
  });

  // 2. Start tab audio transcription with auto-restart
  startTabTranscription();
});

let tabStream;
let wsTab;
let mediaRecorderTab;

async function startTabTranscription() {
  console.log("🎧 Starting tab transcription...");

  if (wsTab) wsTab.close();

  if (!tabStream) {
    tabStream = await new Promise((resolve, reject) => {
      chrome.tabCapture.capture({ audio: true, video: false }, (stream) => {
        if (stream) resolve(stream);
        else reject("❌ Tab capture failed");
      });
    });
  }

  wsTab = new WebSocket("ws://localhost:8000/ws/transcribe/tab");

  wsTab.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log("[TAB]", msg);
  };

  wsTab.onopen = () => {
    console.log("🟢 Tab WebSocket connected");

    mediaRecorderTab = new MediaRecorder(tabStream, { mimeType: "audio/webm;codecs=opus" });

    mediaRecorderTab.ondataavailable = async (e) => {
      if (e.data.size > 0 && wsTab.readyState === WebSocket.OPEN) {
        const arrayBuffer = await e.data.arrayBuffer();
        wsTab.send(arrayBuffer);
      }
    };

    mediaRecorderTab.start(250);

    // 🔁 Restart after 290 seconds
    setTimeout(() => {
      console.log("🔁 Restarting tab stream...");
      mediaRecorderTab.stop();
      wsTab.close();
      startTabTranscription(); // Recursively restart
    }, 290000);
  };

  wsTab.onclose = () => {
    console.log("🔴 Tab WebSocket closed");
  };
}
