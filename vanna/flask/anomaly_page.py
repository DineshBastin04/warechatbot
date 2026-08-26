anomaly_template = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Anomaly Detection Page</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- DataTables Core -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css" />
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>

    <!-- DataTables Buttons Extension -->
    <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.4.1/css/buttons.dataTables.min.css" />
    <script src="https://cdn.datatables.net/buttons/2.4.1/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.html5.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.print.min.js"></script>

    <!-- Required for HTML5 export -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>

    <!-- Chart.js for visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>

    

    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
        }
        .loading {
            color: #999;
        }
        .error {
            color: red;
        }
        #anomalyButton {
            margin: 10px;
            padding: 7px 15px;
            font-size: 15px;
            cursor: pointer;
            border-radius: 5px;
            font-weight: 500;
            color: #ffffff;
            background-color: #F9cd05;
            border: 1px solid #f9cd05;
        }
        #anomalyButton:hover {
            background-color: #ffd700;
        }
        .buttons-home, .buttons-home1 {
            text-align: center;
            border-top: 1px solid #fff;
            padding: 15px 0px;
            left: 0;
            width: 100%;
        }
        .main-layout {
            display: flex;
            flex-direction: row;
            gap: 20px;
        }
        .sidebar {
            width: 250px;
            height: 79vh;
            overflow-y: auto;
            padding: 15px;
            border: 1px solid #ddd;
            background-color: #f7f7f7;
            border-radius: 6px;
        }
        .sidebar::-webkit-scrollbar {
            width: 6px;
        }
        .sidebar::-webkit-scrollbar-thumb {
            background-color: #ccc;
            border-radius: 5px;
        }
        .sidebar::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        #anomalyButtons button {
            display: block;
            width: 100%;
            margin-bottom: 10px;
            padding: 10px;
            font-size: 14px;
            background: none;
            color: #7B83EB;
            border: 1px solid #7B83EB;
            border-radius: 4px;
            cursor: pointer;
            text-align: left;
            transition: background 0.3s;
        }
        #anomalyButtons button:hover {
            background-color: #7B83EB;
            color: #fff;
        }

        .anomaly-content {
            flex-grow: 1;
            overflow-x: auto;
        }
        #result table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        #result th, #result td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        #result th {
            background: #f2f2f2;
            color: #2c3e50;
            font-weight: bold;
        }
        #visualization {
            margin-top: 20px;
            max-width: 100%;
        }
        #anomalyChart {
            max-height: 400px;
        }
        @media (max-width: 600px) {
            .sidebar {
                width: 150px;
            }
            .anomaly-content {
                padding: 15px;
            }
        }


.copyright {
    text-align: center;
    border-top: 1px solid #cbcbcb;
    margin-top: 25px;
}

.warehouse-logo {
  width: 200px;
}
     

    </style>
</head>
<body>
 <div class="logo"><img class="warehouse-logo" alt="wi Logo" src="http://tychons.com/wp-content/uploads/2025/09/warehouse_logo-2.png"></div>

    <h1>Anomaly Detection</h1>
     
