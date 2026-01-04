// Global Variables
let systemOverviewChart;
let currentTheme = localStorage.getItem('theme') || 'light';

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Set initial theme
    setTheme(currentTheme);
    
    // Initialize chart
    initializeSystemOverviewChart();
    
    // Setup event listeners
    setupEventListeners();
    
    // Setup theme toggles
    setupThemeToggles();
    
    // Setup mobile sidebar
    setupMobileSidebar();
    
    // Update stats periodically
    setInterval(updateStats, 30000); // Update every 30 seconds
    
    // Show welcome toast
    setTimeout(() => {
        showToast('Welcome to Admin Dashboard!', 'success');
    }, 1000);
});

// Set theme function
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update theme toggle checkboxes
    document.querySelectorAll('.theme-toggle-checkbox').forEach(checkbox => {
        checkbox.checked = theme === 'dark';
    });
    
    // Update quick toggle buttons
    document.querySelectorAll('.theme-btn-light, .theme-btn-dark').forEach(btn => {
        if (btn.dataset.theme === theme) {
            btn.classList.remove('btn-outline-light');
            btn.classList.add('btn-light');
        } else {
            btn.classList.remove('btn-light');
            btn.classList.add('btn-outline-light');
        }
    });
    
    // Update chart theme if chart exists
    if (systemOverviewChart) {
        updateChartTheme();
    }
}

// Setup theme toggle functionality
function setupThemeToggles() {
    // Theme toggle checkboxes
    document.querySelectorAll('.theme-toggle-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            setTheme(newTheme);
            showToast(`Theme changed to ${newTheme} mode`, 'info');
        });
    });
    
    // Quick theme buttons
    document.querySelectorAll('.theme-btn-light, .theme-btn-dark').forEach(btn => {
        btn.addEventListener('click', function() {
            const newTheme = this.dataset.theme;
            setTheme(newTheme);
            showToast(`Theme changed to ${newTheme} mode`, 'info');
        });
    });
}

// Initialize system overview chart
function initializeSystemOverviewChart() {
    const ctx = document.getElementById('systemOverviewChart').getContext('2d');
    const isDarkMode = currentTheme === 'dark';
    
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDarkMode ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.8)';
    
    systemOverviewChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'New Students',
                data: [5, 8, 3, 10, 7, 2, 4],
                borderColor: '#e74a3b',
                backgroundColor: isDarkMode ? 'rgba(231, 74, 59, 0.2)' : 'rgba(231, 74, 59, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 2
            }, {
                label: 'Results Uploaded',
                data: [12, 15, 10, 18, 14, 8, 11],
                borderColor: '#1cc88a',
                backgroundColor: isDarkMode ? 'rgba(28, 200, 138, 0.2)' : 'rgba(28, 200, 138, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: textColor,
                        font: {
                            family: 'Poppins',
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
                    titleColor: textColor,
                    bodyColor: textColor,
                    borderColor: isDarkMode ? '#444' : '#ddd',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: gridColor,
                        drawBorder: false
                    },
                    ticks: {
                        color: textColor
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: gridColor,
                        drawBorder: false
                    },
                    ticks: {
                        color: textColor,
                        callback: function(value) {
                            return value + ' records';
                        }
                    }
                }
            }
        }
    });
}

// Update chart theme
function updateChartTheme() {
    const isDarkMode = currentTheme === 'dark';
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDarkMode ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.8)';
    
    if (systemOverviewChart) {
        // Update chart colors
        systemOverviewChart.data.datasets[0].backgroundColor = isDarkMode 
            ? 'rgba(231, 74, 59, 0.2)' 
            : 'rgba(231, 74, 59, 0.1)';
        systemOverviewChart.data.datasets[1].backgroundColor = isDarkMode 
            ? 'rgba(28, 200, 138, 0.2)' 
            : 'rgba(28, 200, 138, 0.1)';
        
        // Update axis colors
        systemOverviewChart.options.scales.x.grid.color = gridColor;
        systemOverviewChart.options.scales.x.ticks.color = textColor;
        systemOverviewChart.options.scales.y.grid.color = gridColor;
        systemOverviewChart.options.scales.y.ticks.color = textColor;
        
        // Update legend colors
        systemOverviewChart.options.plugins.legend.labels.color = textColor;
        
        // Update tooltip colors
        systemOverviewChart.options.plugins.tooltip.backgroundColor = isDarkMode ? '#2d2d2d' : '#ffffff';
        systemOverviewChart.options.plugins.tooltip.titleColor = textColor;
        systemOverviewChart.options.plugins.tooltip.bodyColor = textColor;
        systemOverviewChart.options.plugins.tooltip.borderColor = isDarkMode ? '#444' : '#ddd';
        
        systemOverviewChart.update();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Chart period selector
    document.getElementById('chartPeriod')?.addEventListener('change', function() {
        updateChartData(this.value);
    });
    
    // Chart theme toggle
    document.getElementById('toggleChartTheme')?.addEventListener('click', function() {
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });
    
    // Window resize handler
    window.addEventListener('resize', function() {
        if (systemOverviewChart) {
            systemOverviewChart.resize();
        }
    });
}

