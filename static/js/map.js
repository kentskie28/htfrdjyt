document.addEventListener("DOMContentLoaded", function () {
    const urlParams = new URLSearchParams(window.location.search);
    let initialLat = parseFloat(urlParams.get("lat"));
    let initialLon = parseFloat(urlParams.get("lon"));
    let destination = urlParams.get("destination");

    // Default to university coordinates if not provided
    if (isNaN(initialLat) || isNaN(initialLon)) {
        initialLat = 11.4567; // Replace with your university's latitude
        initialLon = 123.4567; // Replace with your university's longitude
    }

    // Initialize the map first
    const map = L.map("map").setView([initialLat, initialLon], 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    let userMarker = L.marker([initialLat, initialLon]).addTo(map).bindPopup("You are here!").openPopup();

    let destinationMarker, destinationCircle;
    let destinationsData = [];

    // Fetch destinations and populate dropdown
    fetch("/static/destinations.json")
        .then((response) => response.json())
        .then((data) => {
            destinationsData = data.destinations;

            const destinationSelect = document.getElementById("destination-select");
            destinationsData.forEach((dest) => {
                const option = document.createElement("option");
                option.value = dest.name.toLowerCase().trim();
                option.textContent = dest.name;
                destinationSelect.appendChild(option);
            });

            if (destination && destination !== "null") {
                updateDestination(destination.toLowerCase().trim());
                destinationSelect.value = destination.toLowerCase().trim();
            } else {
                alert("If there is no destination specified, please select your desired destination.");
            }

            destinationSelect.addEventListener("change", (event) => {
                updateDestination(event.target.value);
            });
        })
        .catch((error) => {
            console.error("Error fetching destinations:", error);
        });

    function updateDestination(destinationName) {
        if (!destinationName) return;

        const normalizedDestinationName = destinationName.toLowerCase().trim();

        const destinationData = destinationsData.find((dest) => {
            const normalizedNames = [dest.name.toLowerCase().trim(), ...dest.othername.map((n) => n.toLowerCase().trim())];
            return normalizedNames.includes(normalizedDestinationName);
        });

        if (destinationData) {
            const { destinationlat, destinationlon, accuracy = 30 } = destinationData;

            if (destinationMarker) destinationMarker.remove();
            if (destinationCircle) destinationCircle.remove();

            const imagePath = `/static/images/${destinationData.name.replace(/\s+/g, "_")}.jpg`;
            const popupContent = `
                <div>
                    <h4>Destination: ${destinationData.name}</h4>
                    <img src="${imagePath}" alt="${destinationData.name}" style="width:100px;height:auto;cursor:pointer;" onclick="openLightbox('${imagePath}')">
                </div>
            `;

            destinationMarker = L.marker([destinationlat, destinationlon])
                .addTo(map)
                .bindPopup(popupContent)
                .openPopup();

            destinationCircle = L.circle([destinationlat, destinationlon], { radius: accuracy }).addTo(map);

            const bounds = L.latLngBounds([[initialLat, initialLon], [destinationlat, destinationlon]]);
            map.fitBounds(bounds, { padding: [50, 50] });
        } else {
            alert("Destination not found.");
        }
    }

    // Request user location and update map
    if ("geolocation" in navigator) {
        navigator.geolocation.watchPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                userMarker.setLatLng([latitude, longitude]);
                map.setView([latitude, longitude], 13);
                sessionStorage.setItem("currentLocation", JSON.stringify({ latitude, longitude }));
            },
            (error) => {
                console.error("Error getting location:", error);
            },
            {
                enableHighAccuracy: true,
                maximumAge: 10000,
                timeout: 5000,
            }
        );
    } else {
        alert("Geolocation is not supported by your browser.");
    }

    // Lightbox functionality
    window.openLightbox = function (imagePath) {
        document.getElementById("lightbox-image").src = imagePath;
        document.getElementById("lightbox").style.display = "flex";
    };

    document.getElementById("close-lightbox").addEventListener("click", function () {
        document.getElementById("lightbox").style.display = "none";
    });
});
