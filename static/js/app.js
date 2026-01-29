// Global variables
let map;
let markers = [];
let homesData = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    loadGlobalData();
    setupFormSubmission();
});

// Initialize Leaflet map
function initMap() {
    // Center on the United States
    map = L.map('map-container').setView([37.8, -96], 4);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);
}

// Load global energy data and display on map
async function loadGlobalData() {
    try {
        const response = await fetch('/api/global-data');
        const data = await response.json();
        
        if (data.success) {
            homesData = data.homes;
            updateStats(data.stats);
            displayHomesOnMap(data.homes);
        }
    } catch (error) {
        console.error('Error loading global data:', error);
    }
}

// Update statistics in the stats bar
function updateStats(stats) {
    document.getElementById('total-homes').textContent = stats.total_homes.toLocaleString();
    document.getElementById('avg-energy').textContent = `${Math.round(stats.avg_energy)} kWh`;
    document.getElementById('cities').textContent = stats.cities;
}

// Display homes on the map with markers
function displayHomesOnMap(homes) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    homes.forEach(home => {
        const color = getEnergyColor(home.monthly_usage);
        
        const marker = L.circleMarker([home.latitude, home.longitude], {
            radius: 8,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);
        
        // Create popup content
        const popupContent = `
            <div style="min-width: 200px;">
                <h3 style="margin: 0 0 10px 0;">${home.location}</h3>
                <p style="margin: 5px 0;"><strong>Energy Usage:</strong> ${home.monthly_usage} kWh/month</p>
                <p style="margin: 5px 0;"><strong>Temperature:</strong> ${home.temperature}°C</p>
                <p style="margin: 5px 0;"><strong>Home Type:</strong> ${capitalizeFirst(home.home_type)}</p>
                <p style="margin: 5px 0;"><strong>Size:</strong> ${home.home_size} sq ft</p>
                <p style="margin: 5px 0;"><strong>Occupants:</strong> ${home.occupants}</p>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        markers.push(marker);
    });
}

// Get color based on energy usage
function getEnergyColor(usage) {
    if (usage < 500) return '#2ecc71';
    if (usage < 1000) return '#f39c12';
    return '#e74c3c';
}

// Setup form submission
function setupFormSubmission() {
    const form = document.getElementById('energy-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await findEnergyTwins();
    });
}

// Find energy twins using ML
async function findEnergyTwins() {
    // Show loading overlay
    document.getElementById('loading-overlay').style.display = 'flex';
    
    // Collect form data
    const formData = new FormData(document.getElementById('energy-form'));
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    try {
        const response = await fetch('/api/find-twins', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result.user_profile, result.twins, result.insights);
        } else {
            alert('Error finding energy twins: ' + result.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to find energy twins. Please try again.');
    } finally {
        // Hide loading overlay
        document.getElementById('loading-overlay').style.display = 'none';
    }
}

// Display results
function displayResults(userProfile, twins, insights) {
    const resultsSection = document.getElementById('results');
    resultsSection.style.display = 'block';
    
    // Display user profile
    displayUserProfile(userProfile);
    
    // Display twins
    displayTwins(twins);
    
    // Display insights
    displayInsights(insights);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Display user profile
function displayUserProfile(profile) {
    const container = document.getElementById('user-profile');
    container.innerHTML = `
        <h3 style="margin-bottom: 1rem; font-size: 1.5rem;">Your Home Profile</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div><strong>Location:</strong> ${profile.location}</div>
            <div><strong>Home Size:</strong> ${profile.home_size} sq ft</div>
            <div><strong>Bedrooms:</strong> ${profile.bedrooms}</div>
            <div><strong>Occupants:</strong> ${profile.occupants}</div>
            <div><strong>Home Type:</strong> ${capitalizeFirst(profile.home_type)}</div>
            <div><strong>Heating:</strong> ${capitalizeFirst(profile.heating_type.replace('_', ' '))}</div>
            <div><strong>Cooling:</strong> ${capitalizeFirst(profile.cooling_type.replace('_', ' '))}</div>
            <div><strong>Solar:</strong> ${profile.has_solar === 'yes' ? 'Yes' : 'No'}</div>
            ${profile.monthly_usage ? `<div><strong>Monthly Usage:</strong> ${profile.monthly_usage} kWh</div>` : ''}
        </div>
    `;
}

// Display twin cards
function displayTwins(twins) {
    const container = document.getElementById('twins-container');
    container.innerHTML = '';
    
    twins.forEach((twin, index) => {
        const card = document.createElement('div');
        card.className = 'twin-card';
        card.innerHTML = `
            <div class="similarity-badge">${Math.round(twin.similarity_score * 100)}% Match</div>
            <div class="twin-header">
                <div class="twin-icon">🏠</div>
                <div>
                    <div class="twin-title">Energy Twin #${index + 1}</div>
                    <div style="color: #666; font-size: 0.9rem;">${twin.location}</div>
                </div>
            </div>
            <div style="background: #f5f7fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <div style="font-size: 1.5rem; font-weight: 700; color: ${getEnergyColor(twin.monthly_usage)};">
                    ${twin.monthly_usage} kWh/month
                </div>
            </div>
            <div class="twin-details">
                <div class="detail-item"><strong>Size:</strong> ${twin.home_size} sq ft</div>
                <div class="detail-item"><strong>Type:</strong> ${capitalizeFirst(twin.home_type)}</div>
                <div class="detail-item"><strong>Bedrooms:</strong> ${twin.bedrooms}</div>
                <div class="detail-item"><strong>Occupants:</strong> ${twin.occupants}</div>
                <div class="detail-item"><strong>Heating:</strong> ${capitalizeFirst(twin.heating_type.replace('_', ' '))}</div>
                <div class="detail-item"><strong>Cooling:</strong> ${capitalizeFirst(twin.cooling_type.replace('_', ' '))}</div>
                <div class="detail-item"><strong>Solar:</strong> ${twin.has_solar ? 'Yes' : 'No'}</div>
                <div class="detail-item"><strong>Temperature:</strong> ${twin.temperature}°C</div>
            </div>
        `;
        container.appendChild(card);
    });
}

// Display insights
function displayInsights(insights) {
    const container = document.getElementById('insights');
    container.innerHTML = `
        <h3>📊 Energy Insights</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-top: 1.5rem;">
            <div>
                <h4 style="margin-bottom: 0.5rem;">Average Twin Usage</h4>
                <div style="font-size: 2rem; font-weight: 700;">${Math.round(insights.avg_twin_usage)} kWh</div>
            </div>
            <div>
                <h4 style="margin-bottom: 0.5rem;">Usage Range</h4>
                <div style="font-size: 1.2rem;">${Math.round(insights.min_usage)} - ${Math.round(insights.max_usage)} kWh</div>
            </div>
            <div>
                <h4 style="margin-bottom: 0.5rem;">Common Features</h4>
                <div style="font-size: 1rem;">${insights.common_heating} heating</div>
            </div>
        </div>
        <div style="margin-top: 2rem; padding: 1.5rem; background: rgba(255,255,255,0.1); border-radius: 8px;">
            <h4 style="margin-bottom: 0.5rem;">💡 Recommendation</h4>
            <p style="font-size: 1.1rem; line-height: 1.8;">${insights.recommendation}</p>
        </div>
    `;
}

// Utility functions
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function scrollToQuestionnaire() {
    document.getElementById('questionnaire').scrollIntoView({ behavior: 'smooth' });
}