</button>


    <div class="main-layout">
        <div id="anomalyButtons" class="sidebar"></div>
        <div id="result" class="anomaly-content">
            <div id="tableContainer"></div>
            <div id="visualization">
                <canvas id="anomalyChart"></canvas>
            </div>
        </div>
    </div>

     <footer>
    <div class="copyright">
    <p>© 2025 Tychons USA LLC. All Rights Reserved</p>
    </div>
    </footer>

    <script>

   
    
        let anomalyChart = null; // Store Chart.js instance

        function getWorkspaceIdFromUrl() {
            const params = new URLSearchParams(window.location.search);
            return params.get("workspace_id") || "unknown";
        }

        function formatAnomalyType(type) {
            return type
                .split("_")
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(" ");
        }

        async function loadAnomalies() {
            const workspace_id = getWorkspaceIdFromUrl();
            const anomalyButtons = document.getElementById("anomalyButtons");
            anomalyButtons.innerHTML = '<p class="loading">Loading anomalies...</p>';

            try {
                const response = await fetch(`/api/v0/get_anomaly_configs?workspace_id=${encodeURIComponent(workspace_id)}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const data = await response.json();

                if (data.type === "error") {
                    anomalyButtons.innerHTML = `<p class="error">Error: ${data.error}</p>`;
                    return;
                }

                const anomalies = data.anomalies || [];
                anomalyButtons.innerHTML = "";

                if (anomalies.length === 0) {
                    anomalyButtons.innerHTML = "<p>No anomalies available.</p>";
                } else {
                    anomalies.forEach(anomaly => {
                        if (anomaly.enabled) {
                            const button = document.createElement("button");
                            button.textContent = formatAnomalyType(anomaly.type);
                            button.onclick = () => fetchAnomaly(anomaly.type);
                            anomalyButtons.appendChild(button);
                        }
                    });
                }
            } catch (error) {
                anomalyButtons.innerHTML = `<p class="error">Failed to load anomalies: ${error.message}</p>`;
            }
        }

        async function fetchAnomaly(anomaly_type) {
            const workspace_id = getWorkspaceIdFromUrl();
            const tableContainer = document.getElementById("tableContainer");
            const visualization = document.getElementById("visualization");
            tableContainer.innerHTML = '<p class="loading">Loading...</p>';
            visualization.style.display = 'none'; // Hide visualization until data is loaded

            try {
                const response = await fetch(`/api/v0/run_anomaly?workspace_id=${encodeURIComponent(workspace_id)}&anomaly_type=${encodeURIComponent(anomaly_type)}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const data = await response.json();

                if (data.type === "error" || data.type === "sql_error") {
                    tableContainer.innerHTML = `<p class="error">Error: ${data.error}</p>`;
                    visualization.style.display = 'none';
                    return;
                }

                if (data.results && data.results.length > 0) {
                    // Build HTML table
                    let html = '<table id="anomalyTable" class="display"><thead><tr>';
                    const headers = Object.keys(data.results[0]);
                    headers.forEach(header => {
                        html += `<th>${header.replace("_", " ").toUpperCase()}</th>`;
                    });
                    html += '</tr></thead><tbody>';

                    // Table rows
                    data.results.forEach(row => {
                        html += '<tr>';
                        headers.forEach(header => {
                            html += `<td>${row[header] ?? "NULL"}</td>`;
                        });
                        html += '</tr>';
                    });

                    html += '</tbody></table>';
                    tableContainer.innerHTML = html;

                    // Initialize DataTable with CSV export
                    setTimeout(() => {
                        $('#anomalyTable').DataTable({
                            dom: 'Bfrtip',
                            buttons: [
                                {
                                    extend: 'csvHtml5',
                                    text: '⬇️ Export CSV',
                                    title: `Anomaly_${anomaly_type}_${workspace_id}`
                                }
                            ]
                        });
                    }, 0);

                    // Render visualization
                    renderAnomalyVisualization(data.results, anomaly_type);
                    visualization.style.display = 'block';
                } else {
                    tableContainer.innerHTML = "<p>No anomalies detected.</p>";
                    visualization.style.display = 'none';
                }
            } catch (error) {
                tableContainer.innerHTML = `<p class="error">Failed to fetch anomaly: ${error.message}</p>`;
                visualization.style.display = 'none';
            }
        }

        function renderAnomalyVisualization(data, anomaly_type) {
            const ctx = document.getElementById('anomalyChart').getContext('2d');
            
            // Destroy previous chart if it exists
            if (anomalyChart) {
                anomalyChart.destroy();
            }

            // Determine visualization type based on data
            const headers = Object.keys(data[0]);
            let xAxis = headers[0]; // First column as X-axis (e.g., wh_id, timestamp)
            let yAxis = headers.find(h => h.includes('count') || h.includes('value') || h.includes('len') || h === 'cnt' || h.includes('missing')) || headers[1]; // Numerical column for Y-axis
            let isAnomaly = headers.find(h => h.includes('anomaly') || h.includes('outlier')); // Anomaly indicator column

            // Prepare data for scatter plot
            const normalPoints = [];
            const anomalyPoints = [];
            data.forEach(row => {
                const point = {
                    x: row[xAxis],
                    y: parseFloat(row[yAxis]) || 0
                };
                if (isAnomaly && row[isAnomaly]) {
                    anomalyPoints.push(point);
                } else {
                    normalPoints.push(point);
                }
            });

            // Create scatter plot
            anomalyChart = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [
                        {
                            label: 'Normal Data',
                            data: normalPoints,
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            pointRadius: 5
                        },
                        {
                            label: 'Anomalies',
                            data: anomalyPoints,
                            backgroundColor: 'rgba(231, 76, 60, 0.8)',
                            pointRadius: 7,
                            pointHoverRadius: 10
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: xAxis.replace("_", " ").toUpperCase()
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: yAxis.replace("_", " ").toUpperCase()
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: `Anomaly Detection: ${formatAnomalyType(anomaly_type)}`
                        },
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });
        }

        window.onload = loadAnomalies;
    </script>
</body>
</html>
"""
