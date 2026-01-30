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
        card.dataset.twinId = twin.id;
        card.dataset.twinIndex = index;
        
        card.innerHTML = `
            <span class="close-expanded" onclick="event.stopPropagation(); closeExpandedCard();">&times;</span>
            <div class="card-content-wrapper">
                <div class="card-left">
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
                </div>
                <div class="card-right">
                    <div class="chart-loading">Loading energy profile...</div>
                </div>
            </div>
        `;
        
        // Make card clickable if timeseries available
        if (twin.timeseries_available) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                if (!card.classList.contains('expanded')) {
                    expandCard(card, twin);
                }
            });
        } else {
            card.style.cursor = 'default';
        }
        
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

// Expanding card system
let currentCharts = {};
let expandedCard = null;
let timeseriesCache = {}; // Cache for timeseries data

function expandCard(card, twin) {
    // If another card is already expanded, close it simultaneously while expanding new one
    if (expandedCard && expandedCard !== card) {
        const oldCard = expandedCard;
        expandedCard = null;
        
        // Start closing animation for old card (without callback)
        closeOldCardSilently(oldCard);
        
        // Continue with expanding new card (will happen simultaneously)
    }
    
    if (expandedCard === card) return;
    
    expandedCard = card;
    
    // Move card to top instantly (no animation)
    card.classList.add('moving-to-top');
    
    // Small delay to let DOM update, then expand
    setTimeout(() => {
        card.classList.remove('moving-to-top');
        card.classList.add('expanded');
        
        // Scroll to show the expanded card
        setTimeout(() => {
            const twinsContainer = document.getElementById('twins-container');
            const cardTop = card.getBoundingClientRect().top;
            
            // Scroll so card is near top of viewport
            window.scrollTo({
                top: window.scrollY + cardTop - 100,
                behavior: 'smooth'
            });
        }, 100);
        
        // Load data
        loadTimeseriesData(card, twin.id, twin.location);
    }, 50);
}

function closeExpandedCard(callback) {
    if (!expandedCard) {
        if (callback) callback();
        return;
    }
    
    const card = expandedCard;
    expandedCard = null;
    
    // Collapse and return to original position simultaneously
    card.classList.remove('expanded');
    card.classList.remove('moving-to-top');
    
    // Clear the card content immediately to prevent canvas ID conflicts
    const cardRight = card.querySelector('.card-right');
    if (cardRight) {
        cardRight.innerHTML = '<div class="chart-loading">Loading energy profile...</div>';
    }
    
    // Clean up after collapse animation completes
    setTimeout(() => {
        card.style.transform = '';
        card.style.transition = '';
        
        // Destroy charts
        Object.values(currentCharts).forEach(chart => chart && chart.destroy());
        currentCharts = {};
        
        // Clear content
        const cardRight = card.querySelector('.card-right');
        if (cardRight) {
            cardRight.innerHTML = '<div class="chart-loading">Loading energy profile...</div>';
        }
        
        if (callback) callback();
    }, 650);
}

// Close old card without callback for simultaneous animation
function closeOldCardSilently(card) {
    const cardId = card.dataset.twinId;
    
    // Collapse and return to original position simultaneously
    card.classList.remove('expanded');
    card.classList.remove('moving-to-top');
    
    // Clear the old card's content to prevent canvas ID conflicts
    const cardRight = card.querySelector('.card-right');
    if (cardRight) {
        cardRight.innerHTML = '<div class="chart-loading">Loading energy profile...</div>';
    }
}

async function loadTimeseriesData(card, buildingId, location) {
    const cardRight = card.querySelector('.card-right');
    const cardId = card.dataset.twinId;
    
    // Destroy any existing charts first before creating new ones
    Object.values(currentCharts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    currentCharts = {};
    
    // Check cache first
    if (timeseriesCache[buildingId]) {
        // Always re-render from cache to ensure fresh canvas elements
        const result = timeseriesCache[buildingId];
        renderTimeseriesUI(cardRight, result);
        return;
    }
    
    cardRight.innerHTML = '<div class="chart-loading">📊 Loading energy profile...</div>';
    
    try {
        const response = await fetch(`/api/timeseries/${buildingId}`);
        const result = await response.json();
        
        if (!result.success) {
            cardRight.innerHTML = `<div class="chart-loading" style="color: #e74c3c;">❌ ${result.message}</div>`;
            return;
        }
        
        // Store in cache
        timeseriesCache[buildingId] = result;
        
        renderTimeseriesUI(cardRight, result);
        
    } catch (error) {
        console.error('Error loading timeseries:', error);
        cardRight.innerHTML = '<div class="chart-loading" style="color: #e74c3c;">❌ Failed to load data</div>';
    }
}

function renderTimeseriesUI(cardRight, result) {
    // Render timeseries UI
    cardRight.innerHTML = `
        <h3 style="margin-bottom: 1.5rem; color: var(--primary-color);">📊 Energy Profile Analysis</h3>
        <div class="tabs">
            <button class="tab-button active" onclick="switchTab('monthly')">Monthly Usage</button>
            <button class="tab-button" onclick="switchTab('daily')">Daily Pattern</button>
            <button class="tab-button" onclick="switchTab('hourly')">Hourly Pattern</button>
            <button class="tab-button" onclick="switchTab('breakdown')">End Use</button>
        </div>
        <div class="tab-content">
            <div id="tab-monthly" class="tab-pane" style="display: block;">
                <canvas id="chart-monthly"></canvas>
            </div>
            <div id="tab-daily" class="tab-pane" style="display: none;">
                <canvas id="chart-daily"></canvas>
            </div>
            <div id="tab-hourly" class="tab-pane" style="display: none;">
                <canvas id="chart-hourly"></canvas>
            </div>
            <div id="tab-breakdown" class="tab-pane" style="display: none;">
                <canvas id="chart-breakdown"></canvas>
            </div>
        </div>
        <div class="timeseries-stats-grid" id="timeseries-stats"></div>
    `;
    
    // Render charts
    setTimeout(() => {
        renderMonthlyChart(result.data.monthly);
        renderDailyChart(result.data.daily);
        renderHourlyChart(result.data.hourly_pattern);
        renderBreakdownChart(result.data.end_use_breakdown);
        displayTimeseriesStats(result.stats);
        
        // Re-center the card after charts are loaded and height has changed
        setTimeout(() => {
            if (expandedCard) {
                expandedCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 300);
    }, 100);
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update panes
    document.querySelectorAll('.tab-pane').forEach(pane => pane.style.display = 'none');
    document.getElementById(`tab-${tabName}`).style.display = 'block';
}

function renderMonthlyChart(data) {
    const canvas = document.getElementById('chart-monthly');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (currentCharts.monthly) {
        currentCharts.monthly.destroy();
    }
    
    currentCharts.monthly = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.month),
            datasets: [{
                label: 'Monthly Electricity Usage (kWh)',
                data: data.map(d => d.total_electricity_kwh),
                backgroundColor: 'rgba(52, 152, 219, 0.6)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Monthly Electricity Usage (2018)',
                    font: { size: 16, weight: 'bold' }
                },
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'kWh' }
                }
            }
        }
    });
}