// Update chart data based on selected period
function updateChartData(period) {
    let labels, studentData, resultsData;
    
    switch(period) {
        case 'Last 30 Days':
            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
            studentData = [25, 32, 28, 35];
            resultsData = [45, 52, 48, 55];
            break;
            
        case 'Last 3 Months':
            labels = ['Month 1', 'Month 2', 'Month 3'];
            studentData = [95, 112, 108];
            resultsData = [185, 202, 198];
            break;
            
        default: // Last 7 Days
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            studentData = [5, 8, 3, 10, 7, 2, 4];
            resultsData = [12, 15, 10, 18, 14, 8, 11];
    }
    
    if (systemOverviewChart) {
        systemOverviewChart.data.labels = labels;
        systemOverviewChart.data.datasets[0].data = studentData;
        systemOverviewChart.data.datasets[1].data = resultsData;
        systemOverviewChart.update();
        
        showToast(`Updated chart data for ${period}`, 'info');
    }
}

// Setup mobile sidebar functionality
function setupMobileSidebar() {
    const mobileSidebar = document.getElementById('mobileSidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');
    
    if (mobileSidebar) {
        mobileSidebar.addEventListener('show.bs.collapse', function () {
            sidebarBackdrop.classList.add('show');
            document.body.style.overflow = 'hidden';
        });
        
        mobileSidebar.addEventListener('hide.bs.collapse', function () {
            sidebarBackdrop.classList.remove('show');
            document.body.style.overflow = '';
        });
        
        sidebarBackdrop.addEventListener('click', function () {
            const collapse = new bootstrap.Collapse(mobileSidebar);
            collapse.hide();
        });
    }

    // Close mobile sidebar when clicking outside
    document.addEventListener('click', function(event) {
        const isClickInside = mobileSidebar?.contains(event.target) || 
                            event.target.closest('.sidebar-toggle') ||
                            event.target.closest('.mobile-menu-btn');
        
        if (!isClickInside && mobileSidebar?.classList.contains('show')) {
            const collapse = new bootstrap.Collapse(mobileSidebar);
            collapse.hide();
        }
    });

    // Handle touch gestures for mobile sidebar
    let touchStartX = 0;
    let touchEndX = 0;

    document.addEventListener('touchstart', function(event) {
        touchStartX = event.changedTouches[0].screenX;
    }, false);

    document.addEventListener('touchend', function(event) {
        touchEndX = event.changedTouches[0].screenX;
        handleSwipe();
    }, false);

    function handleSwipe() {
        const swipeThreshold = 50;
        const swipeDistance = touchEndX - touchStartX;

        if (Math.abs(swipeDistance) > swipeThreshold) {
            if (swipeDistance > 0 && window.innerWidth < 992) {
                // Swipe right - show sidebar
                if (!mobileSidebar.classList.contains('show')) {
                    const collapse = new bootstrap.Collapse(mobileSidebar);
                    collapse.show();
                }
            } else if (swipeDistance < 0 && window.innerWidth < 992) {
                // Swipe left - hide sidebar
                if (mobileSidebar.classList.contains('show')) {
                    const collapse = new bootstrap.Collapse(mobileSidebar);
                    collapse.hide();
                }
            }
        }
    }
}

// Update stats periodically
function updateStats() {
    // Simulate real-time updates
    const studentCount = Math.floor(1245 + Math.random() * 10);
    const teacherCount = Math.floor(58 + Math.random() * 2);
    
    // Update UI
    document.querySelector('.stats-card:first-child .h5').textContent = studentCount;
    document.querySelector('.stats-card:nth-child(2) .h5').textContent = teacherCount;
    
    // Update badges
    document.querySelector('.nav-item:nth-child(2) .badge').textContent = studentCount;
    document.querySelector('.nav-item:nth-child(3) .badge').textContent = teacherCount;
}

// Quick action functions
function addStudent() {
    showToast('Opening Add Student form...', 'info');
    // In a real app, this would open a modal or redirect
    setTimeout(() => {
        showToast('Add Student functionality would open here', 'success');
    }, 500);
}

function addTeacher() {
    showToast('Opening Add Teacher form...', 'info');
    // In a real app, this would open a modal or redirect
    setTimeout(() => {
        showToast('Add Teacher functionality would open here', 'success');
    }, 500);
}

function createClass() {
    showToast('Opening Create Class form...', 'info');
    // In a real app, this would open a modal or redirect
    setTimeout(() => {
        showToast('Create Class functionality would open here', 'success');
    }, 500);
}

function generateReport() {
    showToast('Generating system report...', 'info');
    
    // Simulate report generation
    setTimeout(() => {
        showToast('System report generated successfully! <a href="#" class="text-white">Download</a>', 'success');
    }, 2000);
}

// Show toast notification
function showToast(message, type = 'info') {
    // Remove existing alerts
    const existingToasts = document.querySelectorAll('.custom-toast');
    existingToasts.forEach(toast => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    });
    
    // Create new toast
    const toast = document.createElement('div');
    toast.className = `custom-toast alert alert-${type} alert-dismissible fade show`;
    toast.innerHTML = `
        <i class="fas fa-${getToastIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    toast.style.display = 'block';
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

function getToastIcon(type) {
    switch(type) {
        case 'success': return 'check-circle';
        case 'danger': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl + T to toggle theme
    if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        showToast(`Theme toggled to ${newTheme} mode`, 'info');
    }
    
    // Ctrl + D for dashboard refresh
    if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        updateStats();
        showToast('Dashboard data refreshed', 'success');
    }
    
    // Ctrl + M to toggle mobile menu (on mobile)
    if (e.ctrlKey && e.key === 'm' && window.innerWidth < 992) {
        e.preventDefault();
        const mobileSidebar = document.getElementById('mobileSidebar');
        if (mobileSidebar) {
            const collapse = new bootstrap.Collapse(mobileSidebar);
            if (mobileSidebar.classList.contains('show')) {
                collapse.hide();
            } else {
                collapse.show();
            }
        }
    }
});
