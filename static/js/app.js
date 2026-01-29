// Global variables
let map;
let markerCluster;  // For clustering large datasets
let homesData = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    loadGlobalData();
    setupFormSubmission();
});

// Initialize Leaflet map with marker clustering
function initMap() {
    // Center on the United States
    map = L.map('map-container').setView([37.8, -96], 4);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);
    
    // Initialize marker cluster group with custom options
    markerCluster = L.markerClusterGroup({
        chunkedLoading: true,
        chunkInterval: 200,
        chunkDelay: 50,
        maxClusterRadius: 80,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        iconCreateFunction: function(cluster) {
            const childCount = cluster.getChildCount();
            let size = 'small';
            let c = ' marker-cluster-';
            
            if (childCount < 100) {
                size = 'small';
            } else if (childCount < 1000) {
                size = 'medium';
            } else {
                size = 'large';
            }
            
            return new L.DivIcon({
                html: '<div><span>' + childCount.toLocaleString() + '</span></div>',
                className: 'marker-cluster' + c + size,
                iconSize: new L.Point(40, 40)
            });
        }
    });
    
    map.addLayer(markerCluster);
}

// Load global energy data and display on map
async function loadGlobalData() {
    console.log('🔄 Loading map data...');
    const startTime = performance.now();
    
    // Show loading indicator
    const loadingEl = document.getElementById('map-loading');
    if (loadingEl) loadingEl.style.display = 'block';
    
    try {
        const response = await fetch('/api/global-data');
        const data = await response.json();
        
        if (data.success) {
            const loadTime = Math.round(performance.now() - startTime);
            console.log(`✅ Loaded ${data.homes.length.toLocaleString()} homes in ${loadTime}ms`);
            
            if (data.sample_info) {
                console.log(`ℹ️  ${data.sample_info.note}`);
            }
            
            homesData = data.homes;
            
            // Stats are preloaded in HTML, but update if needed
            if (data.stats) {
                updateStats(data.stats);
            }
            
            displayHomesOnMap(data.homes);
        }
    } catch (error) {
        console.error('❌ Error loading global data:', error);
    } finally {
        // Hide loading indicator
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

// Update statistics in the stats bar
function updateStats(stats) {
    document.getElementById('total-homes').textContent = stats.total_homes.toLocaleString();
    document.getElementById('avg-energy').textContent = `${Math.round(stats.avg_energy)} kWh/month`;
    document.getElementById('cities').textContent = stats.cities.toLocaleString();
}

// Display homes on the map with clustering
function displayHomesOnMap(homes) {
    const startTime = performance.now();
    
    // Clear existing markers
    markerCluster.clearLayers();
    
    console.log(`🗺️  Adding ${homes.length.toLocaleString()} homes to map...`);
    
    // Batch add markers for better performance
    const markers = [];
    
    homes.forEach(home => {
        const color = getEnergyColor(home.usage);
        
        const marker = L.circleMarker([home.lat, home.lon], {
            radius: 6,
            fillColor: color,
            color: '#fff',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.7
        });
        
        // Create popup content with new field names
        const popupContent = `
            <div style="min-width: 200px;">
                <h3 style="margin: 0 0 10px 0; font-size: 1rem;">${home.location}</h3>
                <p style="margin: 5px 0;"><strong>Energy Usage:</strong> ${home.usage.toLocaleString()} kWh/month</p>
                <p style="margin: 5px 0;"><strong>Building Type:</strong> ${home.type}</p>
                <p style="margin: 5px 0;"><strong>Size:</strong> ${home.size.toLocaleString()} sq ft</p>
                <p style="margin: 5px 0;"><strong>Bedrooms:</strong> ${home.beds}</p>
                <p style="margin: 5px 0;"><strong>Occupants:</strong> ${home.occupants}</p>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        markers.push(marker);
    });
    
    // Add all markers at once (faster than individual adds)
    markerCluster.addLayers(markers);
    
    const renderTime = Math.round(performance.now() - startTime);
    console.log(`✅ Map clustering complete in ${renderTime}ms`);
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
    
    // Handle ResStock native format
    const location = profile.display_location || profile.location || 'Unknown';
    const homeSize = profile['in.sqft..ft2'] || profile.home_size || 0;
    const bedrooms = profile['in.bedrooms'] || profile.bedrooms || 0;
    const occupants = profile['in.occupants'] || profile.occupants || 0;
    const buildingType = profile['in.geometry_building_type_acs'] || profile.building_type || 'Unknown';
    const heatingFuel = profile['in.heating_fuel'] || profile.heating_fuel || 'Unknown';
    const coolingType = profile['in.hvac_cooling_type'] || profile.cooling_type || 'Unknown';
    const hasSolar = profile.has_solar_panel || profile.has_solar === 'yes' ? 'Yes' : 'No';
    const monthlyUsage = profile.monthly_kwh || profile.monthly_usage;
    const climateZone = profile['in.ashrae_iecc_climate_zone_2004'] || profile.climate_zone || 'Unknown';
    
    container.innerHTML = `
        <h3 style="margin-bottom: 1rem; font-size: 1.5rem;">Your Home Profile</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div><strong>Location:</strong> ${location}</div>
            <div><strong>Home Size:</strong> ${Math.round(homeSize)} sq ft</div>
            <div><strong>Bedrooms:</strong> ${bedrooms}</div>
            <div><strong>Occupants:</strong> ${occupants}</div>
            <div><strong>Building Type:</strong> ${buildingType}</div>
            <div><strong>Heating Fuel:</strong> ${heatingFuel}</div>
            <div><strong>Cooling:</strong> ${coolingType}</div>
            <div><strong>Climate Zone:</strong> ${climateZone}</div>
            <div><strong>Solar:</strong> ${hasSolar}</div>
            ${monthlyUsage ? `<div><strong>Monthly Usage:</strong> ${Math.round(monthlyUsage)} kWh</div>` : ''}
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
                    ${twin.monthly_usage.toLocaleString()} kWh/month
                </div>
            </div>
            <div class="twin-details">
                <div class="detail-item"><strong>Size:</strong> ${twin.home_size.toLocaleString()} sq ft</div>
                <div class="detail-item"><strong>Type:</strong> ${twin.building_type}</div>
                <div class="detail-item"><strong>Bedrooms:</strong> ${twin.bedrooms}</div>
                <div class="detail-item"><strong>Occupants:</strong> ${twin.occupants}</div>
                <div class="detail-item"><strong>Heating:</strong> ${twin.heating_fuel}</div>
                <div class="detail-item"><strong>Cooling:</strong> ${twin.cooling_type}</div>
                <div class="detail-item"><strong>Climate:</strong> ${twin.climate_zone}</div>
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
