// voiceDetection.js - Handles Web Speech API for danger keywords

let voiceDetectedFlag = 0;
let loudNoiseDetectedFlag = 0;
let recognition = null;

const DANGER_KEYWORDS = [
    "help", "help me", "save me", "danger", "stop", "please help", "leave me", "someone help", "emergency"
];

function initVoiceDetection() {
    const voiceStatus = document.getElementById("voice-status");
    const voiceDot = document.getElementById("voice-dot");

    // Check Audio Context for Loud Noise
    initLoudNoiseDetection();

    // Check Speech Recognition for Keywords
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        voiceStatus.textContent = "Speech API not supported";
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        voiceStatus.textContent = "Listening for keywords...";
        voiceDot.className = "dot active";
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript.toLowerCase();
            } else {
                interimTranscript += event.results[i][0].transcript.toLowerCase();
            }
        }

        const currentSpeech = finalTranscript + interimTranscript;
        console.log("Speech heard:", currentSpeech);

        // Check for danger keywords
        for (const keyword of DANGER_KEYWORDS) {
            if (currentSpeech.includes(keyword)) {
                console.warn(`🚨 DANGER KEYWORD DETECTED: '${keyword}'`);
                voiceDetectedFlag = 1;
                voiceStatus.textContent = `Danger detected: '${keyword}'!`;
                voiceDot.className = "dot danger";

                // Keep flag high for a bit, then reset
                setTimeout(() => {
                    voiceDetectedFlag = 0;
                    voiceStatus.textContent = "Listening...";
                    voiceDot.className = "dot active";
                }, 10000);
                break;
            }
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        voiceStatus.textContent = `Error: ${event.error}`;
        voiceDot.className = "dot inactive";
    };

    recognition.onend = () => {
        // Restart automatically if it stops
        try {
            recognition.start();
        } catch (e) { }
    };

    recognition.start();
}

// ----------------- Loud Noise Detection (Web Audio API) -----------------
let audioContext;
let microphone;
let analyser;

async function initLoudNoiseDetection() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);

        analyser.fftSize = 256;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function checkVolume() {
            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            let average = sum / bufferLength;

            // Threshold for loud noise (scream/yell)
            if (average > 100) {
                loudNoiseDetectedFlag = 1;
                console.warn("🔊 LOUD NOISE SPIKE DETECTED!");
                setTimeout(() => { loudNoiseDetectedFlag = 0; }, 5000);
            }

            requestAnimationFrame(checkVolume);
        }

        checkVolume();
        console.log("Audio Level Monitoring Started.");

    } catch (err) {
        console.error("Microphone access denied for volume check.", err);
    }
}

// Expose flags
window.getVoiceSensorData = () => ({
    voice_detected: voiceDetectedFlag,
    loud_noise: loudNoiseDetectedFlag
});
