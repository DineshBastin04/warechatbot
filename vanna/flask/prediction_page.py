prediction_template = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Prediction Page</title>
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



          #predictionButton {
      margin: 10px;
      padding: 7px 50px;
      font-size: 15px;
      cursor: pointer;
      border-radius: 5px;
      font-weight: 500;
      color: #ffffff;
      background-color: #28A745;
      border: 1px solid #28A745;
      }
      #predictionButton:hover{
      background-color: #5fe47e;
      }
      #anomalyButton{
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
        .buttons-home, .buttons-home1{
        text-align: center;
        border-top: 1px solid #fff;
        padding: 15px 0px;
        left: 0;
        width: 100%;
        }
    /* Modal backdrop */
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    /* Modal content */
    .modal-content {
        background: #ffffff;
        width: 90%;
        max-width: 800px;
        max-height: 80vh;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
    }

    /* Container for sidebar and content */
    .container {
        display: flex;
        height: 100%;
    }

    /* Sidebar */
    .sidebar {
        width: 220px;
        padding: 20px;
        overflow-y: auto;
        height: auto;
    }

    .sidebar h3 {
        margin: 0 0 20px;
        font-size: 1.2em;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .prediction-btn {
        display: block;
        width: 100%;
        padding: 10px;
        margin-bottom: 10px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 1em;
        transition: background 0.3s;
        text-align: left;
    }

    .prediction-btn:hover {
        background: #2980b9;
    }

    /* Main content area */
    .content {
        flex-grow: 1;
        padding: 20px;
        overflow-y: auto;
        background: #ffffff;
    }

    .content h2 {
        margin-top: 0;
        color: #2c3e50;
        font-size: 1.5em;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    #workspaceIdDisplay {
        font-size: 0.9em;
        color: #7f8c8d;
        font-weight: normal;
        background: #ecf0f1;
        padding: 4px 8px;
        border-radius: 4px;
    }

    /* Table styling */
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

    #result .error {
        color: #e74c3c;
        width: 980px;
        margin-left: 25px;
    }

    #result .loading {
        color: #7f8c8d;
        font-style: italic;
    }

    /* Close button */
    .close-btn {
        position: absolute;
        top: 10px;
        right: 10px;
        background: #e74c3c;
        color: white;
        border: none;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.3s;
    }

    .close-btn:hover {
        background: #c0392b;
    }

    .close-btn:focus {
        outline: none;
    }

   

    /* Responsive design */
    @media (max-width: 600px) {
        .modal-content {
            width: 95%;
            max-height: 90vh;
        }
        .sidebar {
            width: 150px;
        }
        .content {
            padding: 15px;
        }
        .content h2 {
            flex-direction: column;
            align-items: flex-start;
        }
    }

    li.list-btns {
    list-style: none;
    display: flex;
}

#predictionButtons button {
    margin-bottom: 15px;
    border: 0;
    padding: 7px 15px;
    border-radius: 5px;
}

.main-layout {
    display: flex;
    flex-direction: row;
    gap: 20px;
}

/* Sidebar styling */
.sidebar {
    width: 250px;
    height: 79vh;
    overflow-y: auto;
    padding: 15px;
    border: 1px solid #ddd;
    background-color: #f7f7f7;
    border-radius: 6px;
}


/* Scrollbar styling (optional) */
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

/* Prediction table content */
.prediction-content {
    flex-grow: 1;
    overflow-x: auto;
}

/* Buttons inside sidebar */
#predictionButtons button {
    display: block;
    width: 100%;
    margin-bottom: 10px;
    padding: 10px;
    font-size: 14px;
    background: none;
    color: #7B83EB;;
    border: 1px solid #7B83EB;;
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
    transition: background 0.3s;
}

#predictionButtons button:hover {
    background-color: #7B83EB;
    color:#fff;
}



