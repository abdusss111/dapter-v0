let wsTab;
let mediaRecorderTab;

function startTabTranscription() {
  chrome.tabCapture.capture({ audio: true, video: false }, (stream) => {
    if (!stream) return console.error("❌ Tab capture failed");

    wsTab = new WebSocket("ws://localhost:8000/ws/transcribe/tab");

    wsTab.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      console.log("[TAB]", msg);
    };

    mediaRecorderTab = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });

    mediaRecorderTab.ondataavailable = async (e) => {
      if (e.data.size > 0 && wsTab.readyState === WebSocket.OPEN) {
        const arrayBuffer = await e.data.arrayBuffer();
        wsTab.send(arrayBuffer);
      }
    };

    mediaRecorderTab.start(250);
  });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "start-tab-capture") {
    startTabTranscription();
  }
});
