// location.js - Handles Real-Time Location Tracking

let userLocation = {
    lat: null,
    lng: null,
    timestamp: null
};

function initLocation() {
    const locStatus = document.getElementById("loc-status");
    const locDot = document.getElementById("loc-dot");

    if (!navigator.geolocation) {
        locStatus.textContent = "Geolocation not supported";
        locDot.className = "dot inactive";
        return;
    }

    navigator.geolocation.watchPosition(
        (position) => {
            userLocation.lat = position.coords.latitude;
            userLocation.lng = position.coords.longitude;
            userLocation.timestamp = new Date().toISOString();
            
            locStatus.textContent = `Tracking Active (${userLocation.lat.toFixed(4)}, ${userLocation.lng.toFixed(4)})`;
            locDot.className = "dot active";

            // In a real app, integrate Google Maps or Leaflet properly here
            const mapDiv = document.getElementById("map");
            mapDiv.innerHTML = `<iframe 
                width="100%" 
                height="100%" 
                style="border:0; border-radius:12px;" 
                loading="lazy" 
                allowfullscreen 
                src="https://maps.google.com/maps?q=${userLocation.lat},${userLocation.lng}&z=15&output=embed">
            </iframe>`;
        },
        (error) => {
            console.error("Error getting location:", error);
            locStatus.textContent = "Location access denied";
            locDot.className = "dot danger";
        },
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
    );
}

// Expose location to other scripts
window.getUserLocation = () => userLocation;
