// motionDetection.js - Handles Accelerometer for Fall and Shake detection
let shakeDetectedFlag = 0;
let fallDetectedFlag = 0;
let runningDetectedFlag = 0;

function initMotionDetection() {
    const motionStatus = document.getElementById("motion-status");
    const motionDot = document.getElementById("motion-dot");

    if (typeof DeviceMotionEvent === 'undefined') {
        motionStatus.innerHTML = "Motion sensor not supported (DeviceMotionEvent)";
        return;
    }

    // Need permission for iOS 13+
    if (typeof DeviceMotionEvent.requestPermission === 'function') {
        DeviceMotionEvent.requestPermission()
            .then(permissionState => {
                if (permissionState === 'granted') {
                    startTracking(motionStatus, motionDot);
                } else {
                    motionStatus.innerHTML = "Permission denied";
                    motionDot.className = "dot danger";
                }
            })
            .catch(console.error);
    } else {
        startTracking(motionStatus, motionDot);
    }
}

function startTracking(statusEl, dotEl) {
    statusEl.innerHTML = "Monitoring accelerometer...";
    dotEl.className = "dot active";

    let lastX = 0, lastY = 0, lastZ = 0;
    let shakeCount = 0;
    const SHAKE_THRESHOLD = 15;
    const FALL_THRESHOLD = 2.0; // Near zero gravity then impact
    const RUNNING_THRESHOLD = 12;

    window.addEventListener('devicemotion', (event) => {
        let acc = event.accelerationIncludingGravity;
        if (!acc || acc.x === null) return;

        let deltaX = Math.abs(acc.x - lastX);
        let deltaY = Math.abs(acc.y - lastY);
        let deltaZ = Math.abs(acc.z - lastZ);

        let totalAcceleration = Math.sqrt(acc.x * acc.x + acc.y * acc.y + acc.z * acc.z);
        let totalDelta = deltaX + deltaY + deltaZ;

        // Shake Detection (Violent continuous shaking)
        if (totalDelta > SHAKE_THRESHOLD) {
            shakeCount++;
            if (shakeCount > 5) { // Needs sustained shake
                console.warn("📳 SHAKE DETECTED!");
                shakeDetectedFlag = 1;
                statusEl.innerHTML = "Violent Shaking Detected!";
                dotEl.className = "dot danger";
                setTimeout(() => { shakeDetectedFlag = 0; shakeCount = 0; }, 5000);
            }
        } else {
            shakeCount = Math.max(0, shakeCount - 1);
        }

        // Fall Detection (Freefall detected - near 0g - followed by impact)
        // Note: Simple heuristic for prototype
        if (totalAcceleration < FALL_THRESHOLD) {
            console.warn("🔻 FREEFALL DETECTED (Possible Drop or Fall)");
            fallDetectedFlag = 1;
            statusEl.innerHTML = "Sudden Fall/Drop Detected!";
            dotEl.className = "dot danger";
            setTimeout(() => { fallDetectedFlag = 0; }, 8000);
        }

        // Running Detection (Continuous fast motion but not violent shake)
        if (totalDelta > RUNNING_THRESHOLD && totalDelta < SHAKE_THRESHOLD && shakeCount < 3) {
            runningDetectedFlag = 1;
            setTimeout(() => { runningDetectedFlag = 0; }, 3000);
        }

        // Reset UI if no flags
        if (shakeDetectedFlag === 0 && fallDetectedFlag === 0) {
            statusEl.innerHTML = "Monitoring accelerometer...";
            dotEl.className = "dot active";
        }

        lastX = acc.x;
        lastY = acc.y;
        lastZ = acc.z;
    });
}

// Expose flags
window.getMotionSensorData = () => ({
    shake: shakeDetectedFlag,
    fall: fallDetectedFlag,
    run: runningDetectedFlag
});
