// app.js (frontend)
const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const transcriptEl = document.getElementById('transcript');
const responseEl = document.getElementById('response');
const presetSelect = document.getElementById('preset');

let recognition;
let isRecording = false;

function supportsSpeechRecognition() {
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

function speak(text) {
  if (!text) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'en-US';
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

async function sendToServer(message) {
  responseEl.textContent = 'Thinking...';
  try {
    const persona = { system: defaultPersonaForPreset(presetSelect.value) };
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, persona })
    });
    const data = await resp.json();
    if (data?.text) {
      responseEl.textContent = data.text;
      speak(data.text);
    } else {
      responseEl.textContent = 'No response from server.';
    }
  } catch (err) {
    console.error(err);
    responseEl.textContent = 'Error contacting server.';
  }
}

function defaultPersonaForPreset(preset) {
  if (preset === 'short') {
    return 'You are concise and respond in one short sentence. Friendly tone.';
  } else if (preset === 'detailed') {
    return 'You provide a helpful, 2-3 sentence detailed response with a friendly tone.';
  }
  return `You are a friendly, human-sounding voice assistant representing the candidate. Prefer concision but expand if user explicitly asks for more. Use the candidate answers when the user asks: 
- life story -> "${CANDIDATE_ANSWERS.life_story}"
- superpower -> "${CANDIDATE_ANSWERS.superpower}"
- top growth areas -> "${CANDIDATE_ANSWERS.top_growth}"
- misconception -> "${CANDIDATE_ANSWERS.misconception}"
- push boundaries -> "${CANDIDATE_ANSWERS.push_boundaries}"
Keep tone confident and approachable.`;
}

const CANDIDATE_ANSWERS = {
  life_story: "I grew up fascinated by data and football, studied data science, and have built machine-learning features for products that millions use.",
  superpower: "Pattern recognition — I quickly spot trends in messy data and turn them into actionable plans.",
  top_growth: "1) Public speaking and storytelling with data, 2) Real-time systems engineering, 3) Advanced deep learning for sequence models.",
  misconception: "People sometimes think I prefer solo work, but I actually push collaboration and open communication.",
  push_boundaries: "I set small weekly stretch goals and pair with people who challenge my assumptions to learn faster."
};

if (!supportsSpeechRecognition()) {
  transcriptEl.textContent = 'Speech Recognition not supported in this browser. Use Chrome on desktop for best results.';
} else {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isRecording = true;
    recordBtn.disabled = true;
    stopBtn.disabled = false;
    transcriptEl.textContent = 'Listening...';
  };

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    transcriptEl.textContent = text;
    sendToServer(text);
  };

  recognition.onerror = (event) => {
    transcriptEl.textContent = 'Recognition error: ' + event.error;
  };

  recognition.onend = () => {
    isRecording = false;
    recordBtn.disabled = false;
    stopBtn.disabled = true;
  };
}

recordBtn.addEventListener('click', () => {
  if (!recognition) return;
  window.speechSynthesis.cancel();
  recognition.start();
});

stopBtn.addEventListener('click', () => {
  if (!recognition) return;
  recognition.stop();
});