function renderDailyChart(data) {
    const canvas = document.getElementById('chart-daily');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (currentCharts.daily) {
        currentCharts.daily.destroy();
    }
    
    // Sample every 7th day for readability
    const sampledData = data.filter((_, i) => i % 7 === 0);
    
    currentCharts.daily = new Chart(ctx, {
        type: 'line',
        data: {
            labels: sampledData.map(d => d.date),
            datasets: [{
                label: 'Daily Electricity Usage (kWh)',
                data: sampledData.map(d => d.total_electricity_kwh),
                borderColor: 'rgba(46, 204, 113, 1)',
                backgroundColor: 'rgba(46, 204, 113, 0.1)',
                borderWidth: 2,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Daily Usage Pattern (Weekly Samples)',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'kWh' }
                }
            }
        }
    });
}

function renderHourlyChart(data) {
    const canvas = document.getElementById('chart-hourly');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (currentCharts.hourly) {
        currentCharts.hourly.destroy();
    }
    
    currentCharts.hourly = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => `${d.hour}:00`),
            datasets: [{
                label: 'Average Hourly Usage (kWh)',
                data: data.map(d => d.total_electricity_kwh),
                borderColor: 'rgba(155, 89, 182, 1)',
                backgroundColor: 'rgba(155, 89, 182, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Typical Day: Average Usage by Hour',
                    font: { size: 16, weight: 'bold' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'kWh' }
                },
                x: {
                    title: { display: true, text: 'Hour of Day' }
                }
            }
        }
    });
}

function renderBreakdownChart(data) {
    const canvas = document.getElementById('chart-breakdown');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (currentCharts.breakdown) {
        currentCharts.breakdown.destroy();
    }
    
    const sortedData = Object.entries(data).sort((a, b) => b[1] - a[1]);
    
    currentCharts.breakdown = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sortedData.map(([name, _]) => name),
            datasets: [{
                data: sortedData.map(([_, value]) => value),
                backgroundColor: [
                    'rgba(52, 152, 219, 0.8)',
                    'rgba(46, 204, 113, 0.8)',
                    'rgba(231, 76, 60, 0.8)',
                    'rgba(241, 196, 15, 0.8)',
                    'rgba(155, 89, 182, 0.8)',
                    'rgba(52, 73, 94, 0.8)',
                    'rgba(26, 188, 156, 0.8)',
                    'rgba(230, 126, 34, 0.8)',
                    'rgba(149, 165, 166, 0.8)',
                    'rgba(127, 140, 141, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Energy Use Breakdown (Average Monthly kWh)',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

function displayTimeseriesStats(stats) {
    const container = document.getElementById('timeseries-stats');
    container.innerHTML = `
        <div class="stat-card">
            <h4>Annual Total</h4>
            <div class="value">${stats.total_annual_kwh.toLocaleString()} kWh</div>
        </div>
        <div class="stat-card">
            <h4>Average Daily</h4>
            <div class="value">${stats.avg_daily_kwh.toFixed(1)} kWh</div>
        </div>
        <div class="stat-card">
            <h4>Peak Daily</h4>
            <div class="value" style="color: #e74c3c;">${stats.peak_daily_kwh.toFixed(1)} kWh</div>
        </div>
        <div class="stat-card">
            <h4>Minimum Daily</h4>
            <div class="value" style="color: #27ae60;">${stats.min_daily_kwh.toFixed(1)} kWh</div>
        </div>
    `;
}

// Close expanded card when pressing Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && expandedCard) {
        closeExpandedCard();
    }
});


function scrollToQuestionnaire() {
    document.getElementById('questionnaire').scrollIntoView({ behavior: 'smooth' });
}