.dataTables_wrapper {
    position: relative;
    background: #fcfbfc;
    padding: 30px;
    border-radius: 20px;
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
 <div class="logo"><img class="warehouse-logo" alt="wi Logo" src="http://tychons.com/wp-content/uploads/2025/09/warehouse_logo-2.png"> </div>

    <h1>Predictions</h1>
  

    <div class="main-layout">
        <div id="predictionButtons" class="sidebar"></div>
        <div id="result" class="prediction-content"></div>
    </div>
    <div class="prediction-column">
    
    <div id="result"></div>
    </div>

    <footer>
    <div class="copyright">
    <p>© 2025 Tychons USA LLC. All Rights Reserved</p>
    </div>
    </footer>

    <script>

  
 

      
        function getWorkspaceIdFromUrl() {
            const params = new URLSearchParams(window.location.search);
            return params.get("workspace_id") || "unknown";
        }

        function formatPredictionType(type) {
            return type
                .split("_")
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(" ");
        }

        async function loadPredictions() {
            const workspace_id = getWorkspaceIdFromUrl();
           
            const predictionButtons = document.getElementById("predictionButtons");
            predictionButtons.innerHTML = '<p class="loading">Loading predictions...</p>';

            try {
                const response = await fetch(`/api/v0/get_prediction_configs?workspace_id=${encodeURIComponent(workspace_id)}`);
                const data = await response.json();

                if (data.type === "error") {
                    predictionButtons.innerHTML = `<p class="error">Error: ${data.error}</p>`;
                    return;
                }

                const predictions = data.predictions || [];
                predictionButtons.innerHTML = "";

                if (predictions.length === 0) {
                    predictionButtons.innerHTML = "<p>No predictions available.</p>";
                } else {
                    predictions.forEach(prediction => {
                        if (prediction.enabled) {
                            const button = document.createElement("button");
                            button.textContent = formatPredictionType(prediction.type);
                            button.onclick = () => fetchPrediction(prediction.type);
                            predictionButtons.appendChild(button);
                        }
                    });
                }
            } catch (error) {
                predictionButtons.innerHTML = `<p class="error">Failed to load predictions: ${error.message}</p>`;
            }
        }


        //fetch and display the data in datatable form
        async function fetchPrediction(prediction_type) {
    const workspace_id = getWorkspaceIdFromUrl();
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = '<p class="loading">Loading...</p>';

    try {
        const response = await fetch(`/api/v0/run_prediction?workspace_id=${encodeURIComponent(workspace_id)}&prediction_type=${encodeURIComponent(prediction_type)}`);
        const data = await response.json();

        if (data.type === "error" || data.type === "sql_error") {
            resultDiv.innerHTML = `<p class="error">Error: ${data.error}</p>`;
            return;
        }

        if (data.df && data.df.length > 0) {
            // Build HTML table
            let html = '<table id="predictionTable" class="display"><thead><tr>';
            const headers = Object.keys(data.df[0]);

            // Table headers
            headers.forEach(header => {
                html += `<th>${header.replace("_", " ").toUpperCase()}</th>`;
            });
            html += '</tr></thead><tbody>';

            // Table rows
            data.df.forEach(row => {
                html += '<tr>';
                headers.forEach(header => {
                    html += `<td>${row[header] ?? "NULL"}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table>';
            resultDiv.innerHTML = html;

            // Initialize DataTable with CSV export
            setTimeout(() => {
                $('#predictionTable').DataTable({
                    dom: 'Bfrtip',
                    buttons: [
                        {
                            extend: 'csvHtml5',
                            text: '⬇️ Export CSV',
                            title: `Prediction_${prediction_type}_${workspace_id}`
                        }
                    ]
                });
            }, 0);
        } else {
            resultDiv.innerHTML = "<p>No data available.</p>";
        }
    } catch (error) {
        resultDiv.innerHTML = `<p class="error">Failed to fetch prediction: ${error.message}</p>`;
    }
}




        window.onload = loadPredictions;
    </script>
</body>
</html>
"""
