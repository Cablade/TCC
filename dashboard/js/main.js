document.addEventListener('DOMContentLoaded', () => {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Outfit';

    // 1. Injetar valores dinâmicos no HTML
    const dataA = DASHBOARD_DATA["A"];
    const dataB = DASHBOARD_DATA["B"];

    document.getElementById('val-a-tp').textContent = dataA.tp;
    document.getElementById('val-a-fn').textContent = dataA.fn;
    document.getElementById('val-a-f1').textContent = dataA.f1.toFixed(2);
    document.getElementById('val-a-time').textContent = dataA.time_seconds < 60 ? 
        `~${dataA.time_seconds} seg` : `~${Math.round(dataA.time_seconds / 60)} min`;

    document.getElementById('val-b-tp').textContent = dataB.tp;
    document.getElementById('val-b-fn').textContent = dataB.fn;
    document.getElementById('val-b-f1').textContent = dataB.f1.toFixed(2);
    document.getElementById('val-b-time').textContent = dataB.time_seconds < 60 ? 
        `~${dataB.time_seconds} seg` : `~${Math.round(dataB.time_seconds / 60)} min`;


    // 2. Accuracy Chart (TP vs FN)
    const ctxAcc = document.getElementById('accuracyChart').getContext('2d');
    new Chart(ctxAcc, {
        type: 'bar',
        data: {
            labels: ['Corretos (TP)', 'Falsos Negativos (FN)'],
            datasets: [
                {
                    label: 'Modelo A (Baseline)',
                    data: [dataA.tp, dataA.fn],
                    backgroundColor: 'rgba(244, 63, 94, 0.8)',
                    borderColor: 'rgba(244, 63, 94, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                },
                {
                    label: 'Modelo B (Proposto)',
                    data: [dataB.tp, dataB.fn],
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', padding: 12 }
            }
        }
    });

    // 3. Time Chart (Processing Seconds)
    const ctxTime = document.getElementById('timeChart').getContext('2d');
    new Chart(ctxTime, {
        type: 'bar',
        data: {
            labels: ['Tempo Total (Segundos)'],
            datasets: [
                {
                    label: 'Modelo A (Baseline)',
                    data: [dataA.time_seconds],
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                },
                {
                    label: 'Modelo B (Proposto)',
                    data: [dataB.time_seconds],
                    backgroundColor: 'rgba(139, 92, 246, 0.8)',
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', padding: 12 }
            },
            scales: {
                y: {
                    type: 'logarithmic',
                    title: { display: true, text: 'Segundos (Escala Logarítmica)', color: '#94a3b8' }
                }
            }
        }
    });
});
