// riskEngine.js - Orchestrates Sensor Data and AI Model Polling

let pollingInterval;
let checkinModalTimeout;
let modalOpen = false;

function initRiskEngine() {
    const btnEnable = document.getElementById("enable-sensors-btn");

    btnEnable.addEventListener("click", () => {
        initLocation();
        initVoiceDetection();
        initMotionDetection();
        initSOS();

        btnEnable.style.display = 'none';

        // Start polling risk level every 5 seconds
        pollingInterval = setInterval(evaluateRisk, 5000);
        console.log("Safety systems armed and risk engine started.");
    });

    // Checkin modal buttons
    document.getElementById("safe-btn").addEventListener("click", () => { closeCheckBox(true); });
    document.getElementById("danger-btn").addEventListener("click", () => { closeCheckBox(false); });
}

function evaluateRisk() {
    if (modalOpen) return; // Don't evaluate new risk while they are answering a prompt

    const voiceData = window.getVoiceSensorData ? window.getVoiceSensorData() : { voice_detected: 0, loud_noise: 0 };
    const motionData = window.getMotionSensorData ? window.getMotionSensorData() : { shake: 0, fall: 0, run: 0 };

    // Calculate Risk Points
    let riskPoints = 0;
    let anomalyMessages = [];

    // Voice & Audio (High Weight)
    if (voiceData.voice_detected) {
        riskPoints += 40;
        anomalyMessages.push("Danger Keyword");
    }
    if (voiceData.loud_noise) {
        riskPoints += 20;
        anomalyMessages.push("Loud Noise Spike");
    }

    // Motion (Medium/High Weight)
    if (motionData.shake) {
        riskPoints += 30;
        anomalyMessages.push("Violent Shaking");
    }
    if (motionData.fall) {
        riskPoints += 35;
        anomalyMessages.push("Fall Detected");
    }
    if (motionData.run) {
        riskPoints += 15;
        anomalyMessages.push("Running Detected");
    }

    // Time/Context (Low Weight mock)
    const hour = new Date().getHours();
    if (hour >= 22 || hour <= 4) {
        riskPoints += 5; // Late night adds baseline risk
    }

    console.log(`Risk Evaluation: Points = ${riskPoints}`, anomalyMessages);

    // Classify Risk Level
    let riskLevel = "LOW";
    if (riskPoints >= 50) {
        riskLevel = "HIGH";
    } else if (riskPoints >= 20) {
        riskLevel = "MEDIUM";
    }

    updateRiskUI(riskLevel, riskPoints);
    handleRiskThresholds(riskLevel, anomalyMessages);
}

function updateRiskUI(level, points) {
    const riskEl = document.getElementById("risk-level");
    const subtextEl = document.querySelector(".risk-subtext");

    riskEl.textContent = level;
    riskEl.className = '';

    if (level === 'LOW') {
        riskEl.classList.add('risk-low');
        subtextEl.textContent = "No danger detected yet.";
    }
    else if (level === 'MEDIUM') {
        riskEl.classList.add('risk-medium');
        subtextEl.textContent = "Unusual activity detected (" + points + " pts).";
    }
    else if (level === 'HIGH') {
        riskEl.classList.add('risk-high');
        subtextEl.textContent = "DANGER DETECTED (" + points + " pts).";
    }
}

function handleRiskThresholds(level, anomalies) {
    if (level === 'HIGH') {
        console.warn("⚠️ HIGH RISK DETECTED - TRIGGERING AUTOMATIC SOS!");
        triggerAutoAlert("HIGH (AI POINTS DETECTION: " + anomalies.join(", ") + ")");
    }
    else if (level === 'MEDIUM') {
        if (!modalOpen) {
            openCheckInBox();
        }
    }
}

function triggerAutoAlert(levelStr) {
    const loc = window.getUserLocation();
    const payload = {
        risk_level: levelStr,
        lat: loc.lat,
        lng: loc.lng
    };

    fetch(window.flaskConfig.alertApiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    }).then(res => res.json()).then(data => {
        console.log("Auto-Alert sent successfully.", data);

        // Show alerted contacts on UI
        const statusText = document.getElementById("sos-status");
        if (statusText) {
            let alertedInfo = "Emergency Contacts";
            if (data.alerted_contacts && data.alerted_contacts.length > 0) {
                alertedInfo = data.alerted_contacts.join("<br>📞 ");
                alertedInfo = "📞 " + alertedInfo;
            }
            statusText.style.color = "var(--sos-red)";
            statusText.innerHTML = `AI Auto-Alert Sent to:<br/>${alertedInfo}`;
            setTimeout(() => { statusText.innerHTML = ""; }, 10000);
        }
    });
}

// ---------------- Check-In Modal Logic ----------------

function openCheckInBox() {
    modalOpen = true;
    const modal = document.getElementById("checkin-modal");
    const countSpan = document.getElementById("countdown");
    modal.style.display = "block";

    let countdown = 15;
    countSpan.textContent = countdown;

    checkinModalTimeout = setInterval(() => {
        countdown--;
        countSpan.textContent = countdown;
        if (countdown <= 0) {
            clearInterval(checkinModalTimeout);
            closeCheckBox(false); // Default to Danger if no response!
        }
    }, 1000);
}

function closeCheckBox(isSafe) {
    clearInterval(checkinModalTimeout);
    document.getElementById("checkin-modal").style.display = "none";
    modalOpen = false;

    if (!isSafe) {
        console.log("User indicated Danger or did not respond - Elevating to HIGH risk alert!");
        triggerAutoAlert("HIGH (NO RESPONSE TO CHECK-IN)");
    } else {
        console.log("User confirmed safe. Resetting sensors.");
        updateRiskUI("LOW", 0);
        document.querySelector(".risk-subtext").textContent = "User marked as safe.";
        // Optionally reset local flags here by calling functions in those files if they existed
        if (typeof voiceDetectedFlag !== 'undefined') voiceDetectedFlag = 0;
        if (typeof loudNoiseDetectedFlag !== 'undefined') loudNoiseDetectedFlag = 0;
        if (typeof shakeDetectedFlag !== 'undefined') shakeDetectedFlag = 0;
        if (typeof fallDetectedFlag !== 'undefined') fallDetectedFlag = 0;
    }
}

// ---------------- Share Location Logic ----------------
function initShareLocation() {
    const shareBtn = document.getElementById("share-loc-btn");
    const statusTxt = document.getElementById("share-loc-status");

    if (!shareBtn) return;

    shareBtn.addEventListener("click", () => {
        const loc = window.getUserLocation ? window.getUserLocation() : { lat: null, lng: null };
        statusTxt.style.display = "block";
        statusTxt.textContent = "Sharing...";

        const payload = {
            risk_level: "INFO (LOCATION_SHARED)",
            lat: loc.lat,
            lng: loc.lng
        };

        fetch(window.flaskConfig.alertApiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            console.log("Location shared.", data);
            statusTxt.textContent = "Location Shared!";
            setTimeout(() => { statusTxt.style.display = "none"; }, 5000);
        }).catch(err => {
            statusTxt.textContent = "Failed to share.";
            setTimeout(() => { statusTxt.style.display = "none"; }, 5000);
        });
    });
}

// Initialize when DOM loads
document.addEventListener("DOMContentLoaded", () => {
    initRiskEngine();
    initShareLocation();
});
