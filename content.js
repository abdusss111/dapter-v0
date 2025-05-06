let wsMic;
let mediaRecorder;
let micStream;

async function startMicTranscription() {
  if (wsMic) wsMic.close();

  if (!micStream) {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  }

  wsMic = new WebSocket("ws://localhost:8000/ws/transcribe/mic");

  wsMic.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log("[MIC]", msg);
  };

  wsMic.onopen = () => {
    mediaRecorder = new MediaRecorder(micStream, { mimeType: "audio/webm;codecs=opus" });

    mediaRecorder.ondataavailable = async (e) => {
      if (e.data.size > 0 && wsMic.readyState === WebSocket.OPEN) {
        const arrayBuffer = await e.data.arrayBuffer();
        wsMic.send(arrayBuffer);
      }
    };

    mediaRecorder.start(250);

    // Restart after 290s to stay under GSTT limit
    setTimeout(() => {
      console.log("🔁 Restarting mic stream...");
      mediaRecorder.stop();
      wsMic.close();
      startMicTranscription();
    }, 290000);
  };

  wsMic.onclose = () => {
    console.log("🔴 Mic WebSocket closed");
  };
}

startMicTranscription();
