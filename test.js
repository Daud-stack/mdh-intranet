
    document.addEventListener("DOMContentLoaded", function () {
        Chart.defaults.font.family = "'Inter', 'Segoe UI', Roboto, sans-serif";
        Chart.defaults.color = '#64748b';

        // Retrieve json datasets
        const chartIncCatLabels = JSON.parse('[]');
        const chartIncCatData = JSON.parse('[]');
        const chartCapaLabels = JSON.parse('[]');
        const chartCapaData = JSON.parse('[]');
        const chartIncSevLabels = JSON.parse('[]');
        const chartIncSevData = JSON.parse('[]');
        const chartSopLabels = JSON.parse('[]');
        const chartSopData = JSON.parse('[]');

        const chartTrendLabels = JSON.parse('[]');
        const dailyIncidents = JSON.parse('[]');
        const dailyTickets = JSON.parse('[]');
        const dailyAudits = JSON.parse('[]');

        const chartTopUsersLabels = JSON.parse('[]');
        const chartTopUsersData = JSON.parse('[]');
        const chartPaLabels = JSON.parse('[]');
        const chartPaData = JSON.parse('[]');
        const chartWoLabels = JSON.parse('[]');
        const chartWoData = JSON.parse('[]');

        // 7-Day Trend
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: chartTrendLabels,
                datasets: [
                    {
                        label: 'Incidents',
                        data: dailyIncidents,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                    },
                    {
                        label: 'Tickets',
                        data: dailyTickets,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                    },
                    {
                        label: 'Audit Events',
                        data: dailyAudits,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.03)' } },
                    x: { grid: { display: false } },
                },
            },
        });

        const sevColors = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6'];
        const incSevCtx = document.getElementById('incSeverityChart').getContext('2d');
        new Chart(incSevCtx, {
            type: 'doughnut',
            data: {
                labels: chartIncSevLabels,
                datasets: [{
                    data: chartIncSevData,
                    backgroundColor: sevColors,
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, usePointStyle: true, font: { size: 11 } }
                    }
                },
                cutout: '60%'
            }
        });

        // Incidents by Category Chart
        const incCatCtx = document.getElementById('incCategoryChart').getContext('2d');
        new Chart(incCatCtx, {
            type: 'doughnut',
            data: {
                labels: chartIncCatLabels,
                datasets: [{
                    data: chartIncCatData,
                    backgroundColor: [
                        '#3b82f6', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6', '#64748b', '#0ea5e9', '#ec4899'
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { boxWidth: 12, usePointStyle: true, font: { size: 11 } }
                    }
                },
                cutout: '70%'
            }
        });

        // CAPA Status Chart
        const capaStatusCtx = document.getElementById('capaStatusChart').getContext('2d');
        new Chart(capaStatusCtx, {
            type: 'bar',
            data: {
                labels: chartCapaLabels,
                datasets: [{
                    label: 'CAPAs',
                    data: chartCapaData,
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderRadius: 4,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0, font: { size: 11 } },
                        grid: { borderDash: [2, 4], color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        ticks: { font: { size: 10 } },
                        grid: { display: false }
                    }
                }
            }
        });

        // Users Chart
        const usersCtx = document.getElementById('usersChart').getContext('2d');
        new Chart(usersCtx, {
            type: 'bar',
            data: {
                labels: chartTopUsersLabels,
                datasets: [{
                    label: 'Actions',
                    data: chartTopUsersData,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderRadius: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.03)' } },
                    y: { grid: { display: false } },
                },
            },
        });

        // SOP Categories Chart
        const sopColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b'];
        const sopCtx = document.getElementById('sopCategoriesChart').getContext('2d');
        new Chart(sopCtx, {
            type: 'polarArea',
            data: {
                labels: chartSopLabels,
                datasets: [{
                    data: chartSopData,
                    backgroundColor: sopColors.map(c => c + 'AA'),
                    borderColor: '#ffffff',
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'right', labels: { boxWidth: 12, usePointStyle: true, font: { size: 10 } } } },
            },
        });

        // Facilities Work Orders Chart
        const woStatusCtx = document.getElementById('woStatusChart').getContext('2d');
        new Chart(woStatusCtx, {
            type: 'doughnut',
            data: {
                labels: chartWoLabels,
                datasets: [{
                    data: chartWoData,
                    backgroundColor: ['#64748b', '#3b82f6', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { boxWidth: 12, usePointStyle: true, font: { size: 10 } }
                    }
                },
                cutout: '70%'
            }
        });

        // Medical Aid
        const paStatusCtx = document.getElementById('paStatusChart').getContext('2d');
        new Chart(paStatusCtx, {
            type: 'bar',
            data: {
                labels: chartPaLabels,
                datasets: [{
                    label: 'Pre-Auth Requests',
                    data: chartPaData,
                    backgroundColor: ['#f59e0b', '#10b981', '#ef4444', '#94a3b8'],
                    borderRadius: 4,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0, font: { size: 11 } },
                        grid: { borderDash: [2, 4], color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        ticks: { font: { size: 10 } },
                        grid: { display: false }
                    }
                }
            }
        });
    });
