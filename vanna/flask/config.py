index_template = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/x-icon" href="icon.ico?v=2">
    <title>Workspace Manager</title>

    <!-- jQuery (must be first for DataTables) -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

    <!-- DataTables CSS & JS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>

    <!-- DataTables Buttons extension -->
    <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.3.6/css/buttons.dataTables.min.css">
    <script src="https://cdn.datatables.net/buttons/2.3.6/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.3.6/js/buttons.html5.min.js"></script>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <!-- PapaParse -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js"></script>

    <!-- Toastify -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/toastify-js/1.12.0/toastify.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/toastify-js/1.12.0/toastify.min.js"></script>

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">

    <!-- Google Fonts preconnect -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">

    <style>
        /* Existing styles remain unchanged except for minor additions */
        body {
            font-family: 'Inter', Arial, sans-serif;
            margin: 0;
            display: flex;
            background: #f5f7fa;
            color: #2d3748;
        }
      .sidebar {
            width: 280px;
            background: #ffffff;
            height: calc(100vh - 56px); /* Full height minus top offset */
            padding: 24px;
            box-shadow: 4px 0 12px rgba(0, 0, 0, 0.05);
            position: absolute;
            top: 56px;
            left: 18px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            overflow-y: auto; /* Enables vertical scroll */
            transition: all 0.3s ease;
        }

        .menu, .submenu, .sub-options {
            list-style: none;
            padding: 0;
        }
        .menu-item {
            padding: 12px 16px;
            cursor: pointer;
            border-radius: 8px;
            color: #4a5568;
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        }
        .menu-item:hover {
            background: #edf2f7;
            color: #2b6cb0;
        }
        .menu-item i {
            font-size: 18px;
            transition: transform 0.3s ease;
        }
        .menu-item.active i.fa-chevron-right {
            transform: rotate(90deg);
        }
        .submenu {
            padding-left: 0;
            margin-top: 8px;
        }
       

        .submenu li {
    padding: 0;
    cursor: pointer;
    border-radius: 8px;
    color: #718096;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
    list-style: none;
}

        .workspace-item {
            display: flex;
            flex-direction: column;
            padding: 8px 16px;
            border-radius: 8px;
            background: #f7fafc;
            margin-bottom: 6px;
            width: 220px;
            transition: all 0.3s ease;
        }

        .workspace-item:hover {
            background: #edf2f7;
            transform: translateX(4px);
        }
        .workspace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
        }
        .workspace-header span {
            font-weight: 500;
            color: #2d3748;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .workspace-header span i {
            font-size: 16px;
            color: #7B83EB;
        }
      .connect-button {
            background: none;
            padding: 6px 14px;
            border: 1px solid #7B83EB;
            color: #7B83EB;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

     .connect-button:hover {
            background: #7B83EB;
            transform: scale(1.05);
            color: #fff;
        }
        .sub-options {
            display: none;
            padding: 8px 16px;
            margin-top: 4px;
            background: #ffffff;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        .sub-options li {
            padding: 6px 8px;
            cursor: pointer;
            border-radius: 4px;
            color: #4a5568;
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s ease;
        }
        .sub-options li:hover {
            background: #e2e8f0;
            color: #2d3748;
        }
        .sub-options li i {
            font-size: 14px;
            color: #718096;
            min-width: 14px;
        }
        .sub-section-label {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: #718096;
            padding: 10px 8px 3px 8px;
            pointer-events: none;
            cursor: default;
        }
        .sub-section-label:not(:first-child) {
            border-top: 1px solid #e2e8f0;
            margin-top: 4px;
            padding-top: 10px;
        }
        .main-content {
            margin-left: 340px;
            padding: 24px;
            width: calc(100% - 340px);
            background: #f5f7fa;
            min-height: 100vh;
        }
         .sql-connection:hover {
            background: #7B83EB;
            transform: scale(1.05);
            color: #fff;
        }

        .sql-connection {
            background: none;
            padding: 8px 20px;
            border: 1px solid #7B83EB;
            color: #7B83EB;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            position: absolute;
            left: 22%;
        }
        
        #savedWorkspaces {
            position: relative;
            top: 50px;
            padding-left: 0px;
        }

        #questionSQLFields input {
            height: 30px;
            position: relative;
            bottom: 14px;
            border: 1px solid #cbcbcb;
        }

#anomalyList > div {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    width: 96%;
}
    
        
        .modal {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 24px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            width: 40%;
            border-radius: 12px;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 12px;
        }
        .modal-header h3 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
        }
        .modal input {
            width: 97%;
            padding: 10px;
            margin: 8px 0 16px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            background: #f7fafc;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        .modal input:focus {
            border-color: #4299e1;
            outline: none;
        }
        .modal button {
            padding: 8px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            background: #4299e1;
            color: white;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .modal button:hover {
            background: #3182ce;
        }
        .overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            z-index: 999;
        }
        .content-section {
            padding: 24px;
            background: #ffffff;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            margin-top: 30px;
        }
        .content-section h4 {
            margin: 0 0 16px;
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
        }
        .content-section select, .content-section input, .content-section textarea {
            width: 96%;
            padding: 10px;
            margin: 6px 0 12px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        .content-section select:focus, .content-section input:focus, .content-section textarea:focus {
            border-color: #4299e1;
            outline: none;
        }
        .content-section button {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .test {
            background: #48bb78;
            color: white;
            margin-right: 12px;
        }
        .test:hover {
            background: #38a169;
        }
        .save {
            background: #4299e1;
            color: white;
        }
        .save:hover {
            background: #3182ce;
        }
        .connect-vanna-btn {
            background: linear-gradient(90deg, #48bb78, #38a169);
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            color: white;
            transition: all 0.3s ease;
            margin-bottom: 16px;
        }
        .connect-vanna-btn:hover {
            background: linear-gradient(90deg, #38a169, #2f855a);
        }
        #dropArea {
            border: 2px dashed #4299e1;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            color: #4299e1;
            cursor: pointer;
            margin-bottom: 16px;
            transition: all 0.3s ease;
        }
        #dropArea.dragover {
            background-color: #ebf8ff;
            border-color: #3182ce;
        }
        #dataTable {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 14px;
        }
        #dataTable th, #dataTable td {
            border: 1px solid #e2e8f0;
            padding: 10px;
            text-align: left;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        #dataTable th {
            background-color: #f7fafc;
            font-weight: 600;
            color: #2d3748;
        }
        #dataGrid {
            overflow-x: auto;
            max-height: 320px;
            overflow-y: auto;
            margin-bottom: 16px;
        }
         #uploadButton, #trainButton {
            background: none;
            color: #7B83EB;
            padding: 8px 16px;
            border: 1px solid #7B83EB;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
            margin: 15px 12px 15px 0px;
        }
        #uploadButton:hover, #trainButton:hover {
            background: #7B83EB;
            color: #fff;
        }
        .success-message {
            position: fixed;
            top: 10px;
            right: 25%;
            background-color: #48bb78;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            display: none;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        .error-message {
            position: fixed;
            top: 5px;
            right: 25%;
            background-color: #f56565;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            display: none;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        .logo {
            position: fixed;
            left: 8%;
        }
        .logo-title {
            font-size: 24px;
            font-family: "Roboto", sans-serif;
            font-weight: 700;
            color: #000;
            margin: 5px 0;
        }
        span.logo-ai {
            font-size: 35px;
            color: #000;
        }
       
        
        .dataTable {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 14px;
        }
        .dataTable th, .dataTable td {
            border: 1px solid #e2e8f0;
            padding: 10px;
            text-align: left;
        }
        .dataTable th {
            background-color: #f7fafc;
            font-weight: 600;
        }
        .modal_Training {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.4);
        }
        .modal-content {
            background-color: #fefefe;
            margin: 15% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            max-width: 500px;
            border-radius: 15px;
        }
        .close-btn {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .training-data-table {
            width: 100%;
            margin-top: 20px;
        }
    



         /* Hide the default checkbox */
            .switch input {
                opacity: 0;
                width: 0;
                height: 0;
            }
 
            /* Style the toggle switch */
            .switch {
                position: relative;
                display: inline-block;
                width: 50px;
                height: 25px;
                bottom: 12px;
            }
 
            /* The slider (background) */
            .slider {
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: #ccc;
                transition: 0.4s;
                border-radius: 25px;
            }
 
            /* Circle inside the switch */
            .slider:before {
                position: absolute;
                content: "";
                height: 18px;
                width: 18px;
                left: 4px;
                bottom: 3px;
                background-color: white;
                transition: 0.4s;
                border-radius: 50%;
            }
 
            /* Checked state styles */
            input:checked + .slider {
                background-color: #4caf50;
            }
 
            input:checked + .slider:before {
                transform: translateX(25px);
            }
            .team-webhook{
                display: block;
            }
/* Toggle Label Styling */
label.switch + span {
    font-weight: 600;
    font-size: 14px;
    padding: 6px 12px;
    border-radius: 6px;
    margin-left: 8px;
    display: inline-block;
    transition: all 0.3s ease;
    cursor: pointer;
}

label.switch + span.enabled {
    background: none; /* Blue for enabled state */
    color: #5cb85c;
    border: 1px solid #5cb85c;
}


label.switch + span.disabled {
    background: none; /* Gray for disabled state */
    color: #e53e3e;
    border: 1px solid #e53e3e;
}

/* Prediction Container Layout */
#predictionList > div {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin-bottom: 10px;
    background-color: #fafafa;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

#predictionList span {
    font-weight: 500;
    min-width: 200px;
    display: inline-block;
    color: #000;
}

table.dataTable{
color: #000;
}


 
//sidebar
 
.modal label {
    color: #000;
}

.dataTables_wrapper {
    position: relative;
    background: #fcfbfc;
    padding: 30px;
    border-radius: 20px;
}
 



/* Button Styling */
button.test, button.save {
    background: none;
    color: #7B83EB;
    border:  1px solid #7B83EB;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background-color 0.2s ease-in-out;
}

button.test:hover, button.save:hover {
    background-color: #7B83EB;
    color: #fff;
}


button.test:disabled, button.save:disabled {
    background-color: #b0bec5; /* Match toggle disabled color */
    cursor: not-allowed;
}

/* Section Spacing */
#predictionsContainer > div:first-child {
    margin-top: 10px;
}

/* Subsection Titles */
h5 {
    margin-bottom: 12px;
    font-size: 1.15rem;
    color: #263238; /* Darker shade for better contrast */
}

/* Input field spacing */
#suggestedPredictionsView input,
#predictionForm input,
#predictionForm textarea,
#predictionForm select {
    margin-bottom: 12px;
    width: 96%;
    padding: 8px;
    border: 1px solid #b0bec5;
    border-radius: 4px;
    font-size: 0.9rem;
}

/* Toggle Switch Styling */
label.switch {
    position: relative;
    display: inline-block;
    width: 40px;
    height: 20px;
    top: 1px;
}

label.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

label.switch .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #b0bec5; /* Gray for off state */
    transition: 0.3s;
    border-radius: 20px;
}

label.switch input:checked + .slider {
    background-color: #1e88e5; /* Blue for on state */
}

label.switch .slider:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 2px;
    bottom: 2px;
    background-color: white;
    transition: 0.3s;
    border-radius: 50%;
}

label.switch input:checked + .slider:before {
    transform: translateX(20px);
}

/* Optional Tooltip Styling */
label.switch[data-tooltip]::after {
    content: attr(data-tooltip);
    position: absolute;
    left: 110%;
    top: 50%;
    transform: translateY(-50%);
    background-color: #263238;
    color: #fff;
    padding: 4px 8px;
    font-size: 0.75rem;
    white-space: nowrap;
    border-radius: 4px;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s;
}

label.switch[data-tooltip]:hover::after {
    opacity: 1;
}
    .loader {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        animation: spin 1s linear infinite;
        display: inline-block;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }


.tdpopup-btn, #updateBtn {
    padding: 7px 15px;
    background: none;
    border: 1px solid #7B83EB;
    color: #7B83EB;
    border-radius: 5px;
    margin-top: 15px;
    margin-left: 15px;
}

.tdpopup-btn:hover, #updateBtn:hover{
    background: #7B83EB;
    border: 1px solid #7B83EB;
    color: #fff;
}

#editSQL {
    border: 1px solid #cbcbcb;
    height: 80px;
}

#editQuestion {
    height: 30px;
    margin-bottom: 15px;
    position: relative;
    top: -12px;
    border: 1px solid #cbcbcb;
}

.edit-input {
    display: flex;
    flex-direction: column;
    padding: 15px;
}

#questionSQLFields {
    display: flex;
    flex-direction: column;
    padding: 15px;
}

textarea#newSQL {
    border: 1px solid #cbcbcb;
}

#algorithm, #processSelect, #openai_model, #model_type,#anomalyProcessSelect{
 
    width: 97.9% !important;
 
}
 
 
 
#trainingDataTable_filter label {
 
    display: flex;
 
    margin: 15px;
 
}
 
 
 
#trainingDataTable_filter label input {
 
    margin-top: 0;
 
}
 
 
 
@media only screen and (min-width: 768px) and (max-width: 1024px){
 
.dataTables_wrapper{
 
   padding: 0px;
 
}
 
}
 
.toggle-container {
 
    display: flex;
 
    align-items: center;
 
    margin-bottom: 10px;
 
}
 
 
 
.toggle-container label:first-child {
 
    width: 200px;
 
    display: inline-block;
 
}
 
.toggle-container:has(#followup_questions),
.toggle-container:has(#ask_results_correct),
.toggle-container:has(#suggested_questions),
.toggle-container:has(#auto_fix_sql) {
    display: none;
}

 
.toggle-switch {
 
    position: relative;
 
    display: inline-block;
 
    width: 60px;
 
    height: 34px;
 
}
 
 
 
.toggle-switch input {
 
    opacity: 0;
 
    width: 0;
 
    height: 0;
 
}
 
 
 
.slider {
 
    position: absolute;
 
    cursor: pointer;
 
    top: 0;
 
    left: 0;
 
    right: 0;
 
    bottom: 0;
 
    background-color: #ccc;
 
    transition: 0.4s;
 
    border-radius: 34px;
 
}
 
 
 
.slider:before {
 
    position: absolute;
 
    content: "";
 
    height: 26px;
 
    width: 26px;
 
    left: 4px;
 
    bottom: 4px;
 
    background-color: white;
 
    transition: 0.4s;
 
    border-radius: 50%;
 
}
 
 
 
input:checked + .slider {
 
    background-color: #4CAF50;
 
}
 
 
 
input:checked + .slider:before {
 
    transform: translateX(26px);
 
}
 
   

    </style>
</head>
<body>

    <div id="globalLoader" style="display: none; text-align: center; margin-top: 20px;">
    <span class="loader"></span> Please wait...
</div>


    <div id="successMessage" class="success-message"></div>
    <div id="errorMessage" class="error-message"></div>

       <div class="logo">
                  <div class="logo"><img class="warehouse-logo" alt="wi Logo" src="http://tychons.com/wp-content/uploads/2025/09/warehouse_logo-2.png"></div>
          <button id="themeToggle" style="display:none; position: fixed; top: 10px; right: 10px; z-index: 1000; padding: 8px 12px; border: none; border-radius: 6px; cursor: pointer; background-color: #4299e1; color: white; font-weight: 500;">
        </button>
    </div>
       
    </div>

   <!-- Sidebar -->
    <div class="sidebar">
        <ul class="menu">
            <li class="menu-item" onclick="toggleMenu('workspace')">
                <i class="fas fa-building"></i>
                <span>Workspaces</span>
                <i class="fas fa-chevron-right"></i>
            </li>
            <ul class="submenu" id="workspace">
                <li><button class="sql-connection" onclick="openWorkspaceModal()">+ Create Workspace</button></li>
                <ul id="savedWorkspaces"></ul>
            </ul>
        </ul>
    </div>

    <!-- Main Content Area -->
    <div class="main-content" id="mainContent">
        <div class="content-section" id="contentArea" style="display: none;"></div>
    </div>

    <!-- Create Workspace Modal -->
    <div class="overlay" id="workspaceOverlay"></div>
    <div class="modal" id="workspaceModal">
        <div class="modal-header">
            <h3>Create Workspace</h3>
            <span class="close" onclick="closeWorkspaceModal()">×</span>
        </div>
        <label for="workspaceName">Workspace Name:</label>
        <input type="text" id="workspaceName" placeholder="Enter workspace name">
        <button class="save" onclick="saveWorkspaceName()">Save</button>
    </div>

    <!-- Training Data Modals -->

 <div id="editModalTraining" class="modal_Training">
        <div class="modal-content">
            <span class="close-btn">×</span>
            <h2>Edit Training Data</h2>
            <div class="edit-input">
            <input type="text" id="editQuestion" placeholder="Question">
            <textarea id="editSQL" placeholder="SQL Query"></textarea>
            </div>
            <div class="update-btn">
            <button id="updateBtn">Update</button>
            </div>
        </div>
    </div>

    <div id="newModalTraining" class="modal_Training">
        <div class="modal-content">
            <span class="close-btn">×</span>
            <h2 id="modalTitle">New Training Data</h2>
            <div id="questionSQLFields">
                <input type="text" id="newQuestion" placeholder="Question">
                <textarea id="newSQL" placeholder="SQL Query"></textarea>
            </div>
            <div id="documentationField" style="display: none;">
                <textarea id="newDocumentation" placeholder="Enter document training data"></textarea>
            </div>
            <button id="saveBtn" class="tdpopup-btn">Save</button>
            <button id="docTrainingBtn" class="tdpopup-btn">Documentation Training</button>
        </div>
    </div>


    <script>


    const STOCKOUT_SCENARIOS = [
    { id: "sku_missing", name: "SKU Not in Inventory" },
    { id: "qty_shortage", name: "Order Qty > Available Stock" },
    { id: "zero_before_pick", name: "Stock Becomes Zero Before Picking" },
    { id: "pick_task_fail", name: "Pick Task Creation Failure" },
    { id: "lost_during_pick", name: "Stock Lost During Picking" },
    { id: "status_unusable", name: "Inventory Exists But Not Usable" },
    { id: "cycle_zero", name: "Cycle Count Adjustment to Zero" },
    { id: "system_physical_mismatch", name: "System Stock Exists But Physical Missing" },
    { id: "expired_inventory", name: "Expired Inventory Only" },
    { id: "inbound_missing", name: "Inbound Dependency Stockout" },
    { id: "manual_adjustment", name: "Manual Inventory Adjustment" }
];

const STOCKOUT_DEFAULT_SQL = {
    sku_missing: `SELECT ord.order_number, ord.item_number
                  FROM t_order_detail ord
                  WHERE ord.item_number NOT IN (
                      SELECT item_number FROM t_stored_item
                  );`,

    qty_shortage: `SELECT ord.order_number, ord.item_number, ord.qty AS ordered_qty, sto.actual_qty
                   FROM t_order_detail ord
                   JOIN t_stored_item sto
                     ON ord.item_number = sto.item_number
                   WHERE ord.qty > sto.actual_qty;`,

    zero_before_pick: `SELECT ord.order_number, ord.item_number, ord.qty AS required_qty,
                       ISNULL(sto.actual_qty,0) AS available_qty
                       FROM t_order_detail ord
                       LEFT JOIN t_stored_item sto
                         ON ord.item_number = sto.item_number
                       WHERE ISNULL(sto.actual_qty,0) <= 0
                          OR ord.qty > ISNULL(sto.actual_qty,0);`,
                
    pick_task_fail: `SELECT ord.order_number, ord.item_number, ord.qty AS required_qty,
                       ISNULL(sto.actual_qty,0) AS available_qty
                       FROM t_order_detail ord
                       LEFT JOIN t_stored_item sto
                         ON ord.item_number = sto.item_number
                       WHERE ISNULL(sto.actual_qty,0) <= 0
                          OR ord.qty > ISNULL(sto.actual_qty,0);`,
    
    lost_during_pick: `SELECT ord.order_number, ord.item_number, ord.qty AS required_qty,
                       ISNULL(sto.actual_qty,0) AS available_qty
                       FROM t_order_detail ord
                       LEFT JOIN t_stored_item sto
                         ON ord.item_number = sto.item_number
                       WHERE ISNULL(sto.actual_qty,0) <= 0
                          OR ord.qty > ISNULL(sto.actual_qty,0);`,                       

    status_unusable: `SELECT ord.order_number, ord.item_number
                      FROM t_order_detail ord
                      WHERE ord.item_number IN (
                          SELECT item_number FROM t_stored_item WHERE status <> 'A'
                      );`,

    status_unusable: `SELECT ord.order_number, ord.item_number, ord.qty AS required_qty,
                       ISNULL(sto.actual_qty,0) AS available_qty
                       FROM t_order_detail ord
                       LEFT JOIN t_stored_item sto
                         ON ord.item_number = sto.item_number
                       WHERE ISNULL(sto.actual_qty,0) <= 0
                          OR ord.qty > ISNULL(sto.actual_qty,0);`,

    cycle_zero: `SELECT cc.trigger_id, cc.wh_id, cc.item_number, cc.location_id,
                        cc.reason, cc.triggered_during, cc.trigger_date, sto.actual_qty
                 FROM t_cycle_count_trigger cc
                 JOIN t_stored_item sto
                   ON cc.item_number = sto.item_number
                 WHERE cc.triggered_during LIKE '%Inventory Adj%'
                   AND sto.actual_qty = 0;`,

    system_physical_mismatch: `SELECT DISTINCT tl.item_number, sto.actual_qty, tl.description
                               FROM t_tran_log tl
                               JOIN t_stored_item sto
                                 ON tl.item_number = sto.item_number
                               WHERE tl.description LIKE '%Adjust%'
                                 AND sto.actual_qty = 0;`,

    expired_inventory: `SELECT DISTINCT ord.order_number, ord.item_number, sto.expiration_date
                        FROM t_order_detail ord
                        JOIN t_stored_item sto
                          ON ord.item_number = sto.item_number
                        WHERE sto.expiration_date < GETDATE();`,

    inbound_missing: `SELECT ord.order_number, ord.item_number
                      FROM t_order_detail ord
                      WHERE NOT EXISTS (
                          SELECT 1 FROM t_aht_receipt rcp
                          WHERE rcp.item_number = ord.item_number
                      );`,

    manual_adjustment: `SELECT DISTINCT ord.order_number, ord.item_number, sto.actual_qty
                        FROM t_order_detail ord
                        JOIN t_stored_item sto
                          ON ord.item_number = sto.item_number
                        JOIN t_tran_log tl
                          ON ord.item_number = tl.item_number
                        WHERE tl.description LIKE '%Inventory Adjust%';`
};




//data integratity agent

const DATA_INTEGRITY_SCENARIOS = [
    { id: "duplicate_approval", name: "Duplicate Approval Alert" },
    { id: "duplicate_cycle_transaction", name: "Duplicate Cycle Count Transaction Alert" },
    { id: "duplicate_adjustment", name: "Duplicate Adjustment Records Alert" }
];

const DATA_INTEGRITY_SQL_MAP = {
    duplicate_approval: `
        SELECT *
        FROM (
            SELECT *,
                   COUNT(*) OVER (
                       PARTITION BY work_q_id, location_id, item_number, hu_id
                   ) AS duplicate_count
            FROM t_cycle_count_approval WITH (NOLOCK)
            WHERE approval_status = 'Open'
        ) t
        WHERE duplicate_count > 1
    `,
    duplicate_cycle_transaction: `
        SELECT *
FROM (
    SELECT *,
           COUNT(*) OVER (
               PARTITION BY
                   control_number,
                   location_id,
                   item_number,
                   hu_id,
                   tran_qty
           ) AS duplicate_count,
           CAST(start_tran_date AS DATETIME)
           + CAST(end_tran_time AS DATETIME) AS tran_datetime
    FROM t_tran_log WITH(NOLOCK)
    WHERE tran_type = '800'
      AND location_id IS NOT NULL
      AND tran_qty IS NOT NULL
) duplicate_transactions
WHERE duplicate_count > 1
  AND tran_datetime >= DATEADD(HOUR, 7, CAST(CAST(GETDATE()-1 AS DATE) AS DATETIME))
  AND tran_datetime <  DATEADD(HOUR, 7, CAST(CAST(GETDATE()   AS DATE) AS DATETIME))
ORDER BY tran_datetime DESC;
    `,
    duplicate_adjustment: `
        SELECT *
        FROM (
            SELECT *,
                   COUNT(*) OVER (
                       PARTITION BY transaction_code, item_number,
                                quantity_before, quantity_after,
                                quantity_change, hu_id,
                                from_location_id, to_location_id,
                                user_id, reason_code
                   ) AS duplicate_count
            FROM t_al_host_inventory_adjustment WITH (NOLOCK)
        ) t
        WHERE duplicate_count > 1
    `
};


    let isDocumentationMode = false;

    function toggleModalMode() {
        const questionSQLFields = document.getElementById('questionSQLFields');
        const documentationField = document.getElementById('documentationField');
        const modalTitle = document.getElementById('modalTitle');
        
        isDocumentationMode = !isDocumentationMode;
        
        if (isDocumentationMode) {
            questionSQLFields.style.display = 'none';
            documentationField.style.display = 'block';
            modalTitle.textContent = 'New Documentation Training';
            document.getElementById('docTrainingBtn').textContent = 'Question-SQL Training';
        } else {
            questionSQLFields.style.display = 'block';
            documentationField.style.display = 'none';
            modalTitle.textContent = 'New Training Data';
            document.getElementById('docTrainingBtn').textContent = 'Documentation Training';
        }
        
        // Clear inputs when switching modes
        document.getElementById('newQuestion').value = '';
        document.getElementById('newSQL').value = '';
        document.getElementById('newDocumentation').value = '';
    }










      

        // Sidebar Menu Toggle
        function toggleMenu(menuId) {
            const menu = document.getElementById(menuId);
            const menuItem = document.querySelector(`.menu-item[onclick="toggleMenu('${menuId}')"]`);
            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
            menuItem.classList.toggle('active');
            fetchSavedWorkspaces();
        }

        // Workspace Modal
        function openWorkspaceModal() {
            document.getElementById('workspaceModal').style.display = 'block';
            document.getElementById('workspaceOverlay').style.display = 'block';
            document.getElementById('workspaceName').value = '';
        }

        function closeWorkspaceModal() {
            document.getElementById('workspaceModal').style.display = 'none';
            document.getElementById('workspaceOverlay').style.display = 'none';
        }

        // Global flag to track if Vanna has been initialized
        let isVannaConnected = false;

        // Connect to Vanna Endpoint with Redirect to /home
        function connectVanna(workspaceId) {
            fetch(`/get_workspace/${workspaceId}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showErrorMessage(data.error || 'Failed to fetch workspace data.');
                    return;
                }
                const requestData = {
                    workspace_id: workspaceId,
                    llm_details: {
                        model_name: data.llm_config.model_name || '',
                        model_type: data.llm_config.model_type || '',
                        api_key: data.llm_config.api_key || '',
                        base_url: data.llm_config.ollama_base_url || ''
                    },
                    db_details: {
                        serverName: data.db_config.serverName || '',
                        port: data.db_config.port || '',
                        databaseName: data.db_config.databaseName || '',
                        username: data.db_config.username || '',
                        password: data.db_config.password || '',
                        db_alias: data.db_config.db_alias || ''
                    },
                    db_details_b: data.db_config_b || {},
                    teams_config: {
                        webhookUrl: data.teams_config?.webhookUrl || '',
                        callbackUrl: data.teams_config?.callbackUrl || ''
                    }
                };
                return fetch('/connect-vanna', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccessMessage(data.message || 'Connected to WI successfully!');
                    isVannaConnected = true;
                    setTimeout(() => {
                        window.location.href = `/home?workspace_id=${workspaceId}`;
                    }, 1000);
                } else {
                    showErrorMessage(data.error || 'Failed to connect to WI.');
                    isVannaConnected = false;
                }
            })
            .catch(error => showErrorMessage('Error connecting to WI: ' + error));
        }

        // Initialize Vanna without redirect (for Predictions section)
       /* function initializeVanna(workspaceId) {
            fetch(`/get_workspace/${workspaceId}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showErrorMessage(data.error || 'Failed to fetch workspace data.');
                    return;
                }
                const requestData = {
                    workspace_id: workspaceId,
                    llm_details: {
                        model_name: data.llm_config.model_name || '',
                        model_type: data.llm_config.model_type || '',
                        api_key: data.llm_config.api_key || '',
                        base_url: data.llm_config.ollama_base_url || ''
                    },
                    db_details: {
                        serverName: data.db_config.serverName || '',
                        port: data.db_config.port || '',
                        databaseName: data.db_config.databaseName || '',
                        username: data.db_config.username || '',
                        password: data.db_config.password || ''
                    }
                };
                return fetch('/initialize-vanna', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccessMessage(data.message || 'WI initialized successfully!');
                    isVannaConnected = true;
                    // For Predictions: Enable predictions toggle
                    const toggleButton = document.getElementById('togglePredictions');
                    const predictionsState = document.getElementById('predictionsState');
                    const predictionsContainer = document.getElementById('predictionsContainer');
                    const addButton = document.querySelector('#predictionsContainer button.save');
                    if (toggleButton && predictionsState && predictionsContainer) {
                        toggleButton.classList.remove('disabled');
                        toggleButton.classList.add('enabled');
                        toggleButton.textContent = 'Disable Predictions';
                        predictionsState.textContent = 'Enabled';
                        predictionsState.classList.remove('disabled');
                        predictionsState.classList.add('enabled');
                        predictionsContainer.style.display = 'block';
                        addButton.disabled = false;
                    }
                } else {
                    showErrorMessage(data.error || 'Failed to initialize WI.');
                    isVannaConnected = false;
                }
            })
            .catch(error => {
                showErrorMessage('Error initializing WI: ' + error);
                isVannaConnected = false;
            });
        }
        */

        function initializeVanna(workspaceId) {
            fetch(`/get_workspace/${workspaceId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) throw new Error(data.error);
                    return fetch('/initialize-vanna', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            workspace_id: workspaceId,
                            llm_details: data.llm_config,
                            db_details: data.db_config,
                            db_details_b: data.db_config_b || {}
                        })
                    });
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        isVannaConnected = true;
                        showSuccessMessage(data.message || 'WI initialized successfully!');
                        updatePredictionToggleUI(true); //  Explicitly enable toggle
                        
                    } else {
                        throw new Error(data.error || 'Failed to initialize WI.');
                    }
                })


                .catch(err => {
                    isVannaConnected = false;
                    showErrorMessage(err.message);
                    updatePredictionToggleUI(false); //  Explicitly disable toggle on error
                });
        }

        // Modify your toggle handler
function togglePredictionsState(workspaceId) {
    const toggleButton = document.getElementById('togglePredictions');
    if (!toggleButton) return;

    if (toggleButton.checked) {
        // User is enabling
        toggleButton.disabled = true;
        initializeVanna(workspaceId);
        toggleButton.disabled = false;
    } else {
        // User is disabling
        isVannaConnected = false;
        updatePredictionToggleUI(false); //  Ensure toggle updates
        showSuccessMessage('Predictions disabled.');
    }
}


// Helper to sync toggle and UI text


function updatePredictionToggleUI(isEnabled) {
    const toggleButton = document.getElementById('togglePredictions');
    const predictionsState = document.getElementById('predictionsState');
    const predictionsContainer = document.getElementById('predictionsContainer');
    const addButton = document.querySelector('#defaultPredictionsView button.save');

    if (!toggleButton || !predictionsState || !predictionsContainer || !addButton) return;

    toggleButton.checked = isEnabled;
    predictionsState.textContent = isEnabled ? 'Enabled' : 'Disabled';
    predictionsState.classList.toggle('enabled', isEnabled);
    predictionsState.classList.toggle('disabled', !isEnabled);
    predictionsContainer.style.display = isEnabled ? 'block' : 'none';
    addButton.disabled = !isEnabled;
}




        function toggleWorkspaceOptions(id) {
            const options = document.getElementById(`options-${id}`);
            options.style.display = options.style.display === 'block' ? 'none' : 'block';
        }

        // Fetch tables (only if Vanna is initialized)
        function fetchTables(workspaceId) {
            if (!isVannaConnected) {
                showErrorMessage("Please initialize WI (LLM and DB) before accessing database schema.");
                return;
            }

            console.log("Fetching tables for workspace:", workspaceId);
            fetch(`/api/v0/get_tables?workspace_id=${workspaceId}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => {
                console.log("Response status:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("Fetched table data:", data);
                if (data.type === "error") {
                    showErrorMessage(data.error);
                    return;
                }
                const tableList = document.getElementById('tableList');
                tableList.innerHTML = '<option value="">--Select Table--</option>';
                data.tables.forEach(table => {
                    const option = document.createElement('option');
                    option.value = table;
                    option.textContent = table;
                    tableList.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error fetching tables:', error);
                //showErrorMessage('Error fetching tables: ' + error);
            });
        }

        // Fetch columns (only if Vanna is initialized)
        function fetchColumns() {
            if (!isVannaConnected) {
                showErrorMessage("Please initialize WI (LLM and DB) before accessing database schema.");
                return;
            }

            const workspaceId = document.getElementById('workspaceId').value;
            const tableName = document.getElementById('tableList').value;
            if (!tableName) {
                document.getElementById('columnList').innerHTML = '<option value="">--Select a table to view columns--</option>';
                return;
            }
            fetch(`/api/v0/get_columns?workspace_id=${workspaceId}&table_name=${tableName}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.type === "error") {
                    showErrorMessage(data.error);
                    return;
                }
                const columnList = document.getElementById('columnList');
                columnList.innerHTML = '';
                data.columns.forEach(column => {
                    const option = document.createElement('option');
                    option.value = column;
                    option.textContent = column;
                    columnList.appendChild(option);
                });
            })
            .catch(error => showErrorMessage('Error fetching columns: ' + error));
        }

        function insertColumnIntoQuery() {
            if (!isVannaConnected) {
                showErrorMessage("Please initialize WI (LLM and DB) before accessing database schema.");
                return;
            }

            const selectedColumns = Array.from(document.getElementById('columnList').selectedOptions).map(option => option.value);
            const tableName = document.getElementById('tableList').value;
            if (!selectedColumns.length || !tableName) {
                showErrorMessage('Please select a table and at least one column.');
                return;
            }
            const columnString = selectedColumns.join(', ');
            const sqlSnippet = `SELECT ${columnString} FROM ${tableName}`;
            const sqlQuery = document.getElementById('sqlQuery');
            sqlQuery.value = sqlQuery.value ? `${sqlQuery.value}\n${sqlSnippet}` : sqlSnippet;
        }

        function testSqlQuery(fieldId) {
            if (!isVannaConnected) {
                showErrorMessage("Please initialize WI (LLM and DB) before testing SQL queries.");
                return;
            }

            const workspaceId = document.getElementById('workspaceId').value;
            const sqlQuery = document.getElementById(fieldId).value;
            const resultField = document.getElementById(`${fieldId}Result`);
            resultField.innerText = 'Testing SQL query...';
            resultField.style.color = 'blue';
            fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql_query: sqlQuery })
            })
            .then(response => response.json())
            .then(data => {
                if (data.type === "error" || data.type === "sql_error") {
                    resultField.innerText = `? ${data.error}`;
                    resultField.style.color = 'red';
                } else {
                    resultField.innerText = `Query executed successfully! Returned ${data.row_count} rows.`;
                    resultField.style.color = 'green';
                }
            })
            .catch(error => {
                resultField.innerText = `? Error testing SQL query: ${error}`;
                resultField.style.color = 'red';
            });
        }
/*
  function previewSqlQuery() {
            if (!isVannaConnected) {
                showErrorMessage("Please initialize WI (LLM and DB) before previewing data.");
                return;
            }

            const workspaceId = document.getElementById('workspaceId').value;
            const sqlQuery = document.getElementById('sqlQuery').value;
            fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql_query: sqlQuery })
            })
            .then(response => response.json())
            .then(data => {
                if (data.type === "error" || data.type === "sql_error") {
                    showErrorMessage(data.error);
                } else {
                    displayPredictionResults('Preview', data.df.slice(0, 5));
                    showSuccessMessage('Preview generated successfully!');
                }
            })
            .catch(error => showErrorMessage('Error previewing SQL query: ' + error));
        }

        */



//show datatable preview in prediction inside edinting the prediction or previewing the data
function previewSqlQuery() {
    if (!isVannaConnected) {
        showErrorMessage("Please initialize WI (LLM and DB) before previewing data.");
        return;
    }

    const workspaceIdInput = document.getElementById('workspaceId');
    const sqlQueryInput = document.getElementById('sqlQuery');
    const sqlQueryResult = document.getElementById('sqlQueryResult');

    // Validate DOM elements
    if (!workspaceIdInput || !sqlQueryInput || !sqlQueryResult) {
        showErrorMessage("Required form elements not found.");
        return;
    }

    const workspaceId = workspaceIdInput.value.trim();
    const sqlQuery = sqlQueryInput.value.trim();

    // Validate inputs
    if (!workspaceId) {
        showErrorMessage("Workspace ID is missing.");
        sqlQueryResult.innerHTML = '';
        return;
    }
    if (!sqlQuery) {
        showErrorMessage("Please enter an SQL query to preview.");
        sqlQueryResult.innerHTML = '';
        return;
    }

    // Show loading state
    sqlQueryResult.innerHTML = '<span>Loading preview...</span>';

    // Send SQL query to backend
    fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql_query: sqlQuery })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.type === "error" || data.type === "sql_error") {
            sqlQueryResult.innerHTML = '';
            showErrorMessage(data.error);
        } else if (data.df && data.df.length > 0) {
            // Render results in a table
            const results = data.df.slice(0, 5); // Limit to 5 rows
            let tableHtml = '<table class="dataTable"><thead><tr>';
            const columns = Object.keys(results[0]);
            columns.forEach(col => {
                tableHtml += `<th>${col}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';
            results.forEach(row => {
                tableHtml += '<tr>';
                columns.forEach(col => {
                    tableHtml += `<td>${row[col] !== null ? row[col] : ''}</td>`;
                });
                tableHtml += '</tr>';
            });
            tableHtml += '</tbody></table>';
            sqlQueryResult.innerHTML = tableHtml;
            showSuccessMessage('Preview generated successfully!');
        } else {
            sqlQueryResult.innerHTML = '<span>No data returned for this query.</span>';
            showSuccessMessage('Query executed successfully, but no data was returned.');
        }
    })
    .catch(error => {
        sqlQueryResult.innerHTML = '';
        showErrorMessage(`Error previewing SQL query: ${error.message}`);
    });
}

        function showAIProviders(id) {
            const contentArea = document.getElementById('contentArea');
            contentArea.innerHTML = `
                <h4>AI Providers</h4>
                <input type="hidden" id="workspaceId" value="${id}">
                <label for="model_type">Select Model Type:</label>
                <select id="model_type" onchange="toggleModelSelection()">
                    <option value="">--Select--</option>
                    <option value="ollama">Ollama Models</option>
                    <option value="openai">OpenAI Models</option>
                </select>
                <div id="ollamaBaseUrlDiv" style="display: none;">
                    <label for="ollama_base_url">Ollama Base URL:</label>
                    <input type="text" id="ollama_base_url" placeholder="http://127.0.0.1:11434/">
                </div>
                <div id="ollamaModelsDiv" style="display: none;">
                    <label for="ollama_model">Select Ollama Model:</label>
                    <select id="ollama_model"></select>
                </div>
                <div id="openaiModelsDiv" style="display: none;">
                    <label for="openai_model">Select OpenAI Model:</label>
                    <select id="openai_model" onchange="toggleApiKeyField()">
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="gpt-4">GPT-4</option>
                        <option value="gpt-4o">GPT-4O</option>
                        <option value="o3">O3</option>
                        <option value="gpt-5.1">GPT-5</option>
                    </select>
                </div>
                <div id="apiKeyField" style="display: none;">
                    <label for="api_key">API Key:</label>
                    <input type="password" id="api_key" placeholder="Enter API key">
                </div>
                <button class="test" onclick="testLLMConnection()">Test Connection</button>
                <p id="test-llm-result"></p>
                <button class="save" onclick="saveLLMConfig()">Save</button>
            `;
            contentArea.style.display = 'block';
            toggleModelSelection();
            loadWorkspaceConfig(id);
        }
        
        //admin config page (pavan)
        function showAIFeatures(id) {
            const contentArea = document.getElementById('contentArea');
            contentArea.innerHTML = `
                <h4>AI Features & Options</h4>
                <input type="hidden" id="workspaceId" value="${id}">
                <div id="aiFeatures">
                    <div class="toggle-container">
                        <label>Suggested Questions</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="suggested_questions">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>SQL Generation</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="sql">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>Table View</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="table" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>CSV Download</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="csv_download" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>Charts</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="chart" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>Redraw Charts</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="redraw_chart" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>Auto Fix SQL</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="auto_fix_sql" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>Ask if Results are Correct</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="ask_results_correct" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>Follow-up Questions</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="followup_questions" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="toggle-container">
                        <label>Summarization</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="summarization" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>
                <button class="save" onclick="saveAIOptions()">Save</button>
            `;
            contentArea.style.display = 'block';
            loadWorkspaceAIOptions(id);
 
            // ✅ Add dynamic event listeners
            const toggles = [
                'suggested_questions', 'sql', 'table', 'csv_download',
                'chart', 'redraw_chart', 'auto_fix_sql', 'ask_results_correct',
                'followup_questions', 'summarization'
            ];
 
            toggles.forEach(name => {
                const el = document.getElementById(name);
                el.addEventListener('change', () => {
                    const val = el.checked;
                    updateWorkspaceSettings(id, name, val);
                });
            });
        }
 
        async function saveAIOptions() {
            const workspaceId = document.getElementById("workspaceId").value;
 
            const payload = {
                workspace_id: workspaceId,
                suggested_questions: document.getElementById("suggested_questions").checked,
                sql: document.getElementById("sql").checked,
                table: document.getElementById("table").checked,
                csv_download: document.getElementById("csv_download").checked,
                chart: document.getElementById("chart").checked,
                redraw_chart: document.getElementById("redraw_chart").checked,
                auto_fix_sql: document.getElementById("auto_fix_sql").checked,
                ask_results_correct: document.getElementById("ask_results_correct").checked,
                followup_questions: document.getElementById("followup_questions").checked,
                summarization: document.getElementById("summarization").checked
            };
 
            try {
                const res = await fetch('/save-ai-options', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                if (!res.ok) {
                    const err = await res.json().catch(()=>({}));
                    console.error("Failed to save AI options", err);
                    alert("Failed to save AI options");
                    return;
                }
 
                // Now re-fetch config (use workspace_id param so backend picks it up robustly)
                const cfgResp = await fetch(`/api/v0/get_config?workspace_id=${encodeURIComponent(workspaceId)}`);
                const json = await cfgResp.json();
                console.log("Updated config:", json);
 
                // Force a page reload so Vanna Home re-renders UI using new config
                // (If you have a SPA update mechanism, call it instead)
                window.location.reload();
            } catch (e) {
                console.error("saveAIOptions error", e);
                alert("save error");
            }
        }
 
 
 
        // new helper
        // This function fetches the saved settings and updates the UI
        function refreshVannaHome(workspaceId) {
            fetch(`/get-ai-options/${workspaceId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error fetching AI options:', data.error);
                        return;
                    }
                   
                    const ai = data.ai_options;
 
                    // Make sure your home page HTML has these IDs!
                    // e.g., <div id="sqlSection">...</div>
                    // e.g., <div id="chartContainer">...</div>
                    // e.g., <div id="summaryBox">...</div>
                   
                    // Find the element and set its display style
                    const sqlSection = document.getElementById('sqlSection');
                    if (sqlSection) {
                        sqlSection.style.display = ai.sql ? 'block' : 'none';
                    }
 
                    const chartContainer = document.getElementById('chartContainer');
                    if (chartContainer) {
                        chartContainer.style.display = ai.chart ? 'block' : 'none';
                    }
 
                    const summaryBox = document.getElementById('summaryBox');
                    if (summaryBox) {
                        summaryBox.style.display = ai.summarization ? 'block' : 'none';
                    }
                   
                    // ... Add logic for all your other toggles here ...
                    // (followup_questions, suggested_questions, etc.)
                })
                .catch(err => console.error('Failed to refresh UI:', err));
        }
 
        // This runs when your home page finishes loading
        document.addEventListener('DOMContentLoaded', () => {
            fetch('/api/v0/get-active-workspace')
                .then(response => {
                    console.log("Raw response status:", response.status);
                    return response.json();
                })
                .then(data => {
                    // 🔴 THIS IS THE IMPORTANT LINE
                    console.log("get-active-workspace API returned:", data);

                    if (data.workspace_id) {
                        console.log("Workspace ID received:", data.workspace_id);

                        refreshVannaHome(data.workspace_id);

                    } else {
                        console.error("No workspace_id in response:", data);
                    }
                })
                .catch(err => {
                    console.error('Error fetching active workspace:', err);
                });
        });


 
       
        async function loadWorkspaceAIOptions(workspaceId) {
            try {
                const resp = await fetch(`/get-ai-options/${encodeURIComponent(workspaceId)}`);
                if (!resp.ok) return;
                const data = await resp.json();
                const ai = data.ai_options || data.effective_config || {};
 
                // Try keys directly
                document.getElementById("suggested_questions").checked = !!ai.suggested_questions;
                document.getElementById("sql").checked = !!ai.sql;
                document.getElementById("table").checked = !!ai.table;
                document.getElementById("csv_download").checked = !!ai.csv_download;
                document.getElementById("chart").checked = !!ai.chart;
                document.getElementById("redraw_chart").checked = !!ai.redraw_chart;
                document.getElementById("auto_fix_sql").checked = !!ai.auto_fix_sql;
                document.getElementById("ask_results_correct").checked = !!ai.ask_results_correct;
                document.getElementById("followup_questions").checked = !!ai.followup_questions;
                document.getElementById("summarization").checked = !!ai.summarization;
            } catch (e) {
                console.error("loadWorkspaceAIOptions error", e);
            }
        }
 
 
        async function updateWorkspaceSettings(workspaceId, settingName, value) {
            try {
                const response = await fetch('/api/update_workspace_settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        workspace_id: workspaceId,
                        settings: { [settingName]: value }
                    })
                });
                const result = await response.json();
                console.log("Updated:", settingName, "=", value, result);
            } catch (err) {
                console.error("Failed to update workspace settings:", err);
            }
        }
 // admin config completes

        function showDBConfig(id) {
            const contentArea = document.getElementById('contentArea');
            contentArea.innerHTML = `
                <h4>Database Configuration</h4>
                <input type="hidden" id="workspaceId" value="${id}">
                <label for="serverName">Server Name:</label>
                <input type="text" id="serverName" placeholder="Server Name">
                <label for="port">Port:</label>
                <input type="text" id="port" placeholder="Port">
                <label for="databaseName">Database Name:</label>
                <input type="text" id="databaseName" placeholder="Database Name">
                <label for="username">Username:</label>
                <input type="text" id="username" placeholder="Username">
                <label for="password">Password:</label>
                <input type="password" id="password" placeholder="Password">
                <button class="test" onclick="testConnection('')">Test Connection</button>
                <p id="test-db-result"></p>
                <button class="save" onclick="saveDBConfig('a')">Save</button>

                <hr style="margin:28px 0;border:none;border-top:1px solid #ddd;">

                <h4>Secondary Database <span style="font-weight:normal;color:#888;">(optional — linked server)</span></h4>
                <p style="color:#666;font-size:0.9em;max-width:560px;">
                    Connect a second database reached via a SQL Server linked server configured
                    from the primary connection above, for questions that need to join data across
                    both databases. Leave this section blank if this workspace only uses one database.
                </p>
                <label for="serverNameB">Server Name:</label>
                <input type="text" id="serverNameB" placeholder="Server Name">
                <label for="portB">Port:</label>
                <input type="text" id="portB" placeholder="Port">
                <label for="databaseNameB">Database Name:</label>
                <input type="text" id="databaseNameB" placeholder="Database Name">
                <label for="usernameB">Username:</label>
                <input type="text" id="usernameB" placeholder="Username">
                <label for="passwordB">Password:</label>
                <input type="password" id="passwordB" placeholder="Password">
                <label for="dbAliasB">Linked Server Alias:</label>
                <input type="text" id="dbAliasB" placeholder="Must match the linked server name configured on the primary SQL Server">
                <button class="test" onclick="testConnection('B')">Test Connection</button>
                <p id="test-db-result-B"></p>
                <button class="save" onclick="saveDBConfig('b')">Save Secondary DB</button>
            `;
            contentArea.style.display = 'block';
            loadWorkspaceConfig(id);
        }

let currentPredictions = [];
let suggestedPredictions = [];
const processTableMap = {
    "receiving_putaway": [
        "t_po_master",
        "t_po_detail",
        "t_receipt",
        "t_asn_master",
        "t_asn_detail",
        "t_tran_log",
        "t_location",
        "t_stored_item",
        "t_hu_master",
        "t_work_q"
    ],
    "planned_move": [
        "t_fwd_pick",
        "t_stored_item",
        "t_location",
        "t_hu_master",
        "t_tran_log",
        "t_work_q"
    ],
    "inventory_movement": [
        "t_stored_item",
        "t_location",
        "t_hu_master",
        "t_tran_log",
        "t_work_q"
    ],
    "inventory_adjustment": [
        "t_cc_ccc_adjustment",
        "t_stored_item",
        "t_location",
        "t_hu_master",
        "t_tran_log",
        "t_work_q"
    ],
    "waving": [
        "t_allocation",
        "t_allocation_q",
        "t_pick_detail",
        "t_tran_log",
        "t_stored_item",
        "t_location",
        "t_hu_master",
        "t_work_q"
    ],
    "order_processing": [
        "t_order",
        "t_order_detail",
        "t_allocation",
        "t_allocation_q",
        "t_pick_detail",
        "t_tran_log",
        "t_stored_item",
        "t_location",
        "t_hu_master",
        "t_work_q"
    ]
};


  /*  instant UI flip for the master toggle  */
        function flipMasterPredictionUI(){
            const toggle   = document.getElementById('masterPredictionToggle');
            const label    = document.getElementById('masterPredictionState');
            const isOn     = toggle.checked;

            label.textContent = isOn ? 'Enabled' : 'Disabled';
            label.classList.toggle('enabled',  isOn);
            label.classList.toggle('disabled', !isOn);
        }

//updated show predictions 
function showPredictions(id) {
    const contentArea = document.getElementById('contentArea');
    contentArea.innerHTML = `
        <h4>Predictions Configuration</h4>
        <input type="hidden" id="workspaceId" value="${id}">
        <p>Configure and run predictions for this workspace.</p>

        <!--  Master Toggle + Save -->
    

        <div style="margin-bottom:16px;display:flex;align-items:center;gap:10px">
        <label class="switch">
            <input type="checkbox"
                id="masterPredictionToggle"
                onchange="flipMasterPredictionUI()">   <!-- NEW -->
            <span class="slider"></span>
        </label>
        <span id="masterPredictionState" class="disabled">Disabled</span>
        <button class="save" onclick="saveMasterPredictionToggle('${id}')">Save</button>
        </div>

        <!--  Existing Enable/Disable Predictions Toggle -->
        <div style="margin-bottom: 16px;">
            <p>Initialize Saved Prediction</p>
            <label class="switch">
                
                <input type="checkbox" id="togglePredictions" onchange="togglePredictionsState('${id}')">
                <span class="slider"></span>
            </label>
            <span id="predictionsState" class="disabled">Disabled</span>
        </div>

        <div id="predictionsContainer" style="display: none;">
            <div style="margin-bottom: 16px;">
            <p>Switch Between Suggest Prediction and Default Prediciton</p>
                <label class="switch">
                    <input type="checkbox" id="viewToggle" onchange="toggleView()" checked>
                    <span class="slider"></span>
                </label>
                <span id="viewState" class="enabled">Default View</span>
            </div>
            <div id="defaultPredictionsView">
                <h5>Saved Predictions</h5>
                <div id="predictionList"></div>
                <button class="save" onclick="openAddPredictionForm()" disabled>Add New Prediction</button>
            </div>
            <div id="suggestedPredictionsView" style="display: none;">
                <h5>Suggested Predictions</h5>
                <label for="processSelect">Select Process:</label>
                <select id="processSelect">
                    <option value="" disabled selected>Select a process</option>
                    <option value="receiving_putaway">Receiving & Putaway</option>
                    <option value="planned_move">Planned Move</option>
                    <option value="inventory_movement">Inventory Movement</option>
                    <option value="inventory_adjustment">Inventory Adjustment & Cycle Counts</option>
                    <option value="waving">Waving</option>
                    <option value="order_processing">Order Picking, Packing, Staging, Loading & Shipping</option>
                </select>
                <label for="predictionQueryInput">Prediction Query:</label>
                <input type="text" id="predictionQueryInput" placeholder="e.g., Predict delays in order picking">
                <button class="test" onclick="fetchSuggestedPredictions()">Get Suggestions</button>
                <div id="suggestedPredictionList"></div>
                <div id="suggestionsLoader" style="display:none; margin-top:10px;">
                    <span class="loader"></span> Loading suggestions...
                </div>
            </div>
        </div>

        <div id="predictionForm" style="display: none; margin-top: 20px;">
            <h5 id="formTitle">Add New Prediction</h5>
            <input type="hidden" id="predictionId">
            <label for="predictionName">Prediction Name:</label>
            <input type="text" id="predictionName" placeholder="e.g., Delivery Time Prediction">
            <label for="sqlQuery">SQL Query:</label>
            <textarea id="sqlQuery" rows="4" placeholder="Enter SQL query to fetch data"></textarea>
            <button class="test" onclick="openSchemaExplorer()">Edit SQL with Schema</button>
            <button class="test" onclick="testSqlQuery('sqlQuery')">Test SQL Query</button>
            <button class="test" onclick="previewSqlQuery()">Preview Data</button>
            <p id="sqlQueryResult"></p>
            <label for="algorithm">Algorithm:</label>
            <select id="algorithm" onchange="updateParameterFields()">
                <option value="mean">Mean</option>
                <option value="linear_regression">Linear Regression</option>
                <option value="logistic_regression">Logistic Regression</option>
                <option value="standard_deviation">Standard Deviation</option>
                <option value="custom">Custom</option>
            </select>
            <div id="parameterFields" style="margin-top: 12px;"></div>
            <button class="save" onclick="savePrediction()">Save Prediction</button>
            <button class="test" onclick="closePredictionForm()">Cancel</button>
        </div>

        <div id="schemaExplorer" style="display: none; margin-top: 20px;">
            <h5>Database Schema Explorer</h5>
            <label for="tableList">Select Table:</label>
            <select id="tableList" onchange="fetchColumns()"></select>
            <label for="columnList">Columns:</label>
            <select id="columnList" multiple style="width: 100%; height: 100px;"></select>
            <button class="test" onclick="insertColumnIntoQuery()">Insert Column into SQL Query</button>
            <button class="test" onclick="closeSchemaExplorer()">Close Explorer</button>
        </div>

        <div id="predictionResults" style="margin-top: 20px;"></div>
    `;

    contentArea.style.display = 'block';

    // Initialize toggle states
    if (isVannaConnected) {
        const toggleButton = document.getElementById('togglePredictions');
        const predictionsState = document.getElementById('predictionsState');
        const predictionsContainer = document.getElementById('predictionsContainer');
        const addButton = document.querySelector('#defaultPredictionsView button.save');
        toggleButton.checked = true;
        predictionsState.textContent = 'Enabled';
        predictionsState.classList.remove('disabled');
        predictionsState.classList.add('enabled');
        predictionsContainer.style.display = 'block';
        addButton.disabled = false;
    }

    // Default view is enabled by default
    const viewToggle = document.getElementById('viewToggle');
    const viewState = document.getElementById('viewState');
    viewToggle.checked = true;
    viewState.textContent = 'Default View';
    viewState.classList.add('enabled');
    viewState.classList.remove('disabled');

    // Fetch predictions and tables
    fetchPredictionConfigs(id);
    fetchTables(id);
}

// Fetch existing prediction configs updated
function fetchPredictionConfigs(workspaceId) {
    fetch(`/api/v0/get_prediction_configs?workspace_id=${workspaceId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error") {
            showErrorMessage(data.error);
            return;
        }
        currentPredictions = data.predictions || [];
        updatePredictionList(currentPredictions, workspaceId);

        //Sync Master Toggle State
        const anyEnabled = currentPredictions.some(p => p.enabled);
        const allEnabled = currentPredictions.length > 0 && currentPredictions.every(p => p.enabled);

        const masterToggle = document.getElementById('masterPredictionToggle');
        const masterState = document.getElementById('masterPredictionState');

        if (masterToggle && masterState) {
            // Master toggle ON only if all are enabled
            masterToggle.checked = allEnabled;

            // Status is Enabled if at least one is enabled
            masterState.textContent = anyEnabled ? 'Enabled' : 'Disabled';
            masterState.classList.toggle('enabled', anyEnabled);
            masterState.classList.toggle('disabled', !anyEnabled);
        }

    })
    .catch(error => showErrorMessage('Error fetching prediction configs: ' + error));
}



//
function saveMasterPredictionToggle(workspaceId) {
    const isEnabled = document.getElementById('masterPredictionToggle').checked;

    // Update all predictions locally
    currentPredictions = currentPredictions.map(pred => ({ ...pred, enabled: isEnabled }));

    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            workspace_id: workspaceId,
            predictions: currentPredictions
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage(`All predictions ${isEnabled ? 'enabled' : 'disabled'}!`);
            updatePredictionList(currentPredictions, workspaceId);

            // Update UI
            const stateLabel = document.getElementById('masterPredictionState');
            stateLabel.textContent = isEnabled ? 'Enabled' : 'Disabled';
            stateLabel.classList.toggle('enabled', isEnabled);
            stateLabel.classList.toggle('disabled', !isEnabled);
        }
    })
    .catch(err => showErrorMessage('Error saving toggle: ' + err));
}

// Toggle between Default and Suggested Views
/*
function toggleView() {
    const viewToggle = document.getElementById('viewToggle');
    const viewState = document.getElementById('viewState');
    const defaultView = document.getElementById('defaultPredictionsView');
    const suggestedView = document.getElementById('suggestedPredictionsView');
    const predictionForm = document.getElementById('predictionForm');
    const isDefaultView = viewToggle.checked;

    viewState.textContent = isDefaultView ? 'Default View' : 'Suggested Predictions';
    viewState.classList.toggle('enabled', isDefaultView);
    viewState.classList.toggle('disabled', !isDefaultView);
    defaultView.style.display = isDefaultView ? 'block' : 'none';
    suggestedView.style.display = isDefaultView ? 'none' : 'block';
    predictionForm.style.display = isDefaultView ? 'none' : 'none'; // Hide form when in Suggested Predictions view
}
*/
// ----------  NEW  toggleView  ----------
function toggleView() {
    /* 1.  wipe whatever is currently shown under the toggle */
    const resultsDiv = document.getElementById('predictionResults');
    if (resultsDiv) resultsDiv.innerHTML = '';

    /* 2.  carry on with the original logic -------------------- */
    const viewToggle   = document.getElementById('viewToggle');
    const viewState    = document.getElementById('viewState');
    const defaultView  = document.getElementById('defaultPredictionsView');
    const suggestedView= document.getElementById('suggestedPredictionsView');
    const predictionForm = document.getElementById('predictionForm');

    const isDefault = viewToggle.checked;

    viewState.textContent = isDefault ? 'Default View' : 'Suggested Predictions';
    viewState.classList.toggle('enabled',  isDefault);
    viewState.classList.toggle('disabled', !isDefault);

    defaultView.style.display  = isDefault ? 'block' : 'none';
    suggestedView.style.display= isDefault ? 'none' : 'block';
    predictionForm.style.display='none';   // always hide form when view flips
}

/*
function updatePredictionList(predictions, workspaceId) {
    const predictionList = document.getElementById('predictionList');
    predictionList.innerHTML = '';
    predictions.forEach((prediction, index) => {
        const div = document.createElement('div');
        div.style.marginBottom = '12px';
        div.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <label class="switch">
                    <input type="checkbox" id="toggle-${index}" ${prediction.enabled ? 'checked' : ''} 
                           onchange="togglePrediction('${prediction.type}', ${index}, '${workspaceId}')">
                    <span class="slider"></span>
                </label>
                <span>${prediction.type.replace('_', ' ')}</span>
                <button class="test" onclick="openEditPredictionFormByIndex(${index})">Edit</button>
                <button class="test" onclick="deletePrediction('${prediction.type}', '${workspaceId}')">Delete</button>
                <button class="test" onclick="runPrediction('${prediction.type}')" ${!prediction.enabled ? 'disabled' : ''}>Run</button>
            </div>
        `;
        predictionList.appendChild(div);
    });
}
*/
function updateSuggestedPredictionList(predictions, workspaceId) {
    const suggestedPredictionList = document.getElementById('suggestedPredictionList');
    suggestedPredictionList.innerHTML = '';
    predictions.forEach((prediction, index) => {
        const displayName = (prediction.prediction_name || prediction.type || 'Unnamed Prediction').replace(/_/g, ' ');
        const justification = prediction.justification || 'No justification provided.';

        const div = document.createElement('div');
        div.style.marginBottom = '16px';
        div.innerHTML = `
            <div style="padding: 10px; border: 1px solid #ccc; border-radius: 8px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <strong>${displayName}</strong>
                    <div>
                        <!--<button class="test" onclick="addSuggestedPrediction(${index}, '${workspaceId}')">Add</button>-->
                        <button class="test" onclick="viewSuggestedPrediction(${index})">View Details</button>
                    </div>
                </div>
                <div style="margin-top: 8px; font-size: 0.95em; color: #555;">
                    <em>Why this suggestion?</em><br>
                    ${justification}
                </div>
            </div>
        `;
        suggestedPredictionList.appendChild(div);
    });
}

/*

function fetchSuggestedPredictions() {
    const workspaceId = document.getElementById('workspaceId').value;
    const query = document.getElementById('predictionQueryInput').value.trim();
    const process = document.getElementById('processSelect').value;
    const loader = document.getElementById('suggestionsLoader');

    if (!query) {
        showErrorMessage('Please enter a prediction query.');
        return;
    }

    loader.style.display = 'block'; // Show loading

    // Step 1: Get workspace name from ID
    fetch(`/get_workspace/${workspaceId}`)
        .then(response => response.json())
        .then(workspace => {
            if (!workspace || !workspace.name) {
                loader.style.display = 'none';
                showErrorMessage('Workspace name not found.');
                return;
            }

            const workspaceName = workspace.name;

            // Step 2: Use process to determine tables
            const tableList = processTableMap[process] || [];
            const tableNamesParam = encodeURIComponent(tableList.join(","));

            // Step 3: Call Flask API with proper params
            fetch(
            `/api/v0/get_prediction_suggestions?` +
            `workspace_id=${encodeURIComponent(workspaceId)}` +
            `&workspace_name=${encodeURIComponent(workspaceName)}` +
            `&table_name=${tableNamesParam}` +
            `&query=${encodeURIComponent(query)}`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            }
            )

                .then(response => response.json())
                .then(data => {
                    loader.style.display = 'none';
                    if (data.type === 'error') {
                        showErrorMessage(data.error);
                        return;
                    }
                    suggestedPredictions = data.suggestions || [];
                    updateSuggestedPredictionList(suggestedPredictions, workspaceName);
                })
                .catch(error => {
                    loader.style.display = 'none';
                    showErrorMessage('Error fetching suggested predictions: ' + error);
                });
        })
        .catch(error => {
            loader.style.display = 'none';
            showErrorMessage('Error fetching workspace details: ' + error);
        });
}

*/

//updated fetch suggested predictions
function fetchSuggestedPredictions() {
    const workspaceId = document.getElementById('workspaceId').value;
    const query = document.getElementById('predictionQueryInput').value.trim();
    const process = document.getElementById('processSelect').value;
    const loader = document.getElementById('suggestionsLoader');
    const listBox = document.getElementById('suggestedPredictionList');

    /*  NEW : wipe old list + old loader *************************/
    listBox.innerHTML = '';
    loader.style.display = 'block';

    /*  basic guard ********************************************/
    if (!query) {
        loader.style.display = 'none';
        showErrorMessage('Please enter a prediction query.');
        return;
    }

    /*  existing logic *****************************************/
    fetch(`/get_workspace/${workspaceId}`)
        .then(response => response.json())
        .then(workspace => {
            if (!workspace || !workspace.name) {
                loader.style.display = 'none';
                showErrorMessage('Workspace name not found.');
                return;
            }

            const workspaceName = workspace.name;
            const tableList = processTableMap[process] || [];
            const tableNamesParam = encodeURIComponent(tableList.join(","));

            return fetch(
                `/api/v0/get_prediction_suggestions?workspace_name=${encodeURIComponent(workspaceName)}` +
                `&table_name=${tableNamesParam}&query=${encodeURIComponent(query)}`,
                { method: 'GET', headers: { 'Content-Type': 'application/json' } }
            );
        })
        .then(response => response.json())
        .then(data => {
            loader.style.display = 'none';
            if (data.type === 'error') {
                showErrorMessage(data.error);
                return;
            }
            suggestedPredictions = data.suggestions || [];
            updateSuggestedPredictionList(suggestedPredictions, workspaceId);
        })
        .catch(error => {
            loader.style.display = 'none';
            showErrorMessage('Error fetching suggested predictions: ' + error);
        });
}




function addSuggestedPrediction(index, workspaceId) {
    if (index < 0 || index >= suggestedPredictions.length) {
        showErrorMessage('Invalid suggestion index.');
        return;
    }
    const prediction = suggestedPredictions[index];
    prediction.enabled = true;
    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, predictions: [prediction] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage('Suggested prediction added!');
            fetchPredictionConfigs(workspaceId);
            document.getElementById('viewToggle').checked = true;
            toggleView();
        }
    })
    .catch(error => showErrorMessage('Error adding suggested prediction: ' + error));
}

function viewSuggestedPrediction(index) {
    if (index < 0 || index >= suggestedPredictions.length) {
        showErrorMessage('Invalid suggestion index.');
        return;
    }
    const prediction = suggestedPredictions[index];
    openEditPredictionForm(prediction, true);
}

function deletePrediction(predictionType, workspaceId) {
    if (!confirm(`Are you sure you want to delete the prediction '${predictionType.replace('_', ' ')}'?`)) {
        return;
    }
    fetch('/delete_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, prediction_type: predictionType })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage('Prediction deleted!');
            fetchPredictionConfigs(workspaceId);
        }
    })
    .catch(error => showErrorMessage('Error deleting prediction: ' + error));
}

/*
function togglePrediction(predictionType, index, workspaceId) {
    if (index < 0 || index >= currentPredictions.length) {
        showErrorMessage('Invalid prediction index.');
        return;
    }
    const prediction = currentPredictions[index];
    if (!prediction || prediction.type !== predictionType) {
        showErrorMessage('Prediction not found.');
        return;
    }
    prediction.enabled = !prediction.enabled;
    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, predictions: [prediction] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage(`Prediction ${prediction.enabled ? 'enabled' : 'disabled'}!`);
            fetchPredictionConfigs(workspaceId);
        }
    })
    .catch(error => showErrorMessage('Error toggling prediction: ' + error));
}

*/

function openAddPredictionForm() {
    const form = document.getElementById('predictionForm');
    document.getElementById('formTitle').textContent = 'Add New Prediction';
    document.getElementById('predictionId').value = '';
    document.getElementById('predictionName').value = '';
    document.getElementById('sqlQuery').value = '';
    document.getElementById('algorithm').value = 'mean';
    document.getElementById('sqlQueryResult').textContent = '';
    updateParameterFields();
    form.style.display = 'block';
}

function openEditPredictionForm(prediction, isSuggestion = false) {
    const form = document.getElementById('predictionForm');
    if (!form) {
        showErrorMessage('Prediction form not found.');
        return;
    }
    const predictionIdField = document.getElementById('predictionId');
    const predictionNameField = document.getElementById('predictionName');
    const sqlQueryField = document.getElementById('sqlQuery');
    const algorithmField = document.getElementById('algorithm');
    const sqlQueryResultField = document.getElementById('sqlQueryResult');

    document.getElementById('formTitle').textContent = isSuggestion ? 'View Suggested Prediction' : 'Edit Prediction';
    predictionIdField.value = prediction.type || '';
    predictionNameField.value = (prediction.type || '').replace('_', ' ');
    sqlQueryField.value = prediction.sql_query || '';
    algorithmField.value = prediction.algorithm || 'mean';
    sqlQueryResultField.textContent = '';

    updateParameterFields();

    const params = prediction.parameters || {};
    try {
        if (prediction.algorithm === 'mean' || prediction.algorithm === 'standard_deviation') {
            const targetColumnField = document.getElementById('targetColumn');
            const inflationRateField = document.getElementById('inflationRate');
            if (targetColumnField) targetColumnField.value = params.target || '';
            if (inflationRateField) inflationRateField.value = params.inflation_rate || '';
        } else if (prediction.algorithm === 'linear_regression' || prediction.algorithm === 'logistic_regression') {
            const featuresField = document.getElementById('features');
            const targetField = document.getElementById('target');
            if (featuresField) featuresField.value = Array.isArray(params.features) ? params.features.join(', ') : '';
            if (targetField) targetField.value = params.target || '';
        } else if (prediction.algorithm === 'custom') {
            const customParamsField = document.getElementById('customParams');
            if (customParamsField) customParamsField.value = JSON.stringify(params, null, 2);
        }
    } catch (error) {
        showErrorMessage('Error populating prediction parameters: ' + error.message);
        return;
    }

    form.style.display = 'block';
    if (isSuggestion) {
        document.querySelector('#predictionForm button.save').textContent = 'Add Prediction';
    } else {
        document.querySelector('#predictionForm button.save').textContent = 'Save Prediction';
    }
}

function closePredictionForm() {
    document.getElementById('predictionForm').style.display = 'none';
}

function openSchemaExplorer() {
    const workspaceId = document.getElementById('workspaceId').value;
    document.getElementById('schemaExplorer').style.display = 'block';
    fetchTables(workspaceId);
}

function closeSchemaExplorer() {
    document.getElementById('schemaExplorer').style.display = 'none';
}

function updateParameterFields() {
    const algorithm = document.getElementById('algorithm').value;
    const parameterFields = document.getElementById('parameterFields');
    parameterFields.innerHTML = '';

    if (algorithm === 'mean' || algorithm === 'standard_deviation') {
        parameterFields.innerHTML = `
            <label for="targetColumn">Target Column:</label>
            <input type="text" id="targetColumn" placeholder="e.g., reorder_qty">
            <label for="inflationRate">Inflation Rate (%):</label>
            <input type="number" id="inflationRate" placeholder="e.g., 2.5" step="0.1">
        `;
    } else if (algorithm === 'linear_regression') {
        parameterFields.innerHTML = `
            <label for="features">Features (comma-separated):</label>
            <input type="text" id="features" placeholder="e.g., qty, price">
            <label for="target">Target Column:</label>
            <input type="text" id="target" placeholder="e.g., reorder_qty">
        `;
    } else if (algorithm === 'logistic_regression') {
        parameterFields.innerHTML = `
            <label for="features">Features (comma-separated):</label>
            <input type="text" id="features" placeholder="e.g., qty, delay_days">
            <label for="target">Target Column (binary):</label>
            <input type="text" id="target" placeholder="e.g., order_delayed">
        `;
    } else if (algorithm === 'custom') {
        parameterFields.innerHTML = `
            <label for="customParams">Custom Parameters (JSON):</label>
            <textarea id="customParams" rows="4" placeholder='{"param1": "value1", "param2": 42}'></textarea>
        `;
    }
}

function savePrediction() {
    const workspaceId = document.getElementById('workspaceId').value;
    const predictionId = document.getElementById('predictionId').value;
    const predictionName = document.getElementById('predictionName').value.trim();
    const sqlQuery = document.getElementById('sqlQuery').value;
    const algorithm = document.getElementById('algorithm').value;

    if (!predictionName || !sqlQuery) {
        showErrorMessage("Prediction name and SQL query are required.");
        return;
    }

    let parameters = {};
    if (algorithm === 'mean' || algorithm === 'standard_deviation') {
        parameters.target = document.getElementById('targetColumn')?.value || '';
        parameters.inflation_rate = parseFloat(document.getElementById('inflationRate')?.value) || null;
        if (!parameters.target) {
            showErrorMessage("Target column is required.");
            return;
        }
    } else if (algorithm === 'linear_regression' || algorithm === 'logistic_regression') {
        parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
        parameters.target = document.getElementById('target')?.value || '';
        if (!parameters.features.length || !parameters.target) {
            showErrorMessage("Features and target column are required.");
            return;
        }
    } else if (algorithm === 'custom') {
        try {
            parameters = JSON.parse(document.getElementById('customParams')?.value || '{}');
        } catch (e) {
            showErrorMessage("Invalid custom parameters JSON format.");
            return;
        }
    }

    const newPrediction = {
        enabled: true,
        type: predictionName.toLowerCase().replace(/\s+/g, '_'),
        sql_query: sqlQuery,
        algorithm,
        parameters
    };

    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, predictions: [newPrediction] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage("Prediction saved!");
            closePredictionForm();
            fetchPredictionConfigs(workspaceId);
        }
    })
    .catch(error => showErrorMessage('Error saving prediction: ' + error));
}
/*
function fetchPredictionConfigs(workspaceId) {
    fetch(`/api/v0/get_prediction_configs?workspace_id=${workspaceId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error") {
            showErrorMessage(data.error);
            return;
        }
        currentPredictions = data.predictions || [];
        updatePredictionList(currentPredictions, workspaceId);
    })
    .catch(error => showErrorMessage('Error fetching prediction configs: ' + error));
}
*/

/*
function runPrediction(predictionType) {
    if (!isVannaConnected) {
        showErrorMessage("Please initialize WI (LLM and DB) before running predictions.");
        return;
    }
    const workspaceId = document.getElementById('workspaceId').value;
    fetch(`/api/v0/run_prediction?workspace_id=${workspaceId}&prediction_type=${predictionType}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error" || data.type === "sql_error") {
            showErrorMessage(data.error);
        } else {
            displayPredictionResults(predictionType, data.df);
            showSuccessMessage(`${predictionType.replace('_', ' ')} prediction completed!`);
        }
    })
    .catch(error => showErrorMessage(`Error running ${predictionType}: ${error}`));
}
*/

//updated run prediction to show loader and results in a table
function runPrediction(predictionType) {
    if (!isVannaConnected) {
        showErrorMessage("Please initialize WI (LLM and DB) before running predictions.");
        return;
    }

    const workspaceId = document.getElementById('workspaceId').value;
    const loader = document.getElementById('predictionLoader');
    const resultsDiv = document.getElementById('predictionResults');

    // Clear previous results and show loader
    resultsDiv.innerHTML = `
        <div id="predictionLoader" style="text-align:center; margin:20px;">
            <span class="loader"></span> Running prediction...
        </div>
    `;
    resultsDiv.scrollIntoView({ behavior: 'smooth' });

    fetch(`/api/v0/run_prediction?workspace_id=${workspaceId}&prediction_type=${predictionType}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error" || data.type === "sql_error") {
            resultsDiv.innerHTML = `<p style="color:red;">${data.error}</p>`;
            showErrorMessage(data.error);
        } else {
            displayPredictionResults(predictionType, data.df); // Render fresh table
            showSuccessMessage(`${predictionType.replace('_', ' ')} prediction completed!`);
        }
    })
    .catch(error => {
        resultsDiv.innerHTML = `<p style="color:red;">Error running ${predictionType}: ${error}</p>`;
        showErrorMessage(`Error running ${predictionType}: ${error}`);
    });
}



/*
function displayPredictionResults(predictionType, results) {
    const resultsDiv = document.getElementById('predictionResults');
    let html = `<h5>${predictionType.replace('_', ' ').toUpperCase()} Results</h5><table class="dataTable">`;
    if (results.length > 0) {
        html += '<tr>';
        Object.keys(results[0]).forEach(key => {
            html += `<th>${key}</th>`;
        });
        html += '</tr>';
        results.forEach(row => {
            html += '<tr>';
            Object.values(row).forEach(value => {
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
    } else {
        html += '<tr><td>No data available</td></tr>';
    }
    html += '</table>';
    resultsDiv.innerHTML = html;
}
*/


//updated display prediction 

function displayPredictionResults(predictionType, results) {
    const resultsDiv = document.getElementById('predictionResults');
    resultsDiv.innerHTML = ''; // Clear old content

    if (!results || results.length === 0) {
        resultsDiv.innerHTML = `<h5>${predictionType.replace('_', ' ').toUpperCase()} Results</h5>
                                <p>No data available.</p>`;
        return;
    }

    let html = `<h5>${predictionType.replace('_', ' ').toUpperCase()} Results</h5>
                <table id="predictionDataTable" class="display dataTable" style="width:100%">
                <thead><tr>`;

    Object.keys(results[0]).forEach(key => {
        html += `<th>${key}</th>`;
    });
    html += `</tr></thead><tbody>`;

    results.forEach(row => {
        html += '<tr>';
        Object.values(row).forEach(value => {
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    resultsDiv.innerHTML = html;

    // Initialize DataTable
    setTimeout(() => {
        if ($.fn.DataTable.isDataTable('#predictionDataTable')) {
            $('#predictionDataTable').DataTable().destroy();
        }
        $('#predictionDataTable').DataTable({
            pageLength: 10,
            responsive: true,
            scrollX: true
        });
    }, 0);
}



function updatePredictionList(predictions, workspaceId) {
    const predictionList = document.getElementById('predictionList');
    predictionList.innerHTML = '';
    predictions.forEach((prediction, index) => {
        const div = document.createElement('div');
        div.style.marginBottom = '12px';
        div.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <label class="switch">
                    <input type="checkbox" id="toggle-${index}" ${prediction.enabled ? 'checked' : ''} 
                           onchange="togglePrediction('${prediction.type}', ${index}, '${workspaceId}')">
                    <span class="slider"></span>
                </label>
                <span>${prediction.type.replace('_', ' ')}</span>
                <button class="test" onclick="openEditPredictionFormByIndex(${index})">Edit</button>
                <button class="test" onclick="deletePrediction('${prediction.type}', '${workspaceId}')">Delete</button>
                <button class="test" onclick="runPrediction('${prediction.type}')" ${!prediction.enabled ? 'disabled' : ''}>Run</button>
            </div>
        `;
        predictionList.appendChild(div);
    });
}

/*

function togglePrediction(predictionType, index, workspaceId) {
    if (index < 0 || index >= currentPredictions.length) {
        showErrorMessage('Invalid prediction index.');
        return;
    }

    const prediction = currentPredictions[index];
    if (!prediction || prediction.type !== predictionType) {
        showErrorMessage('Prediction not found.');
        return;
    }

    prediction.enabled = !prediction.enabled;
    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, predictions: [prediction] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage(`Prediction ${prediction.enabled ? 'enabled' : 'disabled'}!`);
            fetchPredictionConfigs(workspaceId);
        }
    })
    .catch(error => showErrorMessage('Error toggling prediction: ' + error));
}
*/

// Retain other functions (openAddPredictionForm, openEditPredictionForm, etc.) as they are
function openAddPredictionForm() {
    const form = document.getElementById('predictionForm');
    document.getElementById('formTitle').textContent = 'Add New Prediction';
    document.getElementById('predictionId').value = '';
    document.getElementById('predictionName').value = '';
    document.getElementById('sqlQuery').value = '';
    document.getElementById('algorithm').value = 'mean';
    document.getElementById('sqlQueryResult').textContent = '';
    updateParameterFields();
    form.style.display = 'block';
}

function openEditPredictionForm(prediction) {
    const form = document.getElementById('predictionForm');
    if (!form) {
        showErrorMessage('Prediction form not found.');
        return;
    }

    const predictionIdField = document.getElementById('predictionId');
    const predictionNameField = document.getElementById('predictionName');
    const sqlQueryField = document.getElementById('sqlQuery');
    const algorithmField = document.getElementById('algorithm');
    const sqlQueryResultField = document.getElementById('sqlQueryResult');

    if (!predictionIdField || !predictionNameField || !sqlQueryField || !algorithmField || !sqlQueryResultField) {
        showErrorMessage('One or more form fields are missing.');
        return;
    }

    document.getElementById('formTitle').textContent = 'Edit Prediction';
    predictionIdField.value = prediction.type || '';
    predictionNameField.value = (prediction.type || '').replace('_', ' ');
    sqlQueryField.value = prediction.sql_query || '';
    algorithmField.value = prediction.algorithm || 'mean';
    sqlQueryResultField.textContent = '';

    updateParameterFields();

    const params = prediction.parameters || {};
    try {
        if (prediction.algorithm === 'mean' || prediction.algorithm === 'standard_deviation') {
            const targetColumnField = document.getElementById('targetColumn');
            const inflationRateField = document.getElementById('inflationRate');
            if (targetColumnField) targetColumnField.value = params.target || '';
            if (inflationRateField) inflationRateField.value = params.inflation_rate || '';
        } else if (prediction.algorithm === 'linear_regression' || prediction.algorithm === 'logistic_regression') {
            const featuresField = document.getElementById('features');
            const targetField = document.getElementById('target');
            if (featuresField) featuresField.value = Array.isArray(params.features) ? params.features.join(', ') : '';
            if (targetField) targetField.value = params.target || '';
        } else if (prediction.algorithm === 'custom') {
            const customParamsField = document.getElementById('customParams');
            if (customParamsField) customParamsField.value = JSON.stringify(params, null, 2);
        }
    } catch (error) {
        showErrorMessage('Error populating prediction parameters: ' + error.message);
        return;
    }

    form.style.display = 'block';
}

function closePredictionForm() {
    document.getElementById('predictionForm').style.display = 'none';
}

function openSchemaExplorer() {
    const workspaceId = document.getElementById('workspaceId').value;
    document.getElementById('schemaExplorer').style.display = 'block';
    fetchTables(workspaceId);
}

function closeSchemaExplorer() {
    document.getElementById('schemaExplorer').style.display = 'none';
}

function updateParameterFields() {
    const algorithm = document.getElementById('algorithm').value;
    const parameterFields = document.getElementById('parameterFields');
    parameterFields.innerHTML = '';

    if (algorithm === 'mean' || algorithm === 'standard_deviation') {
        parameterFields.innerHTML = `
            <label for="targetColumn">Target Column:</label>
            <input type="text" id="targetColumn" placeholder="e.g., reorder_qty">
            <label for="inflationRate">Inflation Rate (%):</label>
            <input type="number" id="inflationRate" placeholder="e.g., 2.5" step="0.1">
        `;
    } else if (algorithm === 'linear_regression') {
        parameterFields.innerHTML = `
            <label for="features">Features (comma-separated):</label>
            <input type="text" id="features" placeholder="e.g., qty, price">
            <label for="target">Target Column:</label>
            <input type="text" id="target" placeholder="e.g., reorder_qty">
        `;
    } else if (algorithm === 'logistic_regression') {
        parameterFields.innerHTML = `
            <label for="features">Features (comma-separated):</label>
            <input type="text" id="features" placeholder="e.g., qty, delay_days">
            <label for="target">Target Column (binary):</label>
            <input type="text" id="target" placeholder="e.g., order_delayed">
        `;
    } else if (algorithm === 'custom') {
        parameterFields.innerHTML = `
            <label for="customParams">Custom Parameters (JSON):</label>
            <textarea id="customParams" rows="4" placeholder='{"param1": "value1", "param2": 42}'></textarea>
        `;
    }
}

function savePrediction() {
    const workspaceId = document.getElementById('workspaceId').value;
    const predictionId = document.getElementById('predictionId').value;
    const predictionName = document.getElementById('predictionName').value.trim();
    const sqlQuery = document.getElementById('sqlQuery').value;
    const algorithm = document.getElementById('algorithm').value;

    if (!predictionName || !sqlQuery) {
        showErrorMessage("Prediction name and SQL query are required.");
        return;
    }

    let parameters = {};
    if (algorithm === 'mean' || algorithm === 'standard_deviation') {
        parameters.target = document.getElementById('targetColumn')?.value || '';
        parameters.inflation_rate = parseFloat(document.getElementById('inflationRate')?.value) || null;
        if (!parameters.target) {
            showErrorMessage("Target column is required.");
            return;
        }
    } else if (algorithm === 'linear_regression' || algorithm === 'logistic_regression') {
        parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
        parameters.target = document.getElementById('target')?.value || '';
        if (!parameters.features.length || !parameters.target) {
            showErrorMessage("Features and target column are required.");
            return;
        }
    } else if (algorithm === 'custom') {
        try {
            parameters = JSON.parse(document.getElementById('customParams')?.value || '{}');
        } catch (e) {
            showErrorMessage("Invalid custom parameters JSON format.");
            return;
        }
    }

    const newPrediction = {
        enabled: true,
        type: predictionName.toLowerCase().replace(/\s+/g, '_'),
        sql_query: sqlQuery,
        algorithm,
        parameters
    };

    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, predictions: [newPrediction] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage("Prediction saved!");
            closePredictionForm();
            fetchPredictionConfigs(workspaceId);
        }
    })
    .catch(error => showErrorMessage('Error saving prediction: ' + error));
}


/*
function fetchPredictionConfigs(workspaceId) {
    fetch(`/api/v0/get_prediction_configs?workspace_id=${workspaceId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error") {
            showErrorMessage(data.error);
            return;
        }
        currentPredictions = data.predictions || [];
        updatePredictionList(currentPredictions, workspaceId);
    })
    .catch(error => showErrorMessage('Error fetching prediction configs: ' + error));
}
*/
function openEditPredictionFormByIndex(index) {
    if (index < 0 || index >= currentPredictions.length) {
        showErrorMessage('Invalid prediction index.');
        return;
    }
    openEditPredictionForm(currentPredictions[index]);
}


/*
function runPrediction(predictionType) {
    if (!isVannaConnected) {
        showErrorMessage("Please initialize WI (LLM and DB) before running predictions.");
        return;
    }
    const workspaceId = document.getElementById('workspaceId').value;
    fetch(`/api/v0/run_prediction?workspace_id=${workspaceId}&prediction_type=${predictionType}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error" || data.type === "sql_error") {
            showErrorMessage(data.error);
        } else {
            displayPredictionResults(predictionType, data.df);
            showSuccessMessage(`${predictionType.replace('_', ' ')} prediction completed!`);
        }
    })
    .catch(error => showErrorMessage(`Error running ${predictionType}: ${error}`));
}*/

/*
function displayPredictionResults(predictionType, results) {
    const resultsDiv = document.getElementById('predictionResults');
    let html = `<h5>${predictionType.replace('_', ' ').toUpperCase()} Results</h5><table class="dataTable">`;
    if (results.length > 0) {
        html += '<tr>';
        Object.keys(results[0]).forEach(key => {
            html += `<th>${key}</th>`;
        });
        html += '</tr>';
        results.forEach(row => {
            html += '<tr>';
            Object.values(row).forEach(value => {
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
    } else {
        html += '<tr><td>No data available</td></tr>';
    }
    html += '</table>';
    resultsDiv.innerHTML = html;
}
*/  

/*
function togglePredictionsState(workspaceId) {
    const toggleButton = document.getElementById('togglePredictions');
    const predictionsState = document.getElementById('predictionsState');
    const predictionsContainer = document.getElementById('predictionsContainer');
    const predictionForm = document.getElementById('predictionForm');
    const addButton = document.querySelector('#defaultPredictionsView button.save');
    const isEnabled = toggleButton.checked;

    if (isEnabled && !isVannaConnected) {
        toggleButton.checked = false;
        initializeVanna(workspaceId);
        return;
    }

    predictionsState.textContent = isEnabled ? 'Enabled' : 'Disabled';
    predictionsState.classList.toggle('enabled', isEnabled);
    predictionsState.classList.toggle('disabled', !isEnabled);
    predictionsContainer.style.display = isEnabled ? 'block' : 'none';
    predictionForm.style.display = isEnabled && document.getElementById('viewToggle').checked ? 'none' : 'none'; // Hide form when disabled
    addButton.disabled = !isEnabled;
}
*/

function openAddPredictionForm() {
    const form = document.getElementById('predictionForm');
    document.getElementById('formTitle').textContent = 'Add New Prediction';
    document.getElementById('predictionId').value = '';
    document.getElementById('predictionName').value = '';
    document.getElementById('sqlQuery').value = '';
    document.getElementById('algorithm').value = 'mean';
    document.getElementById('sqlQueryResult').textContent = '';
    updateParameterFields();
    form.style.display = 'block';
}

function openEditPredictionForm(prediction) {
    const form = document.getElementById('predictionForm');
    if (!form) {
        showErrorMessage('Prediction form not found.');
        return;
    }

    const predictionIdField = document.getElementById('predictionId');
    const predictionNameField = document.getElementById('predictionName');
    const sqlQueryField = document.getElementById('sqlQuery');
    const algorithmField = document.getElementById('algorithm');
    const sqlQueryResultField = document.getElementById('sqlQueryResult');

    if (!predictionIdField || !predictionNameField || !sqlQueryField || !algorithmField || !sqlQueryResultField) {
        showErrorMessage('One or more form fields are missing.');
        return;
    }

    document.getElementById('formTitle').textContent = 'Edit Prediction';
    predictionIdField.value = prediction.type || '';
    predictionNameField.value = (prediction.type || '').replace('_', ' ');
    sqlQueryField.value = prediction.sql_query || '';
    algorithmField.value = prediction.algorithm || 'mean';
    sqlQueryResultField.textContent = '';

    updateParameterFields();

    const params = prediction.parameters || {};
    try {
        if (prediction.algorithm === 'mean' || prediction.algorithm === 'standard_deviation') {
            const targetColumnField = document.getElementById('targetColumn');
            const inflationRateField = document.getElementById('inflationRate');
            if (targetColumnField) targetColumnField.value = params.target || '';
            if (inflationRateField) inflationRateField.value = params.inflation_rate || '';
        } else if (prediction.algorithm === 'linear_regression' || prediction.algorithm === 'logistic_regression') {
            const featuresField = document.getElementById('features');
            const targetField = document.getElementById('target');
            if (featuresField) featuresField.value = Array.isArray(params.features) ? params.features.join(', ') : '';
            if (targetField) targetField.value = params.target || '';
        } else if (prediction.algorithm === 'custom') {
            const customParamsField = document.getElementById('customParams');
            if (customParamsField) customParamsField.value = JSON.stringify(params, null, 2);
        }
    } catch (error) {
        showErrorMessage('Error populating prediction parameters: ' + error.message);
        return;
    }

    form.style.display = 'block';
}

function closePredictionForm() {
    document.getElementById('predictionForm').style.display = 'none';
}

function openSchemaExplorer() {
    const workspaceId = document.getElementById('workspaceId').value;
    document.getElementById('schemaExplorer').style.display = 'block';
    fetchTables(workspaceId);
}

function closeSchemaExplorer() {
    document.getElementById('schemaExplorer').style.display = 'none';
}

function updateParameterFields() {
    const algorithm = document.getElementById('algorithm').value;
    const parameterFields = document.getElementById('parameterFields');
    parameterFields.innerHTML = '';

    if (algorithm === 'mean' || algorithm === 'standard_deviation') {
        parameterFields.innerHTML = `
            <label for="targetColumn">Target Column:</label>
            <input type="text" id="targetColumn" placeholder="e.g., reorder_qty">
            <label for="inflationRate">Inflation Rate (%):</label>
            <input type="number" id="inflationRate" placeholder="e.g., 2.5" step="0.1">
        `;
    } else if (algorithm === 'linear_regression') {
        parameterFields.innerHTML = `
            <label for="features">Features (comma-separated):</label>
            <input type="text" id="features" placeholder="e.g., qty, price">
            <label for="target">Target Column:</label>
            <input type="text" id="target" placeholder="e.g., reorder_qty">
        `;
    } else if (algorithm === 'logistic_regression') {
        parameterFields.innerHTML = `
            <label for="features">Features (comma-separated):</label>
            <input type="text" id="features" placeholder="e.g., qty, delay_days">
            <label for="target">Target Column (binary):</label>
            <input type="text" id="target" placeholder="e.g., order_delayed">
        `;
    } else if (algorithm === 'custom') {
        parameterFields.innerHTML = `
            <label for="customParams">Custom Parameters (JSON):</label>
            <textarea id="customParams" rows="4" placeholder='{"param1": "value1", "param2": 42}'></textarea>
        `;
    }
}

function savePrediction() {
    const workspaceId = document.getElementById('workspaceId').value;
    const predictionId = document.getElementById('predictionId').value;
    const predictionName = document.getElementById('predictionName').value.trim();
    const sqlQuery = document.getElementById('sqlQuery').value;
    const algorithm = document.getElementById('algorithm').value;

    if (!predictionName || !sqlQuery) {
        showErrorMessage("Prediction name and SQL query are required.");
        return;
    }

    let parameters = {};
    if (algorithm === 'mean' || algorithm === 'standard_deviation') {
        parameters.target = document.getElementById('targetColumn')?.value || '';
        parameters.inflation_rate = parseFloat(document.getElementById('inflationRate')?.value) || null;
        if (!parameters.target) {
            showErrorMessage("Target column is required.");
            return;
        }
    } else if (algorithm === 'linear_regression' || algorithm === 'logistic_regression') {
        parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
        parameters.target = document.getElementById('target')?.value || '';
        if (!parameters.features.length || !parameters.target) {
            showErrorMessage("Features and target column are required.");
            return;
        }
    } else if (algorithm === 'custom') {
        try {
            parameters = JSON.parse(document.getElementById('customParams')?.value || '{}');
        } catch (e) {
            showErrorMessage("Invalid custom parameters JSON format.");
            return;
        }
    }

    const newPrediction = {
        enabled: true,
        type: predictionName.toLowerCase().replace(/\s+/g, '_'),
        sql_query: sqlQuery,
        algorithm,
        parameters
    };

    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, predictions: [newPrediction] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage("Prediction saved!");
            closePredictionForm();
            fetchPredictionConfigs(workspaceId);
        }
    })
    .catch(error => showErrorMessage('Error saving prediction: ' + error));
}
/*
function fetchPredictionConfigs(workspaceId) {
    fetch(`/api/v0/get_prediction_configs?workspace_id=${workspaceId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error") {
            showErrorMessage(data.error);
            return;
        }
        currentPredictions = data.predictions || [];
        updatePredictionList(currentPredictions, workspaceId);
    })
    .catch(error => showErrorMessage('Error fetching prediction configs: ' + error));
}
*/

function updatePredictionList(predictions, workspaceId) {
    const predictionList = document.getElementById('predictionList');
    predictionList.innerHTML = '';
    predictions.forEach((prediction, index) => {
        const div = document.createElement('div');
        div.style.marginBottom = '12px';
        div.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <button id="toggle-${index}" class="${prediction.enabled ? 'enabled' : 'disabled'} connect-button" 
                        onclick="togglePrediction('${prediction.type}', ${index}, '${workspaceId}')">
                    ${prediction.enabled ? 'Disable' : 'Enable'}
                </button>
                <span>${prediction.type.replace('_', ' ')}</span>
                <button class="test" onclick="openEditPredictionFormByIndex(${index})">Edit</button>
                <button class="test" onclick="deletePrediction('${prediction.type}', '${workspaceId}')">Delete</button>
                <button class="test" onclick="runPrediction('${prediction.type}')" ${!prediction.enabled ? 'disabled' : ''}>Run</button>
            </div>
        `;
        predictionList.appendChild(div);
    });
}

function openEditPredictionFormByIndex(index) {
    if (index < 0 || index >= currentPredictions.length) {
        showErrorMessage('Invalid prediction index.');
        return;
    }
    openEditPredictionForm(currentPredictions[index]);
}


/*
function togglePrediction(predictionType, index, workspaceId) {
    if (index < 0 || index >= currentPredictions.length) {
        showErrorMessage('Invalid prediction index.');
        return;
    }

    const prediction = currentPredictions[index];
    if (!prediction || prediction.type !== predictionType) {
        showErrorMessage('Prediction not found.');
        return;
    }

    prediction.enabled = !prediction.enabled;
    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, predictions: [prediction] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage(`Prediction ${prediction.enabled ? 'enabled' : 'disabled'}!`);
            fetchPredictionConfigs(workspaceId);
        }
    })
    .catch(error => showErrorMessage('Error toggling prediction: ' + error));
} */

/*
function runPrediction(predictionType) {
    if (!isVannaConnected) {
        showErrorMessage("Please initialize WI (LLM and DB) before running predictions.");
        return;
    }
    const workspaceId = document.getElementById('workspaceId').value;
    fetch(`/api/v0/run_prediction?workspace_id=${workspaceId}&prediction_type=${predictionType}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error" || data.type === "sql_error") {
            showErrorMessage(data.error);
        } else {
            displayPredictionResults(predictionType, data.df);
            showSuccessMessage(`${predictionType.replace('_', ' ')} prediction completed!`);
        }
    })
    .catch(error => showErrorMessage(`Error running ${predictionType}: ${error}`));
}*/

/*
function displayPredictionResults(predictionType, results) {
    const resultsDiv = document.getElementById('predictionResults');
    let html = `<h5>${predictionType.replace('_', ' ').toUpperCase()} Results</h5><table class="dataTable">`;
    if (results.length > 0) {
        html += '<tr>';
        Object.keys(results[0]).forEach(key => {
            html += `<th>${key}</th>`;
        });
        html += '</tr>';
        results.forEach(row => {
            html += '<tr>';
            Object.values(row).forEach(value => {
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
    } else {
        html += '<tr><td>No data available</td></tr>';
    }
    html += '</table>';
    resultsDiv.innerHTML = html;
}
*/







        function savePredictions() {
            const workspaceId = document.getElementById('workspaceId').value;
            const predictionId = document.getElementById('predictionId').value;
            const predictionName = document.getElementById('predictionName').value.trim();
            const sqlQuery = document.getElementById('sqlQuery').value;
            const algorithm = document.getElementById('algorithm').value;

            if (!predictionName || !sqlQuery) {
                showErrorMessage("Prediction name and SQL query are required.");
                return;
            }

            let parameters = {};
            if (algorithm === 'mean' || algorithm === 'standard_deviation') {
                parameters.target = document.getElementById('targetColumn')?.value || '';
                parameters.inflation_rate = parseFloat(document.getElementById('inflationRate')?.value) || 0;
                if (!parameters.target || parameters.inflation_rate === null) {
                    showErrorMessage("Target column and inflation rate are required.");
                    return;
                }
            } else if (algorithm === 'linear_regression') {
                parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
                parameters.target = document.getElementById('target')?.value || '';
                if (!parameters.features.length || !parameters.target) {
                    showErrorMessage("Features and target column are required.");
                    return;
                }
            } else if (algorithm === 'logistic_regression') {
                parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
                parameters.target = document.getElementById('target')?.value || '';
                if (!parameters.features.length || !parameters.target) {
                    showErrorMessage("Features and target column are required.");
                    return;
                }
            } else if (algorithm === 'custom') {
                try {
                    parameters = JSON.parse(document.getElementById('customParams')?.value || '{}');
                } catch (e) {
                    showErrorMessage("Invalid custom parameters JSON format.");
                    return;
                }
            }

            console.log("Parameters being sent:", parameters); // Debug log

            const newPrediction = {
                enabled: true,
                type: predictionName.toLowerCase().replace(/\s+/g, '_'),
                sql_query: sqlQuery,
                algorithm,
                parameters
            };

            fetch('/save_prediction_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ workspace_id: workspaceId, predictions: [newPrediction] })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showErrorMessage(data.error);
                } else {
                    showSuccessMessage("Prediction saved!");
                    closePredictionForm();
                    fetchPredictionConfigs(workspaceId);
                }
            })
            .catch(error => showErrorMessage('Error saving prediction: ' + error));
        }






/*
        function runPrediction(predictionType) {

            const workspaceId = document.getElementById('workspaceId').value;

            if (!workspaceId) {

                showErrorMessage("Please select a workspace first.");

                return;

            }



            const endpointMap = {

                'inventory_demand': '/api/v0/inventorydemandforecasting',

                'order_fulfillment_time': '/api/v0/orderfulfillmenttimeprediction',

                'order_delay': '/api/v0/orderdelayprediction',

                'price_trend': '/api/v0/pricetrendprediciton'

            };

            const endpoint = endpointMap[predictionType];

            if (!endpoint) {

                showErrorMessage(`No endpoint defined for prediction type: ${predictionType}`);

                return;

            }



            fetch(`${endpoint}?workspace_id=${workspaceId}`, {

                method: 'GET',

                headers: { 'Content-Type': 'application/json' }

            })

            .then(response => response.json())

            .then(data => {

                if (data.type === "error" || data.type === "sql_error") {

                    showErrorMessage(data.error);

                } else {

                    displayPredictionResults(predictionType, data.df);

                    showSuccessMessage(`${predictionType.replace('_', ' ')} prediction completed!`);

                }

            })

            .catch(error => showErrorMessage(`Error running ${predictionType}: ${error}`));

        }

        

        function displayPredictionResults(predictionType, results) {

            const resultsDiv = document.getElementById('predictionResults');

            let html = `<h5>${predictionType.replace('_', ' ').toUpperCase()} Results</h5><table class="dataTable">`;

            if (results.length > 0) {

                html += '<tr>';

                Object.keys(results[0]).forEach(key => {

                    html += `<th>${key}</th>`;

                });

                html += '</tr>';

                results.forEach(row => {

                    html += '<tr>';

                    Object.values(row).forEach(value => {

                        html += `<td>${value}</td>`;

                    });

                    html += '</tr>';

                });

            } else {

                html += '<tr><td>No data available</td></tr>';

            }

            html += '</table>';

            resultsDiv.innerHTML = html; // Replace with new results

        } 
        */



        function loadWorkspaceConfig(id) {

            fetch(`/get_workspace/${id}`)

                .then(response => response.json())

                .then(workspace => {

                    if (workspace.llm_config) {

                        document.getElementById('model_type') && (document.getElementById('model_type').value = workspace.llm_config.model_type || '');

                        toggleModelSelection();

                        if (workspace.llm_config.model_type === 'ollama') {

                            document.getElementById('ollama_base_url') && (document.getElementById('ollama_base_url').value = workspace.llm_config.ollama_base_url || '');

                            document.getElementById('ollama_model') && (document.getElementById('ollama_model').value = workspace.llm_config.ollama_model || '');

                        } else if (workspace.llm_config.model_type === 'openai') {

                            document.getElementById('openai_model') && (document.getElementById('openai_model').value = workspace.llm_config.openai_model || '');

                            document.getElementById('api_key') && (document.getElementById('api_key').value = workspace.llm_config.api_key || '');

                        }

                    }

                    if (workspace.db_config) {

                        document.getElementById('serverName') && (document.getElementById('serverName').value = workspace.db_config.serverName || '');

                        document.getElementById('port') && (document.getElementById('port').value = workspace.db_config.port || '');

                        document.getElementById('databaseName') && (document.getElementById('databaseName').value = workspace.db_config.databaseName || '');

                        document.getElementById('username') && (document.getElementById('username').value = workspace.db_config.username || '');

                        document.getElementById('password') && (document.getElementById('password').value = workspace.db_config.password || '');

                    }

                    if (workspace.db_config_b) {

                        document.getElementById('serverNameB') && (document.getElementById('serverNameB').value = workspace.db_config_b.serverName || '');

                        document.getElementById('portB') && (document.getElementById('portB').value = workspace.db_config_b.port || '');

                        document.getElementById('databaseNameB') && (document.getElementById('databaseNameB').value = workspace.db_config_b.databaseName || '');

                        document.getElementById('usernameB') && (document.getElementById('usernameB').value = workspace.db_config_b.username || '');

                        document.getElementById('passwordB') && (document.getElementById('passwordB').value = workspace.db_config_b.password || '');

                        document.getElementById('dbAliasB') && (document.getElementById('dbAliasB').value = workspace.db_config_b.db_alias || '');

                    }

                });

        }

        function saveWorkspaceName() {
            const workspaceName = document.getElementById('workspaceName').value;
            if (!workspaceName) {
                showErrorMessage("Workspace name is required.");
                return;
            }
            fetch('/save_workspace', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: workspaceName })
            })
            .then(async response => {
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to save workspace');
                }
                showSuccessMessage(data.message || "Workspace created!");
                closeWorkspaceModal();
                fetchSavedWorkspaces();
            })
            .catch(error => showErrorMessage(error.message));
        }


        function toggleModelSelection() {
            const modelType = document.getElementById('model_type')?.value;
            if (!modelType) return;
            document.getElementById('ollamaBaseUrlDiv').style.display = modelType === 'ollama' ? 'block' : 'none';
            document.getElementById('ollamaModelsDiv').style.display = modelType === 'ollama' ? 'block' : 'none';
            document.getElementById('openaiModelsDiv').style.display = modelType === 'openai' ? 'block' : 'none';
            document.getElementById('apiKeyField').style.display = modelType === 'openai' ? 'block' : 'none';
            if (modelType === 'ollama') loadOllamaModels();
        }

        function toggleApiKeyField() {
            document.getElementById('apiKeyField').style.display = 'block';
        }

        function loadOllamaModels() {
            fetch('/get-ollama-models')
                .then(response => response.json())
                .then(data => {
                    const ollamaDropdown = document.getElementById('ollama_model');
                    ollamaDropdown.innerHTML = '';
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        ollamaDropdown.appendChild(option);
                    });
                });
        }

        function testLLMConnection() {
            const modelType = document.getElementById('model_type').value;
            const resultField = document.getElementById('test-llm-result');
            resultField.innerText = 'Testing connection...';
            resultField.style.color = 'blue';
            if (modelType === 'ollama') testOllamaConnection();
            else if (modelType === 'openai') testOpenAIConnection();
            else {
                resultField.innerText = 'Please select a model type.';
                resultField.style.color = 'red';
            }
        }

        function testOllamaConnection() {
            const url = document.getElementById('ollama_base_url').value;
            const resultField = document.getElementById('test-llm-result');
            fetch(url, { method: 'GET' })
                .then(response => {
                    resultField.innerText = response.ok ? '✅ Ollama server is running!' : '❌ Server not reachable.';
                    resultField.style.color = response.ok ? 'green' : 'red';
                })
                .catch(() => {
                    resultField.innerText = '❌ Error connecting to server.';
                    resultField.style.color = 'red';
                });
        }

        function testOpenAIConnection() {
            const apiKey = document.getElementById('api_key').value;
            const resultField = document.getElementById('test-llm-result');
            fetch('/validate-openai-api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey })
            })
            .then(response => response.json())
            .then(data => {
                resultField.innerText = data.success ? ' API key is valid!' : 'Invalid API key.';
                resultField.style.color = data.success ? 'green' : 'red';
            });
        }

        function saveLLMConfig() {
            const workspaceId = document.getElementById('workspaceId').value;
            const payload = {
                workspace_id: workspaceId,
                model_type: document.getElementById('model_type').value,
                ollama_base_url: document.getElementById('ollama_base_url')?.value || null,
                ollama_model: document.getElementById('ollama_model')?.value || null,
                openai_model: document.getElementById('openai_model')?.value || null,
                api_key: document.getElementById('api_key')?.value || null
            };
            fetch('/save-llm-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => showSuccessMessage(data.message || 'LLM Config saved!'))
            .catch(error => showErrorMessage('Error saving LLM config: ' + error));
        }

        function testConnection(suffix) {
            suffix = suffix || '';
            const payload = {
                serverName: document.getElementById('serverName' + suffix).value,
                port: document.getElementById('port' + suffix).value,
                databaseName: document.getElementById('databaseName' + suffix).value,
                username: document.getElementById('username' + suffix).value,
                password: document.getElementById('password' + suffix).value
            };
            const resultField = document.getElementById(suffix ? 'test-db-result-' + suffix : 'test-db-result');
            resultField.innerText = 'Testing connection...';
            resultField.style.color = 'blue';
            fetch('/test_connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                resultField.innerText = data.message || data.error;
                resultField.style.color = data.message ? 'green' : 'red';
            })
            .catch(error => {
                resultField.innerText = '? Error testing connection.';
                resultField.style.color = 'red';
            });
        }

        function saveDBConfig(slot) {
            slot = slot || 'a';
            const suffix = slot === 'b' ? 'B' : '';
            const workspaceId = document.getElementById('workspaceId').value;
            const payload = {
                workspace_id: workspaceId,
                slot: slot,
                serverName: document.getElementById('serverName' + suffix).value,
                port: document.getElementById('port' + suffix).value,
                databaseName: document.getElementById('databaseName' + suffix).value,
                username: document.getElementById('username' + suffix).value,
                password: document.getElementById('password' + suffix).value
            };
            if (slot === 'b') {
                const aliasField = document.getElementById('dbAliasB');
                if (aliasField) payload.dbAlias = aliasField.value;
            }
            fetch('/save_connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => showSuccessMessage(data.message || 'DB Config saved!'))
            .catch(error => showErrorMessage('Error saving DB config: ' + error));
        }

        let filesToUpload = [];

        function previewCSV(file) {
            if (!file || !file.name.endsWith('.csv')) {
                showErrorMessage('Please upload a valid CSV file.');
                return;
            }
            Papa.parse(file, {
                header: true, // Parse CSV with headers
                complete: (result) => {
                    const headers = result.meta.fields || [];
                    displayCSVGrid(result.data, headers.length, headers);
                },
                skipEmptyLines: true
            });
        }

        function displayCSVGrid(data, columnCount, headers) {
            const table = document.getElementById('dataTable');
            table.innerHTML = '';
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            headerRow.id = 'tableHeaderRow';
            headers.forEach(cell => {
                const th = document.createElement('th');
                th.textContent = cell;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);
            const tbody = document.createElement('tbody');
            tbody.id = 'tableBody';
            data.forEach(row => {
                const tr = document.createElement('tr');
                headers.forEach(header => {
                    const td = document.createElement('td');
                    td.textContent = row[header] || '';
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            document.getElementById('dataGrid').style.display = 'block';
            document.getElementById('trainButton').style.display = 'block';

            // Set training type based on column count
            const trainButton = document.getElementById('trainButton');
            if (columnCount === 1 && headers[0].toLowerCase() === 'documentation') {
                trainButton.onclick = () => startDocumentationTraining();
            } else {
                trainButton.onclick = () => startQuestionSqlTraining();
            }
        }


        function startDocumentationTraining() {
            const workspaceId = document.getElementById('workspaceId').value;
            if (!workspaceId) {
                showErrorMessage('Workspace ID is required to train.');
                return;
            }

            const tableBody = document.getElementById('tableBody');
            if (!tableBody) {
                showErrorMessage('Table body not found. Please upload a valid CSV file.');
                return;
            }

            let documentationContent = [];
            tableBody.querySelectorAll('tr').forEach(row => {
                const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
                if (cells.length > 0 && cells[0]) {
                    documentationContent.push(cells[0]); // Single column content
                }
            });

            if (documentationContent.length === 0) {
                showErrorMessage('No documentation content found in the CSV.');
                return;
            }

            fetch(`/get_workspace/${workspaceId}`)
                .then(response => response.json())
                .then(workspace => {
                    if (!workspace || !workspace.name) {
                        showErrorMessage('Workspace name not found.');
                        return;
                    }

                    fetch('/api/v0/train_documentation', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            workspace_id: workspaceId,
                            workspace_name: workspace.name,
                            documentation: documentationContent
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            showErrorMessage('Training failed: ' + data.error);
                        } else {
                            showSuccessMessage(data.message || 'Documentation training completed successfully!');
                            document.getElementById('dataGrid').style.display = 'none';
                            document.getElementById('trainButton').style.display = 'none';
                            loadTrainingData(workspaceId);
                        }
                    })
                    .catch(error => showErrorMessage('Training failed: ' + error));
                })
                .catch(error => showErrorMessage('Error fetching workspace: ' + error));
        }

        function startQuestionSqlTraining() {
            const workspaceId = document.getElementById('workspaceId').value;
            if (!workspaceId) {
                showErrorMessage('Workspace ID is required to train.');
                return;
            }

            const tableHeaderRow = document.getElementById('tableHeaderRow');
            if (!tableHeaderRow) {
                showErrorMessage('Table header row not found. Please upload a valid CSV file.');
                return;
            }

            const headers = Array.from(tableHeaderRow.children).map(th => th.textContent.trim());
            if (!headers.includes('question') || !headers.includes('sql')) {
                showErrorMessage('CSV must contain "question" and "sql" columns.');
                return;
            }

            const tableBody = document.getElementById('tableBody');
            if (!tableBody) {
                showErrorMessage('Table body not found. Please upload a valid CSV file.');
                return;
            }

            let trainingData = [];
            tableBody.querySelectorAll('tr').forEach(row => {
                const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
                const questionIndex = headers.indexOf('question');
                const sqlIndex = headers.indexOf('sql');
                const question = cells[questionIndex];
                const sql = cells[sqlIndex];
                if (question && sql) {
                    trainingData.push({ question, sql });
                }
            });

            if (trainingData.length === 0) {
                showErrorMessage('No valid training data found in the CSV.');
                return;
            }

            fetch('/api/v0/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ workspace_id: workspaceId, training_data: trainingData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showErrorMessage('Training failed: ' + data.error);
                } else {
                    showSuccessMessage(data.message || 'Training completed successfully!');
                    document.getElementById('dataGrid').style.display = 'none';
                    document.getElementById('trainButton').style.display = 'none';
                    loadTrainingData(workspaceId);
                }
            })
            .catch(error => showErrorMessage('Training failed: ' + error));
        }

        function saveTrainingData() {
            if (!filesToUpload.length) {
                showErrorMessage('No files uploaded!');
                return;
            }
            const workspaceId = document.getElementById('workspaceId').value;
            const formData = new FormData();
            formData.append('workspace_id', workspaceId);
            filesToUpload.forEach(file => formData.append('files', file));
            fetch('/save_training_data', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => showSuccessMessage(data.message || 'Training data saved!'))
            .catch(error => showErrorMessage('Error saving training data: ' + error));
        }

        function showSuccessMessage(message) {
            const successMessage = document.getElementById('successMessage');
            successMessage.innerText = message;
            successMessage.style.display = 'block';
            setTimeout(() => successMessage.style.display = 'none', 1000);
        }

        function showErrorMessage(message) {
            const errorMessage = document.getElementById('errorMessage');
            errorMessage.innerText = message;
            errorMessage.style.display = 'block';
            setTimeout(() => errorMessage.style.display = 'none', 1000);
        }

            function fetchSavedWorkspaces() {
                fetch('/get_workspaces')
                    .then(response => response.json())
                    .then(workspaces => {
                        const savedWorkspaces = document.getElementById('savedWorkspaces');
                        savedWorkspaces.innerHTML = '';
                        workspaces.forEach(workspace => {
                            const displayName = workspace.display_name || workspace.name;
                            const li = document.createElement('li');
                            li.innerHTML = `
                                <div class="workspace-item">
                                    <div class="workspace-header">
                                        <span><i class="fas fa-brain"></i>${displayName}</span>
                                        <button class="connect-button" onclick="connectVanna('${workspace.id}')">Connect</button>
                                    </div>
                                    <div class="sub-options" id="options-${workspace.id}">
                                        <div class="sub-section-label">Configure AI</div>
                                        <li onclick="showAIProviders('${workspace.id}')"><i class="fas fa-robot"></i>AI Providers</li>
                                        <li onclick="showAIFeatures('${workspace.id}')"><i class="fas fa-cogs"></i>AI Features & Options</li>
                                        <li onclick="showPredictions('${workspace.id}')"><i class="fas fa-chart-line"></i>Predictions</li>
                                        <li onclick="showAnomaly('${workspace.id}')"><i class="fas fa-exclamation-triangle"></i>Anomaly Detection</li>
                                        <li onclick="showTrainingModule('${workspace.id}')"><i class="fas fa-book"></i>Training Data</li>

                                        <div class="sub-section-label">Manage Agents</div>
                                        <li onclick="showAgents('${workspace.id}')"><i class="fas fa-envelope"></i>Query Agents</li>
                                        <li onclick="showResetDevicesAgent('${workspace.id}')"><i class="fas fa-sync-alt"></i>Reset Devices Agent</li>
                                        <li onclick="showUnpickAgent('${workspace.id}')"><i class="fas fa-undo-alt"></i>Unpick Agent</li>

                                        <div class="sub-section-label">Workspace Admin</div>
                                        <li onclick="showDBConfig('${workspace.id}')"><i class="fas fa-server"></i>DB Config</li>
                                        <li onclick="showTeamsConfig('${workspace.id}')"><i class="fab fa-microsoft"></i>Teams Configuration</li>
                                        <li onclick="deleteWorkspace('${workspace.id}')"><i class="fas fa-trash-alt"></i>Delete</li>
                                    </div>
                                </div>
                            `;
                            const header = li.querySelector('.workspace-header span');
                            header.addEventListener('click', () => toggleWorkspaceOptions(workspace.id));
                            savedWorkspaces.appendChild(li);
                        });
                    })
                    .catch(error => showErrorMessage('Error fetching workspaces: ' + error));
            }


            function deleteWorkspace(workspaceId) {
                if (!confirm('Are you sure you want to delete this workspace?')) return;
                fetch(`/delete_workspace/${workspaceId}`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw new Error(err.error || 'Failed to delete workspace'); });
                    }
                    return response.json();
                })
                .then(data => {
                    showSuccessMessage(data.message || 'Workspace deleted successfully!');
                    fetchSavedWorkspaces();
                })
                .catch(error => showErrorMessage('Error deleting workspace: ' + error));
            }

        function showTrainingModule(id) {
            const contentArea = document.getElementById('contentArea');
            contentArea.innerHTML = `
                <h4>Training Module</h4>
                <input type="hidden" id="workspaceId" value="${id}">
                <p>Upload a CSV file or manage training data for this workspace.</p>
                <div id="dropArea">
                    <p>Drag and drop CSV files here or click to upload</p>
                    <input type="file" id="fileInput" accept=".csv">
                </div>
                <button id="uploadButton" onclick="handleFileUpload()">Upload & Preview</button>
                <div id="dataGrid" style="display: none;">
                    <h3>Preview Data</h3>
                    <table id="dataTable"></table>
                   <button id="trainButton" onclick="startTraining()">Train</button>
                </div>
                <div class="btn-container">
                    <button class="btn-new" onclick="openNewTrainingModal()">New</button>
                    <button class="btn-edit" id="editBtn" disabled>Edit</button>
                    <button class="btn-delete" id="deleteBtn" disabled>Delete</button>
                    <button onclick="console.log('export button clicked')" id="exportBtn">Export Training Data</button>
                </div>
                <h5>Existing Training Data</h5>
                <table id="trainingDataTable" class="dataTable training-data-table">
                    <thead>
                        <tr><th>Question</th><th>Content</th></tr>
                    </thead>
                    <tbody></tbody>
                </table>
            `;
            contentArea.style.display = 'block';
            setupTrainingEvents();
            $(document).ready(function () {
                var table = $('#trainingDataTable').DataTable({
                    pageLength: 10,
                    lengthChange: false
                });

                $('#trainingDataTable tbody').on('click', 'tr', function () {
                    $(this).toggleClass('selected').siblings().removeClass('selected');
                    updateButtons();
                });

                function updateButtons() {
                    var selected = $('#trainingDataTable tr.selected').length;
                    $('#editBtn, #deleteBtn').prop('disabled', selected === 0);
                }

                function showToast(message, type = "success") {
                    Toastify({
                        text: message,
                        duration: 1000,
                        gravity: "top",
                        position: "center",
                        style: { background: type === "success" ? "green" : "red" },
                        stopOnFocus: true
                    }).showToast();
                }

                $("#editBtn").click(function () {
                    var selectedRow = $('#trainingDataTable tr.selected');
                    if (selectedRow.length === 0) return;

                    var id = selectedRow.attr("id").replace("row-", "");
                    var question = selectedRow.find('td:eq(0)').text();
                    var content = selectedRow.find('td:eq(1)').text();
                    var isDocumentation = id.endsWith("-doc");

                    $("#editQuestion").val(question);
                    $("#editSQL").val(content);
                    // Disable question field for documentation entries
                    $("#editQuestion").prop('disabled', isDocumentation);
                    $("#editModalTraining").fadeIn();

                    $("#updateBtn").off("click").on("click", function () {
                        var updatedQuestion = $("#editQuestion").val();
                        var updatedContent = $("#editSQL").val();
                        var workspaceId = document.getElementById('workspaceId').value;

                        fetch(`/get_workspace/${workspaceId}`)
                            .then(response => {
                                if (!response.ok) throw new Error(`Failed to fetch workspace: ${response.status}`);
                                return response.json();
                            })
                            .then(workspace => {
                                if (!workspace.name) throw new Error("Workspace name not found");
                                fetch(`/api/v0/edit_training_data?workspace_name=${workspace.name}`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        id,
                                        question: isDocumentation ? null : updatedQuestion,
                                        content: updatedContent,
                                        is_documentation: isDocumentation
                                    })
                                })
                                .then(response => {
                                    if (!response.ok) throw new Error(`Edit request failed: ${response.status}`);
                                    return response.json();
                                })
                                .then(data => {
                                    if (data.success) {
                                        showToast("Training data updated successfully!", "success");
                                        var table = $('#trainingDataTable').DataTable();
                                        table.cell(selectedRow, 0).data(isDocumentation ? '' : updatedQuestion);
                                        table.cell(selectedRow, 1).data(updatedContent);
                                        selectedRow.attr("id", `row-${data.new_id}`);
                                        $("#editModalTraining").fadeOut();
                                    } else {
                                        showToast("Error: " + (data.error || "Unknown error"), "error");
                                    }
                                })
                                .catch(error => showToast("Error updating entry: " + error.message, "error"));
                            })
                            .catch(error => showToast("Error fetching workspace: " + error.message, "error"));
                    });
                });

                $("#deleteBtn").click(function () {
                    var selectedRow = $('#trainingDataTable tr.selected');
                    if (selectedRow.length === 0) {
                        showToast("Please select a row to delete", "error");
                        return;
                    }

                    var id = selectedRow.attr("id").replace("row-", "");
                    var workspaceId = document.getElementById('workspaceId').value;

                    fetch(`/get_workspace/${workspaceId}`)
                        .then(response => {
                            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                            return response.json();
                        })
                        .then(workspace => {
                            var workspaceName = workspace.name;
                            if (!workspaceName) throw new Error("Workspace name not found in response");

                            return fetch('/api/v0/remove_training_data_module', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ id, workspace_name: workspaceName })
                            });
                        })
                        .then(response => {
                            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                            return response.json();
                        })
                        .then(data => {
                            if (data.success) {
                                table.row(selectedRow).remove().draw();
                                updateButtons();
                                showToast("Training data deleted successfully!", "success");
                                loadTrainingData(workspaceId);
                            } else {
                                showToast("Error: " + (data.error || "Unknown error"), "error");
                            }
                        })
                        .catch(error => {
                            showToast("Error deleting entry: " + error.message, "error");
                        });
                });



                $("#exportBtn").click(function () {
                    const workspaceId = document.getElementById('workspaceId')?.value || 'unknown';
                    console.log(`Export Training Data button clicked for workspace ID: ${workspaceId}`);
                    if (!document.getElementById('exportBtn')) {
                        console.warn("Export button not found in DOM");
                    }

                    // Send log to server
                    fetch('/api/v0/log_event', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            event: 'Export Training Data button clicked',
                            workspaceId: workspaceId,
                            timestamp: new Date().toISOString()
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            console.error('Failed to send log to server:', response.status);
                        }
                    })
                    .catch(error => {
                        console.error('Error sending log to server:', error.message);
                    });

                    exportTrainingData();
                });





                $(".close-btn").click(function () {
                    $("#editModalTraining, #newModalTraining").fadeOut();
                });

                $(window).click(function (event) {
                    if ($(event.target).is(".modal_Training")) {
                        $(".modal_Training").fadeOut();
                    }
                });

                loadTrainingData(id);
            });
        }


        function loadTrainingData(workspaceId) {
            const table = $('#trainingDataTable').DataTable();
            
            // Show loader
            const loaderHTML = `<div id="trainingLoader" style="text-align:center; margin: 16px;">
                                    <span class="loader"></span> Loading training data...
                                </div>`;
            $('#trainingDataTable_wrapper').before(loaderHTML); // Insert above the table

            fetch(`/get_workspace/${workspaceId}`)
                .then(response => response.json())
                .then(workspace => {
                    if (!workspace || !workspace.name) {
                        showErrorMessage('Workspace name not found.');
                        $('#trainingLoader').remove(); // Remove loader
                        return;
                    }

                    fetch(`/api/v0/get_training_data_module?workspace_name=${workspace.name}`)
                        .then(response => response.json())
                        .then(data => {
                            table.clear();
                            if (data.df && Array.isArray(data.df)) {
                                data.df.forEach(entry => {
                                    let displayContent = '';
                                    if (entry.training_data_type === 'sql' || entry.training_data_type === 'documentation') {
                                        displayContent = entry.content || '';
                                    }

                                    const newRow = table.row.add([
                                        entry.question || '',
                                        displayContent
                                    ]).draw().node();
                                    $(newRow).attr("id", `row-${entry.id}`);
                                });
                            } else {
                                showErrorMessage(data.error || "No training data found");
                            }
                            $('#trainingLoader').remove(); // Remove loader after data loads
                        })
                        .catch(error => {
                            showErrorMessage('Error fetching training data: ' + error);
                            $('#trainingLoader').remove();
                        });
                })
                .catch(error => {
                    showErrorMessage('Error fetching workspace details: ' + error);
                    $('#trainingLoader').remove();
                });
        }




        function exportTrainingData() {
            const workspaceId = document.getElementById('workspaceId').value;
            
            fetch(`/get_workspace/${workspaceId}`)
                .then(response => response.json())
                .then(workspace => {
                    if (!workspace || !workspace.name) {
                        showErrorMessage('Workspace name not found.');
                        return;
                    }

                    fetch(`/api/v0/get_training_data_module?workspace_name=${workspace.name}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.df && Array.isArray(data.df)) {
                                // Convert data to CSV
                                const headers = ['Question', 'Content'];
                                const csvRows = [headers.join(',')];
                                
                                data.df.forEach(entry => {
                                    const question = (entry.question || '').replace(/"/g, '""');
                                    const content = (entry.content || '').replace(/"/g, '""');
                                    csvRows.push(`"${question}","${content}"`);
                                });
                                // older export with buggy utf
                                // const csvContent = csvRows.join('\n');
                                // const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                                // Add UTF-8 BOM
                                console.log(data.df[1978]);
                                const csvContent = csvRows.join('\n');
                                const BOM = '\uFEFF';
                                const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });

                                const url = URL.createObjectURL(blob);
                                const link = document.createElement('a');
                                link.setAttribute('href', url);
                                link.setAttribute('download', `training_data_${workspaceId}.csv`);
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                URL.revokeObjectURL(url);
                                showSuccessMessage('Training data exported successfully!');
                            } else {
                                showErrorMessage(data.error || 'No training data found to export.');
                            }
                        })
                        .catch(error => {
                            showErrorMessage('Error fetching training data: ' + error);
                        });
                })
                .catch(error => {
                    showErrorMessage('Error fetching workspace details: ' + error);
                });
        }






        function openEditTrainingModal(id, question, sql) {
            const modal = document.getElementById('editModalTraining');
            modal.style.display = 'block';
            document.getElementById('editQuestion').value = question;
            document.getElementById('editSQL').value = sql;
            const updateBtn = document.getElementById('updateBtn');
            updateBtn.onclick = () => updateTrainingData(id);
            modal.querySelector('.close-btn').onclick = () => modal.style.display = 'none';
        }

        function openNewTrainingModal() {
            const modal = document.getElementById('newModalTraining');
            modal.style.display = 'block';
            document.getElementById('newQuestion').value = '';
            document.getElementById('newSQL').value = '';
            const saveBtn = document.getElementById('saveBtn');
            saveBtn.onclick = () => addTrainingData();
            modal.querySelector('.close-btn').onclick = () => modal.style.display = 'none';
        }

        function updateTrainingData(trainingId) {
            const workspaceId = document.getElementById('workspaceId').value;
            const newQuestion = document.getElementById('editQuestion').value;
            const newContent = document.getElementById('editSQL').value;
            const isDocumentation = trainingId.endsWith("-doc");

            fetch(`/get_workspace/${String(workspaceId)}`)  // Convert workspaceId to string
                .then(response => response.json())
                .then(workspace => {
                    fetch(`/api/v0/edit_training_data?workspace_name=${workspace.name}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: trainingId,
                            question: isDocumentation ? null : newQuestion,
                            content: newContent,
                            is_documentation: isDocumentation
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showSuccessMessage('Training data updated!');
                            document.getElementById('editModalTraining').style.display = 'none';
                            loadTrainingData(workspaceId);
                        } else {
                            showErrorMessage(data.error || 'Failed to update training data.');
                        }
                    })
                    .catch(error => showErrorMessage('Error updating training data: ' + error));
                })
                .catch(error => showErrorMessage('Error fetching workspace: ' + error));
        }

        function addTrainingData() {
            const workspaceId = document.getElementById('workspaceId').value.trim();
            
            if (!workspaceId) {
                showErrorMessage("Workspace ID is required!");
                console.error("Workspace ID is missing");
                return;
            }

            if (isDocumentationMode) {
                const documentation = document.getElementById('newDocumentation').value.trim();
                
                if (!documentation) {
                    showErrorMessage("Documentation field is required!");
                    console.error("Documentation field is empty");
                    return;
                }

                // Fetch workspace name from the backend
                console.log("Fetching workspace name for ID:", workspaceId);
                fetch(`/get_workspace/${workspaceId}`)
                    .then(response => response.json())
                    .then(workspace => {
                        if (!workspace || !workspace.name) {
                            showErrorMessage("Workspace name not found!");
                            console.error("Workspace name not found in response:", workspace);
                            return;
                        }
                        const workspaceName = workspace.name;
                        console.log("Workspace name fetched:", workspaceName);

                        fetch('/api/v0/train_documentation', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                workspace_id: workspaceId,
                                workspace_name: workspaceName,
                                documentation: [documentation]
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                console.error('Documentation training error:', data.error);
                                showErrorMessage(data.error);
                            } else {
                                console.log('Documentation training success:', data.message);
                                showSuccessMessage(data.message || 'Documentation training added!');
                                document.getElementById('newModalTraining').style.display = 'none';
                                loadTrainingData(workspaceId);
                            }
                        })
                        .catch(error => {
                            console.error('Error adding documentation training:', error);
                            showErrorMessage('Error adding documentation training: ' + error.message);
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching workspace:', error);
                        showErrorMessage('Error fetching workspace: ' + error.message);
                    });
            } else {
                const question = document.getElementById('newQuestion').value.trim();
                const sql = document.getElementById('newSQL').value.trim();

                if (!question || !sql) {
                    showErrorMessage("Both fields are required!");
                    console.error("Question or SQL field is empty");
                    return;
                }

                fetch('/api/v0/train', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        workspace_id: workspaceId,
                        training_data: [{ question, sql }]
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Training data error:', data.error);
                        showErrorMessage(data.error);
                    } else {
                        console.log('Question-SQL training success:', data.message);
                        showSuccessMessage(data.message || 'Training data added!');
                        document.getElementById('newModalTraining').style.display = 'none';
                        loadTrainingData(workspaceId);
                    }
                })
                .catch(error => {
                    console.error('Error adding training data:', error);
                    showErrorMessage('Error adding training data: ' + error.message);
                });
            }
        }

        // Add event listeners
        document.getElementById('docTrainingBtn').addEventListener('click', toggleModalMode);
        document.getElementById('saveBtn').addEventListener('click', addTrainingData);

        // Ensure modal is in default state when opened or closed
        document.getElementById('newModalTraining').addEventListener('click', function(e) {
            if (e.target.className === 'close-btn') {
                this.style.display = 'none';
                isDocumentationMode = false;
                toggleModalMode(); // Reset to default Question-SQL mode
            }
        });




        function setupTrainingEvents() {
            const dropArea = document.getElementById('dropArea');
            const fileInput = document.getElementById('fileInput');
            dropArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropArea.classList.add('dragover');
            });
            dropArea.addEventListener('dragleave', () => dropArea.classList.remove('dragover'));
            dropArea.addEventListener('drop', (e) => {
                e.preventDefault();
                dropArea.classList.remove('dragover');
                filesToUpload = Array.from(e.dataTransfer.files);
                previewCSV(filesToUpload[0]);
            });
            fileInput.addEventListener('change', () => {
                filesToUpload = Array.from(fileInput.files);
                previewCSV(filesToUpload[0]);
            });
        }

        function handleFileUpload() {
            if (!filesToUpload.length) {
                showErrorMessage('No files selected!');
                return;
            }
            const workspaceId = document.getElementById('workspaceId').value;
            const formData = new FormData();
            filesToUpload.forEach(file => formData.append('files', file));
            formData.append('workspace_id', workspaceId);
            fetch('/upload_training_data', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                showSuccessMessage(data.message || 'File uploaded!');
                previewCSV(filesToUpload[0]);
            })
            .catch(error => showErrorMessage('Error uploading file: ' + error));
        }

        function startTraining() {
                const workspaceId = document.getElementById('workspaceId').value;

                const trainButton = document.getElementById('trainButton');
                trainButton.disabled = true;
                trainButton.innerHTML = `<span class="loader"></span> Training...`;

                fetch(`/api/v0/train_model?workspace_id=${workspaceId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(response => response.json())
                .then(data => {
                    trainButton.disabled = false;
                    trainButton.innerHTML = `Train`;

                    if (data.success) {
                        showSuccessMessage("Training completed!");
                        loadTrainingData(workspaceId);
                    } else {
                        showErrorMessage(data.error || "Training failed");
                    }
                })
                .catch(error => {
                    trainButton.disabled = false;
                    trainButton.innerHTML = `Train`;
                    showErrorMessage("Error training model: " + error);
                });
            }



        
        





        function openAddPredictionForm() {
            const form = document.getElementById('predictionForm');
            document.getElementById('formTitle').textContent = 'Add New Prediction';
            document.getElementById('predictionId').value = '';
            document.getElementById('predictionName').value = '';
            document.getElementById('sqlQuery').value = '';
            document.getElementById('algorithm').value = 'mean';
            document.getElementById('sqlQueryResult').textContent = '';
            updateParameterFields();
            form.style.display = 'block';
        }

        function openEditPredictionForm(prediction) {
            const form = document.getElementById('predictionForm');
            if (!form) {
                showErrorMessage('Prediction form not found.');
                return;
            }

            // Set basic fields
            const predictionIdField = document.getElementById('predictionId');
            const predictionNameField = document.getElementById('predictionName');
            const sqlQueryField = document.getElementById('sqlQuery');
            const algorithmField = document.getElementById('algorithm');
            const sqlQueryResultField = document.getElementById('sqlQueryResult');

            if (!predictionIdField || !predictionNameField || !sqlQueryField || !algorithmField || !sqlQueryResultField) {
                showErrorMessage('One or more form fields are missing.');
                return;
            }

            document.getElementById('formTitle').textContent = 'Edit Prediction';
            predictionIdField.value = prediction.type || '';
            predictionNameField.value = (prediction.type || '').replace('_', ' ');
            sqlQueryField.value = prediction.sql_query || '';
            algorithmField.value = prediction.algorithm || 'mean';
            sqlQueryResultField.textContent = '';

            // Update parameter fields first
            updateParameterFields();

            // Populate algorithm-specific fields after updating parameter fields
            const params = prediction.parameters || {};
            try {
                if (prediction.algorithm === 'mean' || prediction.algorithm === 'standard_deviation') {
                    const targetColumnField = document.getElementById('targetColumn');
                    const inflationRateField = document.getElementById('inflationRate');
                    if (targetColumnField) targetColumnField.value = params.target || '';
                    if (inflationRateField) inflationRateField.value = params.inflation_rate || '';
                } else if (prediction.algorithm === 'linear_regression' || prediction.algorithm === 'logistic_regression') {
                    const featuresField = document.getElementById('features');
                    const targetField = document.getElementById('target');
                    if (featuresField) featuresField.value = Array.isArray(params.features) ? params.features.join(', ') : '';
                    if (targetField) targetField.value = params.target || '';
                } else if (prediction.algorithm === 'custom') {
                    const customParamsField = document.getElementById('customParams');
                    if (customParamsField) customParamsField.value = JSON.stringify(params, null, 2);
                }
            } catch (error) {
                showErrorMessage('Error populating prediction parameters: ' + error.message);
                return;
            }

            form.style.display = 'block';
        }

        function closePredictionForm() {
            document.getElementById('predictionForm').style.display = 'none';
        }

        function openSchemaExplorer() {
            const workspaceId = document.getElementById('workspaceId').value;
            document.getElementById('schemaExplorer').style.display = 'block';
            fetchTables(workspaceId);
        }

        function closeSchemaExplorer() {
            document.getElementById('schemaExplorer').style.display = 'none';
        }

        function updateParameterFields() {
            const algorithm = document.getElementById('algorithm').value;
            const parameterFields = document.getElementById('parameterFields');
            parameterFields.innerHTML = '';

            if (algorithm === 'mean' || algorithm === 'standard_deviation') {
                parameterFields.innerHTML = `
                    <label for="targetColumn">Target Column:</label>
                    <input type="text" id="targetColumn" placeholder="e.g., reorder_qty">
                    <label for="inflationRate">Inflation Rate (%):</label>
                    <input type="number" id="inflationRate" placeholder="e.g., 2.5" step="0.1">
                `;
            } else if (algorithm === 'linear_regression') {
                parameterFields.innerHTML = `
                    <label for="features">Features (comma-separated):</label>
                    <input type="text" id="features" placeholder="e.g., qty, price">
                    <label for="target">Target Column:</label>
                    <input type="text" id="target" placeholder="e.g., reorder_qty">

                `;
            } else if (algorithm === 'logistic_regression') {
                parameterFields.innerHTML = `
                    <label for="features">Features (comma-separated):</label>
                    <input type="text" id="features" placeholder="e.g., qty, delay_days">
                    <label for="target">Target Column (binary):</label>
                    <input type="text" id="target" placeholder="e.g., order_delayed">
                `;
            } else if (algorithm === 'custom') {
                parameterFields.innerHTML = `
                    <label for="customParams">Custom Parameters (JSON):</label>
                    <textarea id="customParams" rows="4" placeholder='{"param1": "value1", "param2": 42}'></textarea>
                `;
            }
        }

        function savePrediction() {
            const workspaceId = document.getElementById('workspaceId').value;
            const predictionId = document.getElementById('predictionId').value;
            const predictionName = document.getElementById('predictionName').value.trim();
            const sqlQuery = document.getElementById('sqlQuery').value;
            const algorithm = document.getElementById('algorithm').value;

            if (!predictionName || !sqlQuery) {
                showErrorMessage("Prediction name and SQL query are required.");
                return;
            }

            let parameters = {};
            if (algorithm === 'mean' || algorithm === 'standard_deviation') {
                parameters.target = document.getElementById('targetColumn')?.value || '';
                parameters.inflation_rate = parseFloat(document.getElementById('inflationRate')?.value) || null;
                if (!parameters.target) {
                    showErrorMessage("Target column is required.");
                    return;
                }
            } else if (algorithm === 'linear_regression') {
                parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
                parameters.target = document.getElementById('target')?.value || '';
                parameters.inflation_rate = parseFloat(document.getElementById('inflationRate')?.value) || null;
                if (!parameters.features.length || !parameters.target) {
                    showErrorMessage("Features and target column are required.");
                    return;
                }
            } else if (algorithm === 'logistic_regression') {
                parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
                parameters.target = document.getElementById('target')?.value || '';
                if (!parameters.features.length || !parameters.target) {
                    showErrorMessage("Features and target column are required.");
                    return;
                }
            } else if (algorithm === 'custom') {
                try {
                    parameters = JSON.parse(document.getElementById('customParams')?.value || '{}');
                } catch (e) {
                    showErrorMessage("Invalid custom parameters JSON format.");
                    return;
                }
            }

            const newPrediction = {
                enabled: true,
                type: predictionName.toLowerCase().replace(/\s+/g, '_'),
                sql_query: sqlQuery,
                algorithm,
                parameters
            };

            fetch('/save_prediction_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ workspace_id: workspaceId, predictions: [newPrediction] })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showErrorMessage(data.error);
                } else {
                    showSuccessMessage("Prediction saved!");
                    closePredictionForm();
                    fetchPredictionConfigs(workspaceId);
                }
            })
            .catch(error => showErrorMessage('Error saving prediction: ' + error));
        }
/*
        function fetchPredictionConfigs(workspaceId) {
            fetch(`/api/v0/get_prediction_configs?workspace_id=${workspaceId}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.type === "error") {
                    showErrorMessage(data.error);
                    return;
                }
    
                currentPredictions = data.predictions || [];
                updatePredictionList(currentPredictions, workspaceId);
    
                // Delay this until DOM is guaranteed to be ready
                setTimeout(() => {
                    const toggleBtn = document.getElementById('togglePredictions');
                    const stateLabel = document.getElementById('predictionsState');
                    const container = document.getElementById('predictionsContainer');
                    const addBtn = document.querySelector('#predictionsContainer button.save');
    
                    if (!toggleBtn || !stateLabel || !container || !addBtn) {
                        console.warn("Prediction toggle elements not found yet — skipping toggle UI update");
                        return;
                    }
    
                    const hasEnabled = currentPredictions.some(p => p.enabled);
    
                    if (hasEnabled) {
                        toggleBtn.classList.remove('disabled');
                        toggleBtn.classList.add('enabled');
                        toggleBtn.textContent = 'Disable Predictions';
                        stateLabel.textContent = 'Enabled';
                        stateLabel.classList.remove('disabled');
                        stateLabel.classList.add('enabled');
                        container.style.display = 'block';
                        addBtn.disabled = false;
                    } else {
                        toggleBtn.classList.remove('enabled');
                        toggleBtn.classList.add('disabled');
                        toggleBtn.textContent = 'Enable Predictions';
                        stateLabel.textContent = 'Disabled';
                        stateLabel.classList.remove('enabled');
                        stateLabel.classList.add('disabled');
                        container.style.display = 'none';
                        addBtn.disabled = true;
                    }
                }, 0); // Use 0 or a small delay to wait for DOM paint
            })
            .catch(error => showErrorMessage('Error fetching prediction configs: ' + error));
        }
        */

        function updatePredictionList(predictions, workspaceId) {
            const predictionList = document.getElementById('predictionList');
            predictionList.innerHTML = '';
            predictions.forEach((prediction, index) => {
                const div = document.createElement('div');
                div.style.marginBottom = '12px';
                div.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <button id="toggle-${index}" class="${prediction.enabled ? 'enabled' : 'disabled'} connect-button" 
                                onclick="togglePrediction('${prediction.type}', ${index}, '${workspaceId}')">
                            ${prediction.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <span>${prediction.type.replace('_', ' ')}</span>
                        <button class="test" onclick="openEditPredictionFormByIndex(${index})">Edit</button>
                        <button class="test" onclick="deletePrediction('${prediction.type}', '${workspaceId}')">Delete</button>
                        <button class="test" onclick="runPrediction('${prediction.type}')" ${!prediction.enabled ? 'disabled' : ''}>Run</button>
                    </div>
                `;
                predictionList.appendChild(div);
            });
        }

        function openEditPredictionFormByIndex(index) {
            if (index < 0 || index >= currentPredictions.length) {
                showErrorMessage('Invalid prediction index.');
                return;
            }
            openEditPredictionForm(currentPredictions[index]);
        }
/*
    function togglePrediction(predictionType, index, workspaceId) {
        if (index < 0 || index >= currentPredictions.length) {
            showErrorMessage('Invalid prediction index.');
            return;
        }

        const prediction = currentPredictions[index];
        if (!prediction || prediction.type !== predictionType) {
            showErrorMessage('Prediction not found.');
            return;
        }

        prediction.enabled = !prediction.enabled;
        fetch('/save_prediction_config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace_id: workspaceId, predictions: [prediction] })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showErrorMessage(data.error);
            } else {
                showSuccessMessage(`Prediction ${prediction.enabled ? 'enabled' : 'disabled'}!`);
                fetchPredictionConfigs(workspaceId); // Refresh the list
            }
        })
        .catch(error => showErrorMessage('Error toggling prediction: ' + error));
    }
    */

    //updated toggle individual prediction to toggle all predictions
    // Toggle an individual prediction ON/OFF
function togglePrediction(predictionType, index, workspaceId) {
    if (index < 0 || index >= currentPredictions.length) {
        showErrorMessage('Invalid prediction index.');
        return;
    }

    const prediction = currentPredictions[index];
    if (!prediction || prediction.type !== predictionType) {
        showErrorMessage('Prediction not found.');
        return;
    }

    // Flip enabled state
    prediction.enabled = !prediction.enabled;

    // Save back to server
    fetch('/save_prediction_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            workspace_id: workspaceId,
            predictions: [prediction]
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage(`Prediction ${prediction.enabled ? 'enabled' : 'disabled'}!`);
            fetchPredictionConfigs(workspaceId); // refresh list
        }
    })
    .catch(err => showErrorMessage('Error toggling prediction: ' + err));
}


     /*   function runPrediction(predictionType) {
            if (!isVannaConnected) {
                showErrorMessage("Please initialize WI (LLM and DB) before running predictions.");
                return;
            }
            const workspaceId = document.getElementById('workspaceId').value;
            fetch(`/api/v0/run_prediction?workspace_id=${workspaceId}&prediction_type=${predictionType}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.type === "error" || data.type === "sql_error") {
                    showErrorMessage(data.error);
                } else {
                    displayPredictionResults(predictionType, data.df);
                    showSuccessMessage(`${predictionType.replace('_', ' ')} prediction completed!`);
                }
            })
            .catch(error => showErrorMessage(`Error running ${predictionType}: ${error}`));
        } */

        /*
        function displayPredictionResults(predictionType, results) {
            const resultsDiv = document.getElementById('predictionResults');
            let html = `<h5>${predictionType.replace('_', ' ').toUpperCase()} Results</h5><table class="dataTable">`;
            if (results.length > 0) {
                html += '<tr>';
                Object.keys(results[0]).forEach(key => {
                    html += `<th>${key}</th>`;
                });
                html += '</tr>';
                results.forEach(row => {
                    html += '<tr>';
                    Object.values(row).forEach(value => {
                        html += `<td>${value}</td>`;
                    });
                    html += '</tr>';
                });
            } else {
                html += '<tr><td>No data available</td></tr>';
            }
            html += '</table>';
            resultsDiv.innerHTML = html;
        }
*/
               function loadWorkspaceConfig(id) {
            fetch(`/get_workspace/${id}`)
                .then(response => response.json())
                .then(workspace => {
                    if (workspace.llm_config) {
                        document.getElementById('model_type') && (document.getElementById('model_type').value = workspace.llm_config.model_type || '');
                        toggleModelSelection();
                        if (workspace.llm_config.model_type === 'ollama') {
                            document.getElementById('ollama_base_url') && (document.getElementById('ollama_base_url').value = workspace.llm_config.ollama_base_url || '');
                            document.getElementById('ollama_model') && (document.getElementById('ollama_model').value = workspace.llm_config.model_name || '');
                        } else if (workspace.llm_config.model_type === 'openai') {
                            document.getElementById('openai_model') && (document.getElementById('openai_model').value = workspace.llm_config.model_name || '');
                            document.getElementById('api_key') && (document.getElementById('api_key').value = workspace.llm_config.api_key || '');
                        }
                    }
                    if (workspace.db_config) {
                        document.getElementById('serverName') && (document.getElementById('serverName').value = workspace.db_config.serverName || '');
                        document.getElementById('port') && (document.getElementById('port').value = workspace.db_config.port || '');
                        document.getElementById('databaseName') && (document.getElementById('databaseName').value = workspace.db_config.databaseName || '');
                        document.getElementById('username') && (document.getElementById('username').value = workspace.db_config.username || '');
                        document.getElementById('password') && (document.getElementById('password').value = workspace.db_config.password || '');
                    }
                    if (workspace.db_config_b) {
                        document.getElementById('serverNameB') && (document.getElementById('serverNameB').value = workspace.db_config_b.serverName || '');
                        document.getElementById('portB') && (document.getElementById('portB').value = workspace.db_config_b.port || '');
                        document.getElementById('databaseNameB') && (document.getElementById('databaseNameB').value = workspace.db_config_b.databaseName || '');
                        document.getElementById('usernameB') && (document.getElementById('usernameB').value = workspace.db_config_b.username || '');
                        document.getElementById('passwordB') && (document.getElementById('passwordB').value = workspace.db_config_b.password || '');
                        document.getElementById('dbAliasB') && (document.getElementById('dbAliasB').value = workspace.db_config_b.db_alias || '');
                    }
                    // Populate Teams Configuration (if available)
                    if (workspace.teams_config) {
                        document.getElementById('teamsWebhook') && (document.getElementById('teamsWebhook').value = workspace.teams_config.webhookUrl || '');  // Fix
                        document.getElementById('callbackUrl') && (document.getElementById('callbackUrl').value = workspace.teams_config.callbackUrl || '');  // Fix
                        document.getElementById('enableTeamsToggle') && (document.getElementById('enableTeamsToggle').checked = !!workspace.teams_config.enabled);
                    }
                })
                .catch(error => showErrorMessage('Error loading workspace config: ' + error));
        }

        function showSuccessMessage(message) {
            const successDiv = document.getElementById('successMessage');
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            setTimeout(() => successDiv.style.display = 'none', 3000);
        }

        function showErrorMessage(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => errorDiv.style.display = 'none', 5000);
        }

        // Initialize the page
        fetchSavedWorkspaces();


        function generateCallbackUrl() {
            const workspaceId = document.getElementById('workspaceId').value;
            fetch('/generate_callback_url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ workspace_id: workspaceId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.callback_url) {
                    document.getElementById('callbackUrl').value = data.callback_url;
                    showSuccessMessage('Callback URL generated successfully!');
                } else {
                    showErrorMessage(data.error || 'Failed to generate callback URL.');
                }
            })
            .catch(error => showErrorMessage('Error generating callback URL: ' + error));
        }

       
       function showTeamsConfig(id) {
            const contentArea = document.getElementById('contentArea');
            contentArea.innerHTML = `
                <h4>Teams Configuration</h4>
                <input type="hidden" id="workspaceId" value="${id}">
                <p>Configure Microsoft Teams integration for this workspace.</p>

                <label class="switch">
                    <input type="checkbox" id="enableTeamsToggle">
                    <span class="slider round"></span>
                </label>
                <span style="margin-left: 10px;">Enable Teams Connector</span>

                <button class="save" onclick="saveTeamsConfig()">Save Configuration</button>
                <p id="teams-test-result"></p>
            `;
            contentArea.style.display = 'block';

            // Load the configuration immediately
            loadTeamsConfig();
        }

        function saveTeamsConfig() {
            const workspaceId = document.getElementById('workspaceId').value.trim();
            const isEnabled = document.getElementById('enableTeamsToggle').checked;

            if (!workspaceId) {
                showErrorMessage('Workspace ID is required.');
                return;
            }

            const payload = {
                workspace_id: workspaceId,
                teams_config: {
                    enabled: isEnabled
                }
            };

            fetch('/save_teams_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showErrorMessage(data.error);
                } else {
                    showSuccessMessage('Teams configuration saved successfully!');
                }
            })
            .catch(error => showErrorMessage('Error saving Teams config: ' + error.message));
        }




       function loadTeamsConfig() {
            const workspaceInput = document.getElementById('workspaceId');
            
            if (!workspaceInput) {
                console.error("Element with ID 'workspaceId' not found.");
                return;
            }

            const workspaceId = workspaceInput.value.trim();
            
            if (!workspaceId) {
                console.warn("Workspace ID is empty.");
                return;
            }

            fetch('/get_teams_config?workspace_id=' + encodeURIComponent(workspaceId))
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        showErrorMessage(data.error || "Failed to load Teams config.");
                        return;
                    }

                    const config = data.teams_config || {};
                    document.getElementById('enableTeamsToggle').checked = !!config.enabled;
                })
                .catch(error => showErrorMessage('Error loading Teams config: ' + error.message));
        }



        function toggleTeamsConfig() {
            const isEnabled = document.getElementById('enableTeamsToggle').checked;
            const webhookField = document.getElementById('teamsWebhook');
 
            if (isEnabled) {
                webhookField.removeAttribute("disabled");
            } else {
                webhookField.setAttribute("disabled", "true");
            }
        }

        function showGlobalLoader() {
                document.getElementById('globalLoader').style.display = 'block';
            }
            function hideGlobalLoader() {
                document.getElementById('globalLoader').style.display = 'none';
            }

            

let currentAnomalies = [];
let suggestedAnomalies = [];


/*  instant UI flip for the master anomaly toggle  */
function flipMasterAnomalyUI(){
    const toggle   = document.getElementById('masterAnomalyToggle');
    const label    = document.getElementById('masterAnomalyState');
    const isOn     = toggle.checked;

    label.textContent = isOn ? 'Enabled' : 'Disabled';
    label.classList.toggle('enabled',  isOn);
    label.classList.toggle('disabled', !isOn);
}

//updated 

function showAnomaly(workspaceId) {
    const contentArea = document.getElementById('contentArea');
    contentArea.innerHTML = `
        <h4>Anomaly Detection Configuration</h4>
        <input type="hidden" id="workspaceId" value="${workspaceId}">
        <p>Configure and run anomaly detection for this workspace.</p>

        <!-- Master Toggle + Save -->

        <div style="margin-bottom:16px;display:flex;align-items:center;gap:10px">
        <label class="switch">
            <input type="checkbox"
                id="masterAnomalyToggle"
                onchange="flipMasterAnomalyUI()">   <!-- NEW -->
            <span class="slider"></span>
        </label>
        <span id="masterAnomalyState" class="disabled">Disabled</span>
        <button class="save" onclick="saveMasterAnomalyToggle('${workspaceId}')">Save</button>
        </div>

        <!-- Enable/Disable Anomalies Toggle -->
        <div style="margin-bottom: 16px;">
            <p>Initialize Saved Anomalies</p>
            <label class="switch">
                <input type="checkbox" id="toggleAnomalies" onchange="toggleAnomaliesState('${workspaceId}')">
                <span class="slider"></span>
            </label>
            <span id="anomaliesState" class="disabled">Disabled</span>
        </div>

        <div id="anomaliesContainer" style="display: none;">
            <div style="margin-bottom: 16px;">
                <p>Switch Between Default and Suggested Anomalies</p>
                <label class="switch">
                    <input type="checkbox" id="viewToggle" onchange="toggleAnomalyView()" checked>
                    <span class="slider"></span>
                </label>
                <span id="viewState" class="enabled">Default View</span>
            </div>
            <div id="defaultAnomaliesView">
                <h5>Saved Anomaly Configurations</h5>
                <div id="anomalyList"></div>
                <button class="save" onclick="openAddAnomalyForm()" disabled>Add New Anomaly</button>
            </div>
            <div id="suggestedAnomaliesView" style="display: none;">
                <h5>Suggested Anomaly Configurations</h5>
                <label for="anomalyProcessSelect">Select Process:</label>
                <select id="anomalyProcessSelect">
                    <option value="" disabled selected>Select a process</option>
                    <option value="receiving_putaway">Receiving & Putaway</option>
                    <option value="planned_move">Planned Move</option>
                    <option value="inventory_movement">Inventory Movement</option>
                    <option value="inventory_adjustment">Inventory Adjustment & Cycle Counts</option>
                    <option value="waving">Waving</option>
                    <option value="order_processing">Order Picking, Packing, Staging, Loading & Shipping</option>
                </select>
                <label for="anomalyQueryInput">Anomaly Query:</label>
                <input type="text" id="anomalyQueryInput" placeholder="e.g., Detect abnormal cycle count activity">
                <button class="test" onclick="fetchSuggestedAnomalies('${workspaceId}')">Get Suggestions</button>
                <div id="suggestedAnomalyList"></div>
                <div id="suggestionsLoader" style="display:none; margin-top:10px;">
                    <span class="loader"></span> Loading suggestions...
                </div>
            </div>
        </div>
        <div id="anomalyForm" style="display: none; margin-top: 20px;">
            <h5 id="formTitle">Add New Anomaly</h5>
            <input type="hidden" id="anomalyId">
            <label for="anomalyName">Anomaly Name:</label>
            <input type="text" id="anomalyName" placeholder="e.g., Unusual Inventory Levels">
            <label for="sqlQuery">SQL Query:</label>
            <textarea id="sqlQuery" rows="4" placeholder="Enter SQL query to fetch data"></textarea>
            <button class="test" onclick="openSchemaExplorer()">Edit SQL with Schema</button>
            <button class="test" onclick="testSqlQuery('sqlQuery')">Test SQL Query</button>
            <button class="test" onclick="previewSqlQuery()">Preview Data</button>
            <p id="sqlQueryResult"></p>
            <label for="algorithm">Algorithm:</label>
            <select id="algorithm" onchange="updateAnomalyParameterFields()">
                <option value="z_score">Z-Score</option>
                <option value="isolation_forest">Isolation Forest</option>
                <option value="dbscan">DBSCAN</option>
                <option value="custom">Custom</option>
            </select>
            <div id="parameterFields" style="margin-top: 12px;"></div>
            <button class="save" onclick="saveAnomaly()">Save Anomaly</button>
            <button class="test" onclick="closeAnomalyForm()">Cancel</button>
        </div>
        <div id="schemaExplorer" style="display: none; margin-top: 20px;">
            <h5>Database Schema Explorer</h5>
            <label for="tableList">Select Table:</label>
            <select id="tableList" onchange="fetchColumns()"></select>
            <label for="columnList">Columns:</label>
            <select id="columnList" multiple style="width: 100%; height: 100px;"></select>
            <button class="test" onclick="insertColumnIntoQuery()">Insert Column into SQL Query</button>
            <button class="test" onclick="closeSchemaExplorer()">Close Explorer</button>
        </div>
        <div id="anomalyResults" style="margin-top: 20px;"></div>
    `;
    contentArea.style.display = 'block';

    // Initialize toggle states
    if (isVannaConnected) {
        updateAnomalyToggleUI(true);
    }

    // Default view is enabled by default
    const viewToggle = document.getElementById('viewToggle');
    const viewState = document.getElementById('viewState');
    viewToggle.checked = true;
    viewState.textContent = 'Default View';
    viewState.classList.add('enabled');
    viewState.classList.remove('disabled');

    // Fetch anomaly configurations and tables
    fetchAnomalyConfigs(workspaceId);
    fetchTables(workspaceId);
}

//toggle for saved anomaly each anomaly
function toggleAnomaly(anomalyType, index, workspaceId) {
    if (index < 0 || index >= currentAnomalies.length) {
        showErrorMessage('Invalid anomaly index.');
        return;
    }
    const anomaly = currentAnomalies[index];
    if (!anomaly || anomaly.type !== anomalyType) {
        showErrorMessage('Anomaly not found.');
        return;
    }
    anomaly.enabled = !anomaly.enabled;
    fetch('/save_anomaly_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, anomalies: [anomaly] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage(`Anomaly ${anomaly.enabled ? 'enabled' : 'disabled'}!`);
            fetchAnomalyConfigs(workspaceId);
        }
    })
    .catch(error => showErrorMessage('Error toggling anomaly: ' + error));
}



function toggleAnomaliesState(workspaceId) {
    const toggleButton = document.getElementById('toggleAnomalies');
    if (!toggleButton) return;

    toggleButton.disabled = true; // Disable toggle during processing
    const isEnabled = toggleButton.checked;

    if (isEnabled) {
        // Initialize Vanna when enabling
        fetch(`/get_workspace/${workspaceId}`)
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error! Status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                return fetch('/initialize-vanna', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        workspace_id: workspaceId,
                        llm_details: data.llm_config,
                        db_details: data.db_config
                    })
                });
            })
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error! Status: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data.success) {
                    isVannaConnected = true;
                    showSuccessMessage(data.message || 'WI initialized successfully!');
                    updateAnomalyToggleUI(true);
                } else {
                    throw new Error(data.error || 'Failed to initialize WI.');
                }
            })
            .catch(err => {
                isVannaConnected = false;
                showErrorMessage(`Error initializing WI: ${err.message}`);
                updateAnomalyToggleUI(false);
                toggleButton.checked = false; // Revert toggle on error
            })
            .finally(() => {
                toggleButton.disabled = false; // Re-enable toggle
            });
    } else {
        // Disable Vanna
        isVannaConnected = false;
        updateAnomalyToggleUI(false);
        showSuccessMessage('Anomaly detection disabled.');
        toggleButton.disabled = false;
    }
}



function updateAnomalyToggleUI(isEnabled) {
    const toggleButton = document.getElementById('toggleAnomalies');
    const anomaliesState = document.getElementById('anomaliesState');
    const anomaliesContainer = document.getElementById('anomaliesContainer');
    const addButton = document.querySelector('#defaultAnomaliesView button.save');

    if (!toggleButton || !anomaliesState || !anomaliesContainer || !addButton) return;

    toggleButton.checked = isEnabled;
    anomaliesState.textContent = isEnabled ? 'Enabled' : 'Disabled';
    anomaliesState.classList.toggle('enabled', isEnabled);
    anomaliesState.classList.toggle('disabled', !isEnabled);
    anomaliesContainer.style.display = isEnabled ? 'block' : 'none';
    addButton.disabled = !isEnabled;
}







//updated toggle anomaly state

/*
function toggleAnomalyView() {
    const viewToggle = document.getElementById('viewToggle');
    const viewState = document.getElementById('viewState');
    const defaultView = document.getElementById('defaultAnomaliesView');
    const suggestedView = document.getElementById('suggestedAnomaliesView');
    const anomalyForm = document.getElementById('anomalyForm');
    const isDefaultView = viewToggle.checked;

    viewState.textContent = isDefaultView ? 'Default View' : 'Suggested Anomalies';
    viewState.classList.toggle('enabled', isDefaultView);
    viewState.classList.toggle('disabled', !isDefaultView);
    defaultView.style.display = isDefaultView ? 'block' : 'none';
    suggestedView.style.display = isDefaultView ? 'none' : 'block';
    anomalyForm.style.display = isDefaultView ? 'none' : 'none';
}
*/

function toggleAnomalyView() {
    /* 1.  wipe whatever is currently shown under the toggle */
    const resultsDiv = document.getElementById('anomalyResults');
    if (resultsDiv) resultsDiv.innerHTML = '';

    /* 2.  carry on with the original logic -------------------- */
    const viewToggle    = document.getElementById('viewToggle');
    const viewState     = document.getElementById('viewState');
    const defaultView   = document.getElementById('defaultAnomaliesView');
    const suggestedView = document.getElementById('suggestedAnomaliesView');
    const anomalyForm   = document.getElementById('anomalyForm');

    const isDefault = viewToggle.checked;

    viewState.textContent = isDefault ? 'Default View' : 'Suggested Anomalies';
    viewState.classList.toggle('enabled',  isDefault);
    viewState.classList.toggle('disabled', !isDefault);

    defaultView.style.display   = isDefault ? 'block' : 'none';
    suggestedView.style.display = isDefault ? 'none' : 'block';
    anomalyForm.style.display   = 'none';   // always hide form when view flips
}

function openAddAnomalyForm() {
    const form = document.getElementById('anomalyForm');
    document.getElementById('formTitle').textContent = 'Add New Anomaly';
    document.getElementById('anomalyId').value = '';
    document.getElementById('anomalyName').value = '';
    document.getElementById('sqlQuery').value = '';
    document.getElementById('algorithm').value = 'z_score';
    document.getElementById('sqlQueryResult').textContent = '';
    updateAnomalyParameterFields();
    form.style.display = 'block';
}


/*
function fetchSuggestedAnomalies(workspaceId) {
    const process = document.getElementById('anomalyProcessSelect').value;
    const loader = document.getElementById('suggestionsLoader');
    const query = document.getElementById('anomalyQueryInput').value.trim();

    if (!process) {
        showErrorMessage('Please select a process.');
        return;
    }

    loader.style.display = 'block';

    // Step 1: Get workspace name from ID
    fetch(`/get_workspace/${workspaceId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(workspace => {
            if (!workspace || !workspace.name) {
                loader.style.display = 'none';
                showErrorMessage('Workspace name not found.');
                return;
            }

            const workspaceName = workspace.name;

            // Step 2: Use process to determine tables
            const tableList = processTableMap[process] || [];
            if (tableList.length === 0) {
                loader.style.display = 'none';
                showErrorMessage('No tables mapped for selected process.');
                return;
            }
            const tableNamesParam = encodeURIComponent(tableList.join(","));

            // Step 3: Call API to get anomaly suggestions
            fetch(`/api/v0/get_anomaly_suggestions?workspace_name=${encodeURIComponent(workspaceName)}&table_name=${tableNamesParam}&query=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
                .then(response => {
                    loader.style.display = 'none';
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    let suggestions = [];
                    if (data.type === 'error') {
                        showErrorMessage(data.error);
                        return;
                    } else if (data.suggestions && Array.isArray(data.suggestions)) {
                        suggestions = data.suggestions;
                    } else if (Array.isArray(data)) {
                        suggestions = data;
                    } else {
                        showErrorMessage('Unexpected response format from anomaly suggestions API.');
                        return;
                    }

                    if (suggestions.length === 0) {
                        showErrorMessage('No anomaly suggestions found.');
                        return;
                    }

                    suggestedAnomalies = suggestions;

                    const viewToggle = document.getElementById('viewToggle');
                    if (viewToggle && viewToggle.checked) {
                        viewToggle.checked = false;
                        toggleAnomalyView();
                    }

                    updateSuggestedAnomalyList(suggestedAnomalies, workspaceName);
                })
                .catch(error => {
                    loader.style.display = 'none';
                    showErrorMessage('Error fetching suggested anomalies: ' + error.message);
                });
        })
        .catch(error => {
            loader.style.display = 'none';
            showErrorMessage('Error fetching workspace details: ' + error.message);
        });
}
*/

//updated fetch suggested anomalies
function fetchSuggestedAnomalies(workspaceId) {
    const process   = document.getElementById('anomalyProcessSelect').value;
    const loader    = document.getElementById('suggestionsLoader');
    const query     = document.getElementById('anomalyQueryInput').value.trim();
    const listBox   = document.getElementById('suggestedAnomalyList');

    /*  NEW : wipe old list + old loader *************************/
    listBox.innerHTML = '';
    loader.style.display = 'block';

    /*  basic guard ********************************************/
    if (!process) {
        loader.style.display = 'none';
        showErrorMessage('Please select a process.');
        return;
    }

    /*  existing logic *****************************************/
    fetch(`/get_workspace/${workspaceId}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json();
        })
        .then(workspace => {
            if (!workspace || !workspace.name) {
                loader.style.display = 'none';
                showErrorMessage('Workspace name not found.');
                return;
            }

            const workspaceName = workspace.name;
            const tableList = processTableMap[process] || [];
            if (tableList.length === 0) {
                loader.style.display = 'none';
                showErrorMessage('No tables mapped for selected process.');
                return;
            }
            const tableNamesParam = encodeURIComponent(tableList.join(','));

            return fetch(
            `/api/v0/get_anomaly_suggestions?` +
            `workspace_id=${encodeURIComponent(workspaceId)}` +
            `&workspace_name=${encodeURIComponent(workspaceName)}` +
            `&table_name=${tableNamesParam}` +
            `&query=${encodeURIComponent(query)}`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            }
            );

        })
        .then(response => response.json())
        .then(data => {
            loader.style.display = 'none';

            let suggestions = [];
            if (data.type === 'error') {
                showErrorMessage(data.error);
                return;
            } else if (data.suggestions && Array.isArray(data.suggestions)) {
                suggestions = data.suggestions;
            } else if (Array.isArray(data)) {
                suggestions = data;
            } else {
                showErrorMessage('Unexpected response format from anomaly suggestions API.');
                return;
            }

            if (suggestions.length === 0) {
                showErrorMessage('No anomaly suggestions found.');
                return;
            }

            suggestedAnomalies = suggestions;

            const viewToggle = document.getElementById('viewToggle');
            if (viewToggle && viewToggle.checked) {
                viewToggle.checked = false;
                toggleAnomalyView();
            }

            updateSuggestedAnomalyList(suggestedAnomalies, workspaceId);
        })
        .catch(error => {
            loader.style.display = 'none';
            showErrorMessage('Error fetching suggested anomalies: ' + error.message);
        });
}


function updateSuggestedAnomalyList(suggestions, workspaceName) {
    const list = document.getElementById('suggestedAnomalyList');
    if (!list) {
        console.error('suggestedAnomalyList element not found in DOM');
        showErrorMessage('UI error: Could not find suggestedAnomalyList element.');
        return;
    }
    list.innerHTML = ''; // Clear previous content
    console.log('Rendering suggestions:', suggestions); // Debug log

    if (!suggestions || suggestions.length === 0) {
        list.innerHTML = '<p>No suggestions available.</p>';
        return;
    }

    suggestions.forEach((suggestion, index) => {
        try {
            const div = document.createElement('div');
            div.style.marginBottom = '16px';
            div.style.padding = '10px';
            div.style.border = '1px solid #ddd';
            // Escape HTML in suggestion fields to prevent XSS
            const escapeHtml = (str) => str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
            div.innerHTML = `
                <p><strong>${escapeHtml(suggestion.anomaly_name || 'Unnamed Anomaly')}</strong> (Table: ${escapeHtml(suggestion.table_name || 'Unknown')})</p>
                <p>Algorithm: ${escapeHtml(suggestion.algorithm || 'Unknown')}</p>
                <p>SQL: <pre>${escapeHtml(suggestion.sql_query || 'No query provided')}</pre></p>
                <p>Parameters: <pre>${escapeHtml(JSON.stringify(suggestion.parameters || {}, null, 2))}</pre></p>
                <p>Justification: ${escapeHtml(suggestion.justification || 'No justification provided')}</p>
                <button class="test" onclick='useSuggestedAnomaly(${JSON.stringify(JSON.stringify(suggestion))})'>Use Suggestion</button>
            `;
            list.appendChild(div);
        } catch (error) {
            console.error(`Error rendering suggestion ${index}:`, error);
            showErrorMessage(`Error rendering suggestion ${index + 1}: ${error.message}`);
        }
    });
}

function useSuggestedAnomaly(suggestionJson) {
    const suggestion = JSON.parse(suggestionJson);
    const form = document.getElementById('anomalyForm');
    document.getElementById('formTitle').textContent = 'Add Suggested Anomaly';
    document.getElementById('anomalyId').value = '';
    document.getElementById('anomalyName').value = suggestion.anomaly_name;
    document.getElementById('sqlQuery').value = suggestion.sql_query;
    document.getElementById('algorithm').value = suggestion.algorithm;
    document.getElementById('sqlQueryResult').textContent = '';
    updateAnomalyParameterFields();
    // Populate parameter fields
    const parameterFields = document.getElementById('parameterFields');
    if (suggestion.algorithm === 'z_score') {
        document.getElementById('targetColumn').value = suggestion.parameters.target;
        document.getElementById('threshold').value = suggestion.parameters.threshold;
    } else if (suggestion.algorithm === 'isolation_forest') {
        document.getElementById('features').value = suggestion.parameters.features.join(', ');
        document.getElementById('contamination').value = suggestion.parameters.contamination;
    } else if (suggestion.algorithm === 'dbscan') {
        document.getElementById('features').value = suggestion.parameters.features.join(', ');
        document.getElementById('eps').value = suggestion.parameters.eps;
        document.getElementById('min_samples').value = suggestion.parameters.min_samples;
    } else if (suggestion.algorithm === 'custom') {
        document.getElementById('customParams').value = JSON.stringify(suggestion.parameters);
    }
    form.style.display = 'block';
}

function updateAnomalyParameterFields() {
    const algorithm = document.getElementById('algorithm').value;
    const parameterFields = document.getElementById('parameterFields');
    parameterFields.innerHTML = '';

    if (algorithm === 'z_score') {
        parameterFields.innerHTML = `
            <label for="targetColumn">Target Column:</label>
            <input type="text" id="targetColumn" placeholder="e.g., quantity">
            <label for="threshold">Threshold:</label>
            <input type="number" id="threshold" placeholder="e.g., 2.0" step="0.1">
        `;
    } else if (algorithm === 'isolation_forest') {
        parameterFields.innerHTML = `
            <label for="features">Features (comma-separated):</label>
            <input type="text" id="features" placeholder="e.g., quantity, price">
            <label for="contamination">Contamination:</label>
            <input type="number" id="contamination" placeholder="e.g., 0.1" step="0.01">
        `;
    } else if (algorithm === 'dbscan') {
        parameterFields.innerHTML = `
            <label for="features">Features (comma-separated):</label>
            <input type="text" id="features" placeholder="e.g., quantity, price">
            <label for="eps">Epsilon (eps):</label>
            <input type="number" id="eps" placeholder="e.g., 0.5" step="0.1">
            <label for="min_samples">Min Samples:</label>
            <input type="number" id="min_samples" placeholder="e.g., 5" step="1">
        `;
    } else if (algorithm === 'custom') {
        parameterFields.innerHTML = `
            <label for="customParams">Custom Parameters (JSON):</label>
            <textarea id="customParams" rows="4" placeholder='{"param1": "value1", "param2": 42}'></textarea>
        `;
    }
}

function saveAnomaly() {
    const workspaceId = document.getElementById('workspaceId').value;
    const anomalyId = document.getElementById('anomalyId').value;
    const anomalyName = document.getElementById('anomalyName').value.trim();
    const sqlQuery = document.getElementById('sqlQuery').value;
    const algorithm = document.getElementById('algorithm').value;

    if (!anomalyName || !sqlQuery) {
        showErrorMessage("Anomaly name and SQL query are required.");
        return;
    }

    let parameters = {};
    if (algorithm === 'z_score') {
        parameters.target = document.getElementById('targetColumn')?.value || '';
        parameters.threshold = parseFloat(document.getElementById('threshold')?.value) || 2.0;
        if (!parameters.target) {
            showErrorMessage("Target column is required.");
            return;
        }
    } else if (algorithm === 'isolation_forest') {
        parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
        parameters.contamination = parseFloat(document.getElementById('contamination')?.value) || 0.1;
        if (!parameters.features.length) {
            showErrorMessage("Features are required.");
            return;
        }
    } else if (algorithm === 'dbscan') {
        parameters.features = document.getElementById('features')?.value.split(',').map(f => f.trim()) || [];
        parameters.eps = parseFloat(document.getElementById('eps')?.value) || 0.5;
        parameters.min_samples = parseInt(document.getElementById('min_samples')?.value) || 5;
        if (!parameters.features.length) {
            showErrorMessage("Features are required.");
            return;
        }
    } else if (algorithm === 'custom') {
        try {
            parameters = JSON.parse(document.getElementById('customParams')?.value || '{}');
        } catch (e) {
            showErrorMessage("Invalid custom parameters JSON format.");
            return;
        }
    }

    const newAnomaly = {
        enabled: true,
        type: anomalyName.toLowerCase().replace(/\s+/g, '_'),
        sql_query: sqlQuery,
        algorithm,
        parameters
    };

    fetch('/save_anomaly_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, anomalies: [newAnomaly] })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.type === 'error') {
                showErrorMessage(data.error);
            } else if (data.type === 'success') {
                showSuccessMessage(data.message || "Anomaly configuration saved!");
                closeAnomalyForm();
                fetchAnomalyConfigs(workspaceId);
            } else {
                showErrorMessage("Unexpected response format from save anomaly API.");
            }
        })
        .catch(error => {
            console.error('Error saving anomaly:', error);
            showErrorMessage('Error saving anomaly: ' + error.message);
        });
}

function closeAnomalyForm() {
    document.getElementById('anomalyForm').style.display = 'none';
}




//updated fetchAnomalyConfigs function 

   function fetchAnomalyConfigs(workspaceId) {
    fetch(`/api/v0/get_anomaly_configs?workspace_id=${workspaceId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === "error") {
            showErrorMessage(data.error);
            return;
        }
        currentAnomalies = data.anomalies || [];
        updateAnomalyList(currentAnomalies, workspaceId);

        // Sync Master Toggle
        const anyEnabled = currentAnomalies.some(a => a.enabled);
        const allEnabled = currentAnomalies.length > 0 && currentAnomalies.every(a => a.enabled);

        const masterToggle = document.getElementById('masterAnomalyToggle');
        const masterState = document.getElementById('masterAnomalyState');

        if (masterToggle && masterState) {
            masterToggle.checked = allEnabled;
            masterState.textContent = anyEnabled ? 'Enabled' : 'Disabled';
            masterState.classList.toggle('enabled', anyEnabled);
            masterState.classList.toggle('disabled', !anyEnabled);
        }
    })
    .catch(error => showErrorMessage("Error fetching anomaly configs: " + error));
}



//save MasterAnomalyToggle function

   function saveMasterAnomalyToggle(workspaceId) {
    const isEnabled = document.getElementById('masterAnomalyToggle').checked;

    // Update all anomalies locally
    currentAnomalies = currentAnomalies.map(anom => ({ ...anom, enabled: isEnabled }));

    fetch('/save_anomaly_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            workspace_id: workspaceId,
            anomalies: currentAnomalies
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorMessage(data.error);
        } else {
            showSuccessMessage(`All anomalies ${isEnabled ? 'enabled' : 'disabled'}!`);
            updateAnomalyList(currentAnomalies, workspaceId);

            // Update UI
            const stateLabel = document.getElementById('masterAnomalyState');
            stateLabel.textContent = isEnabled ? 'Enabled' : 'Disabled';
            stateLabel.classList.toggle('enabled', isEnabled);
            stateLabel.classList.toggle('disabled', !isEnabled);
        }
    })
    .catch(error => showErrorMessage("Error saving anomaly toggle: " + error));
}





function updateAnomalyList(anomalies, workspaceId) {
    const anomalyList = document.getElementById('anomalyList');
    anomalyList.innerHTML = '';
    anomalies.forEach((anomaly, index) => {
        const div = document.createElement('div');
        div.style.marginBottom = '12px';
        div.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <label class="switch">
                    <input type="checkbox" id="toggle-${index}" ${anomaly.enabled ? 'checked' : ''} 
                           onchange="toggleAnomaly('${anomaly.type}', ${index}, '${workspaceId}')">
                    <span class="slider"></span>
                </label>
                <span>${anomaly.type.replace(/_/g, ' ')}</span>
                <button class="test" onclick="openEditAnomalyByIndex(${index})">Edit</button>
                <button class="test" onclick="deleteAnomaly('${anomaly.type}', '${workspaceId}')">Delete</button>
                <button class="test" onclick="runAnomaly('${anomaly.type}', '${workspaceId}')" ${!anomaly.enabled ? 'disabled' : ''}>Run</button>
            </div>
        `;
        anomalyList.appendChild(div);
    });
}

function openEditAnomalyByIndex(index) {
    if (index < 0 || index >= currentAnomalies.length) {
        showErrorMessage('Invalid anomaly index.');
        return;
    }
    openEditAnomaly(currentAnomalies[index]);
}

function openEditAnomaly(anomaly, isSuggestion = false) {
    const form = document.getElementById('anomalyForm');
    if (!form) {
        showErrorMessage('Anomaly form not found.');
        return;
    }
    const anomalyIdField = document.getElementById('anomalyId');
    const anomalyNameField = document.getElementById('anomalyName');
    const sqlQueryField = document.getElementById('sqlQuery');
    const algorithmField = document.getElementById('algorithm');
    const sqlQueryResultField = document.getElementById('sqlQueryResult');

    document.getElementById('formTitle').textContent = isSuggestion ? 'View Suggested Anomaly' : 'Edit Anomaly';
    anomalyIdField.value = anomaly.type || '';
    anomalyNameField.value = (anomaly.type || '').replace(/_/g, ' ');
    sqlQueryField.value = anomaly.sql_query || '';
    algorithmField.value = anomaly.algorithm || 'z_score';
    sqlQueryResultField.textContent = '';

    updateAnomalyParameterFields();

    const params = anomaly.parameters || {};
    try {
        if (anomaly.algorithm === 'z_score') {
            const targetColumnField = document.getElementById('targetColumn');
            const thresholdField = document.getElementById('threshold');
            if (targetColumnField) targetColumnField.value = params.target || '';
            if (thresholdField) thresholdField.value = params.threshold || '';
        } else if (anomaly.algorithm === 'isolation_forest') {
            const featuresField = document.getElementById('features');
            const contaminationField = document.getElementById('contamination');
            if (featuresField) featuresField.value = Array.isArray(params.features) ? params.features.join(', ') : '';
            if (contaminationField) contaminationField.value = params.contamination || '';
        } else if (anomaly.algorithm === 'dbscan') {
            const featuresField = document.getElementById('features');
            const epsField = document.getElementById('eps');
            const minSamplesField = document.getElementById('min_samples');
            if (featuresField) featuresField.value = Array.isArray(params.features) ? params.features.join(', ') : '';
            if (epsField) epsField.value = params.eps || '';
            if (minSamplesField) minSamplesField.value = params.min_samples || '';
        } else if (anomaly.algorithm === 'custom') {
            const customParamsField = document.getElementById('customParams');
            if (customParamsField) customParamsField.value = JSON.stringify(params, null, 2);
        }
    } catch (error) {
        showErrorMessage('Error populating anomaly parameters: ' + error.message);
        return;
    }

    form.style.display = 'block';
    if (isSuggestion) {
        document.querySelector('#anomalyForm button.save').textContent = 'Add Anomaly';
    } else {
        document.querySelector('#anomalyForm button.save').textContent = 'Save Anomaly';
    }
}

function deleteAnomaly(anomalyType, workspaceId) {
    if (confirm(`Are you sure you want to delete the anomaly configuration "${anomalyType}"?`)) {
        fetch('/delete_anomaly_config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace_id: workspaceId, anomaly_type: anomalyType })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showErrorMessage(data.error);
                } else {
                    showSuccessMessage("Anomaly configuration deleted!");
                    fetchAnomalyConfigs(workspaceId);
                }
            })
            .catch(error => showErrorMessage('Error deleting anomaly: ' + error));
    }
}


/*
function runAnomaly(anomalyType, workspaceId) {
    if (!isVannaConnected) {
        showErrorMessage("Please initialize WI (LLM and DB) before running anomaly detection.");
        return;
    }
    const tableContainer = document.getElementById("tableContainer") || document.createElement("div");
    const visualization = document.getElementById("visualization");
    tableContainer.innerHTML = '<p class="loading">Loading...</p>';
    if (visualization) visualization.style.display = 'none';

    fetch(`/api/v0/run_anomaly?workspace_id=${encodeURIComponent(workspaceId)}&anomaly_type=${encodeURIComponent(anomalyType)}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Run anomaly response:', data); // Debug log
            if (data.type === 'error' || data.type === 'sql_error') {
                tableContainer.innerHTML = `<p class="error">Error: ${data.error}</p>`;
                if (visualization) visualization.style.display = 'none';
                showErrorMessage(data.error);
            } else if (data.type === 'success') {
                // Use fetchAnomaly’s rendering logic for consistency
                renderAnomalyTableAndChart(anomalyType, data.results);
                showSuccessMessage(`Anomaly detection for ${anomalyType.replace('_', ' ')} completed!`);
            } else {
                tableContainer.innerHTML = `<p class="error">Unexpected response format</p>`;
                if (visualization) visualization.style.display = 'none';
                showErrorMessage('Unexpected response format from run anomaly API.');
            }
        })
        .catch(error => {
            console.error('Error running anomaly:', error);
            tableContainer.innerHTML = `<p class="error">Failed to fetch anomaly: ${error.message}</p>`;
            if (visualization) visualization.style.display = 'none';
            showErrorMessage('Error running anomaly detection: ' + error.message);
        });
}

*/


//run anomlay function updated 

function runAnomaly(anomalyType) {
    if (!isVannaConnected) {
        showErrorMessage("Please initialize WI (LLM and DB) before running anomaly detection.");
        return;
    }
    const workspaceId = document.getElementById('workspaceId').value;

    const resultsDiv = document.getElementById('anomalyResults');
    if (!resultsDiv) { showErrorMessage('Results container missing'); return; }

    // loader
    resultsDiv.innerHTML = '<div style="text-align:center;margin:20px"><span class="loader"></span> Running anomaly…</div>';

    fetch(`/api/v0/run_anomaly?workspace_id=${encodeURIComponent(workspaceId)}&anomaly_type=${encodeURIComponent(anomalyType)}`)
        .then(r => r.json())
        .then(data => {
            if (data.type === 'error' || data.type === 'sql_error') {
                resultsDiv.innerHTML = `<p class="error">${data.error}</p>`;
                showErrorMessage(data.error);
                return;
            }
            const rows = data.results || [];
            renderAnomalyTableAndChart(anomalyType, rows);   // ← new helper
            showSuccessMessage(`${anomalyType.replace(/_/g,' ')} anomaly detection completed!`);
        })
        .catch(err => {
            resultsDiv.innerHTML = `<p class="error">${err.message}</p>`;
            showErrorMessage('Error running anomaly: ' + err.message);
        });
}


function renderAnomalyTableAndChart(anomalyType, data) {
    const resultsDiv   = document.getElementById('anomalyResults');
    const tableDiv     = document.getElementById('tableContainer')  || document.createElement('div');
    const chartDiv     = document.getElementById('visualization')   || document.createElement('div');

    tableDiv.id = 'tableContainer';
    chartDiv.id = 'visualization';
    chartDiv.innerHTML = '<canvas id="anomalyChart" width="400" height="300"></canvas>';
    resultsDiv.innerHTML = '';          // wipe old content
    resultsDiv.appendChild(tableDiv);
    resultsDiv.appendChild(chartDiv);

    if (!data || !data.length) { 
        tableDiv.innerHTML = '<p>No anomalies detected.</p>'; 
        chartDiv.style.display='none'; 
        return; 
    }

    // ---------- TABLE ----------
    let html = `<table id="anomalyTable" class="display" style="width:100%"><thead><tr>`;
    const headers = Object.keys(data[0]);
    headers.forEach(h => html += `<th>${h.replace(/_/g,' ').toUpperCase()}</th>`);
    html += '</tr></thead><tbody>';
    data.forEach(r => {
        html += '<tr>';
        headers.forEach(h => html += `<td>${r[h] ?? ''}</td>`);
        html += '</tr>';
    });
    html += '</tbody></table>';
    tableDiv.innerHTML = html;

    // Data-table with CSV export
    setTimeout(() => {
        if ($.fn.DataTable.isDataTable('#anomalyTable')) $('#anomalyTable').DataTable().destroy();
        $('#anomalyTable').DataTable({
            dom: 'Bfrtip',
            buttons: [{ extend: 'csvHtml5', text: '⬇ Export CSV', title: `Anomaly_${anomalyType}_${new Date().toISOString().slice(0,10)}` }],
            pageLength: 10,
            scrollX: true
        });
    }, 0);

    // ---------- CHART (optional) ----------
    if (typeof Chart !== 'undefined') {
        try { 
            renderAnomalyVisualization(data, anomalyType); 
            chartDiv.style.display='block'; 
        }
        catch(e) { 
            console.warn('Chart render skipped:', e); 
            chartDiv.style.display='none'; 
        }
    } else { 
        chartDiv.style.display='none'; 
    }
}


function renderAnomalyVisualization(data, anomaly_type) {
    const canvas = document.getElementById('anomalyChart');
    if (!canvas) return;                       // canvas missing → skip silently

    const ctx = canvas.getContext('2d');
    if (!ctx) return;                          // 2-D context failed → skip

    // 1.  SAFELY destroy previous chart (if any)
    if (window.anomalyChart instanceof Chart) {
        window.anomalyChart.destroy();
    }
    window.anomalyChart = null;                // always reset

    // 2.  Build datasets exactly like before
    const headers   = Object.keys(data[0]);
    const xAxis     = headers[0];
    const yAxis     = headers.find(h => /count|value|len|cnt|missing/i.test(h)) || headers[1];
    const isAnomaly = headers.find(h => /anomaly|outlier/i.test(h));

    const normalPoints = [];
    const anomalyPoints = [];

    data.forEach(row => {
        const point = { x: row[xAxis], y: parseFloat(row[yAxis]) || 0 };
        (isAnomaly && row[isAnomaly] ? anomalyPoints : normalPoints).push(point);
    });

    // 3.  Create new chart
    window.anomalyChart = new Chart(ctx, {
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
                x: { title: { display: true, text: xAxis.replace(/_/g, ' ').toUpperCase() } },
                y: { title: { display: true, text: yAxis.replace(/_/g, ' ').toUpperCase() } }
            },
            plugins: {
                title: {
                    display: true,
                    text: `Anomaly Detection: ${anomaly_type.replace(/_/g,' ').toUpperCase()}`
                },
                legend: { position: 'top' }
            }
        }
    });
}

function displayAnomalyResults(title, results) {
    const resultsDiv = document.getElementById('anomalyResults');
    resultsDiv.innerHTML = `<h5>${title} Results</h5>`;
    if (results.length === 0) {
        resultsDiv.innerHTML += '<p>No anomalies detected.</p>';
        return;
    }
    const table = document.createElement('table');
    table.style.borderCollapse = 'collapse';
    table.style.width = '100%';
    const headers = Object.keys(results[0]);
    const headerRow = document.createElement('tr');
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        th.style.border = '1px solid #ddd';
        th.style.padding = '8px';
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);
    results.forEach(row => {
        const tr = document.createElement('tr');
        headers.forEach(header => {
            const td = document.createElement('td');
            td.textContent = row[header];
            td.style.border = '1px solid #ddd';
            td.style.padding = '8px';
            tr.appendChild(td);
        });
        table.appendChild(tr);
    });
    resultsDiv.appendChild(table);
}

//show agent configurations
function showAgents(id) {
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <h4>Agents</h4>
        <input type="hidden" id="workspaceId" value="${id}">

        <p>Select agent type to configure:</p>

        <button class="save" onclick="loadStockoutAgent('${id}')">Stockout Agent</button>
        <button class="save" onclick="loadDataIntegrityAgent('${id}')">Data Integrity Agent</button>
    `;

    contentArea.style.display = 'block';
}

function loadStockoutAgent(workspaceId) {

    document.getElementById('contentArea').innerHTML = `
        <h4>Stockout Agent</h4>
        <p>Loading configuration...</p>
    `;

    fetch(`/api/v0/get_agent_config?workspace_id=${workspaceId}&agent_type=stockout`)
        .then(res => res.json())
        .then(data => {

            let config = data.agent_config || {};

            // ✅ HARDEN CONFIG (IMPORTANT)
            config.agent_type = "stockout";
            config.enabled = !!config.enabled;
            config.scenarios = Array.isArray(config.scenarios) ? config.scenarios : [];
            config.recipients = Array.isArray(config.recipients) ? config.recipients : [];

            renderStockoutAgentUI(workspaceId, config);
        })
        .catch(err => {
            console.error("LOAD ERROR:", err);
            showErrorMessage("Failed to load agent configuration.");
        });
}



function renderStockoutAgentUI(workspaceId, config) {

    const enabled = config.enabled ? "checked" : "";
    const recipients = Array.isArray(config.recipients) ? config.recipients : [];

    let recipientRows = recipients.map((email, idx) => `
        <div style="display:flex; gap:8px; margin-bottom:6px;">
            <input type="email"
                value="${email}"
                data-index="${idx}"
                class="agent-email"
                style="width:300px;"
            >
            <button class="test" onclick="removeRecipient(${idx})">✕</button>
        </div>
    `).join("");

    let scenarioRows = "";

    STOCKOUT_SCENARIOS.forEach(scenario => {
        const saved = (config.scenarios || []).find(s => s.id === scenario.id);
        const scenarioEnabled = saved ? saved.enabled : false;
        const scenarioSql =
            saved?.sql ||
            STOCKOUT_DEFAULT_SQL?.[scenario.id] ||
            "";

        scenarioRows += `
            <div style="border-bottom:1px solid #ddd; padding:10px 0;">
                <label class="switch">
                    <input type="checkbox"
                        id="toggle_${scenario.id}"
                        ${scenarioEnabled ? "checked" : ""}>
                    <span class="slider"></span>
                </label>

                <strong>${scenario.name}</strong>

                <button class="test" onclick="toggleSqlEditor('${scenario.id}')">Edit SQL</button>
                <button class="test" onclick="testScenarioSQL('${workspaceId}','${scenario.id}')">Test SQL</button>
                <button class="test"onclick="testScenarioAlert('${workspaceId}', '${scenario.id}')">Test Alert</button>


                <textarea id="sql_${scenario.id}"
                    style="display:none;width:98%;height:80px;margin-top:8px;">
${scenarioSql}</textarea>

                <div id="test_${scenario.id}" style="font-size:12px;"></div>
            </div>
        `;
    });

    document.getElementById('contentArea').innerHTML = `
        <h4>Stockout Agent</h4>

        <div style="display:flex; align-items:center; gap:12px;">
            <label class="switch">
                <input type="checkbox" id="stockoutAgentToggle"
                    ${enabled}
                    onchange="updateStockoutToggleUI()">
                <span class="slider"></span>
            </label>
            <span id="stockoutAgentState"
                class="${config.enabled ? "enabled" : "disabled"}">
                ${config.enabled ? "Enabled" : "Disabled"}
            </span>

            <button class="save" onclick="saveStockoutAgent('${workspaceId}')">
                Save Changes
            </button>
        </div>

        <hr>

        <h5>Alert Recipients</h5>
        <div id="recipientList">
            ${recipientRows}
        </div>

        <button class="test" onclick="addRecipient()">+ Add Email</button>

        <hr>

        <h5>Stockout Scenarios</h5>
        ${scenarioRows}
    `;
}


function addRecipient() {
    const list = document.getElementById("recipientList");
    list.insertAdjacentHTML("beforeend", `
        <div style="display:flex; gap:8px; margin-bottom:6px;">
            <input type="email" class="agent-email"
                placeholder="email@example.com"
                style="width:300px;">
            <button class="test" onclick="this.parentElement.remove()">✕</button>
        </div>
    `);
}

function removeRecipient(index) {
    const rows = document.querySelectorAll("#recipientList > div");
    if (rows[index]) rows[index].remove();
}


function openScenarioEditor(id) {
    const field = document.getElementById(`sql_${id}`);
    field.style.display = (field.style.display === "none") ? "block" : "none";
}



function toggleSqlEditor(scenarioId) {
    const textarea = document.getElementById(`sql_${scenarioId}`);
    if (!textarea) return;

    textarea.style.display =
        textarea.style.display === "none" || textarea.style.display === ""
            ? "block"
            : "none";
}


function testScenarioSQL(workspaceId, scenarioId) {

    const sql = document.getElementById(`sql_${scenarioId}`).value;
    const resultArea = document.getElementById(`test_${scenarioId}`);

    resultArea.textContent = "Testing SQL...";
    resultArea.style.color = "blue";

    fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql_query: sql })
    })
    .then(res => res.json())
    .then(data => {
        if (data.type === "error" || data.type === "sql_error") {
            resultArea.textContent = data.error;
            resultArea.style.color = "red";
        } else {
            resultArea.textContent = `Returned ${data.row_count} rows`;
            resultArea.style.color = "green";
        }
    })
    .catch(err => {
        resultArea.textContent = err;
        resultArea.style.color = "red";
    });
}


function updateStockoutToggleUI() {
    const toggle = document.getElementById('stockoutAgentToggle');
    const stateLabel = document.getElementById('stockoutAgentState');

    const isEnabled = toggle.checked;

    stateLabel.textContent = isEnabled ? "Enabled" : "Disabled";

    stateLabel.classList.toggle('enabled', isEnabled);
    stateLabel.classList.toggle('disabled', !isEnabled);
}


function saveStockoutAgent(workspaceId) {

    const enabled = document.getElementById('stockoutAgentToggle').checked;

    const recipients = Array.from(
        document.querySelectorAll('.agent-email')
    )
    .map(input => input.value.trim())
    .filter(email => email.length > 0);

    const scenarios = STOCKOUT_SCENARIOS.map(s => ({
        id: s.id,
        name: s.name,
        enabled: document.getElementById(`toggle_${s.id}`).checked,
        sql: document.getElementById(`sql_${s.id}`).value
    }));

    const payload = {
        workspace_id: workspaceId,
        agent_config: {
            agent_type: "stockout",
            enabled,
            recipients,
            scenarios
        }
    };

    fetch('/api/v0/save_agent_config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage("Stockout Agent saved successfully.");
        } else {
            showErrorMessage("Failed to save Stockout Agent.");
        }
    })
    .catch(err => showErrorMessage(err));
}



function testScenarioAlert(workspaceId, scenarioId) {

    const sql = document.getElementById(`sql_${scenarioId}`).value;

    const recipients = Array.from(
        document.querySelectorAll('.agent-email')
    )
    .map(i => i.value.trim())
    .filter(v => v.length > 0);

    if (recipients.length === 0) {
        showErrorMessage("Please add at least one email recipient.");
        return;
    }

    fetch("/api/v0/test_agent_alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            workspace_id: workspaceId,
            agent_type: "stockout",
            scenario_id: scenarioId,
            sql: sql,
            recipients: recipients
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage(data.message);
        } else {
            showErrorMessage(data.error);
        }
    })
    .catch(err => showErrorMessage(err));
}


// Data Integrity Agent UI

function loadDataIntegrityAgent(workspaceId) {

    document.getElementById('contentArea').innerHTML = `
        <h4>Data Integrity Agent</h4>
        <p>Loading configuration...</p>
    `;

    fetch(`/api/v0/get_agent_config?workspace_id=${workspaceId}&agent_type=data_integrity`)
        .then(res => res.json())
        .then(data => {

            let config = data.agent_config || {};

            config.agent_type = "data_integrity";
            config.enabled = !!config.enabled;
            config.scenarios = Array.isArray(config.scenarios) ? config.scenarios : [];
            config.recipients = Array.isArray(config.recipients) ? config.recipients : [];
            config.interval_minutes = config.interval_minutes || 30;

            renderDataIntegrityAgentUI(workspaceId, config);
        })
        .catch(err => {
            console.error("LOAD ERROR:", err);
            showErrorMessage("Failed to load Data Integrity Agent.");
        });
}


function renderDataIntegrityAgentUI(workspaceId, config) {

    const enabled = config.enabled ? "checked" : "";
    const recipients = Array.isArray(config.recipients) ? config.recipients : [];
    const intervalMinutes = config.interval_minutes || 5;

    const cooldownDays = config.cooldown_days || 0;
    const cooldownMinutes = config.cooldown_minutes || 60;

    // ---------- Recipient Rows ----------
    let recipientRows = recipients.map((email) => `
        <div style="display:flex; gap:8px; margin-bottom:6px;">
            <input type="email"
                value="${email}"
                class="agent-email"
                style="width:300px;">
            <button class="test"
                onclick="this.parentElement.remove()">✕</button>
        </div>
    `).join("");

    // ---------- Scenario Rows ----------
    let scenarioRows = "";

    DATA_INTEGRITY_SCENARIOS.forEach(scenario => {

        const saved = (config.scenarios || []).find(s => s.id === scenario.id);
        const scenarioEnabled = saved ? saved.enabled : false;
        const scenarioSql = saved?.sql && saved.sql.trim().length > 0
            ? saved.sql
            : (DATA_INTEGRITY_SQL_MAP[scenario.id] || "");

        scenarioRows += `
            <div style="border-bottom:1px solid #ddd; padding:12px 0;">

                <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">

                    <label class="switch">
                        <input type="checkbox"
                            id="toggle_${scenario.id}"
                            ${scenarioEnabled ? "checked" : ""}>
                        <span class="slider"></span>
                    </label>

                    <strong>${scenario.name}</strong>

                    <button class="test"
                        onclick="toggleSqlEditor('${scenario.id}')">
                        Edit SQL
                    </button>

                    <button class="test"
                        onclick="testIntegritySQL('${workspaceId}','${scenario.id}')">
                        Test SQL
                    </button>

                    <button class="test"
                        onclick="testIntegrityAlert('${workspaceId}','${scenario.id}')">
                        Test Alert
                    </button>

                </div>

                <textarea id="sql_${scenario.id}"
                    style="display:none;width:98%;height:90px;margin-top:10px;">
${scenarioSql}</textarea>

                <div id="test_${scenario.id}"
                    style="font-size:12px;margin-top:6px;"></div>

            </div>
        `;
    });

    document.getElementById('contentArea').innerHTML = `
        <h4>Data Integrity Agent</h4>

        <div style="display:flex; align-items:center; gap:12px;">
            <label class="switch">
                <input type="checkbox"
                    id="dataIntegrityToggle"
                    ${enabled}
                    onchange="updateDataIntegrityToggleUI()">
                <span class="slider"></span>
            </label>

            <span id="dataIntegrityState"
                class="${config.enabled ? "enabled" : "disabled"}">
                ${config.enabled ? "Enabled" : "Disabled"}
            </span>

            <button class="save"
                onclick="saveDataIntegrityAgent('${workspaceId}')">
                Save Changes
            </button>
        </div>

        <hr>

        <h5>Execution Interval</h5>
        <input type="number"
            id="integrityInterval"
            min="1"
            value="${intervalMinutes}"
            style="width:120px;"> minutes

        <hr>

        <h5>Alert Cooldown</h5>

        <div style="display:flex; gap:20px;">
            <div>
                <label>Days</label><br>
                <input type="number"
                    id="cooldownDays"
                    min="0"
                    value="${cooldownDays}"
                    style="width:80px;">
            </div>

            <div>
                <label>Minutes</label><br>
                <input type="number"
                    id="cooldownMinutes"
                    min="0"
                    value="${cooldownMinutes}"
                    style="width:100px;">
            </div>
        </div>

        <hr>

        <h5>Alert Recipients</h5>
        <div id="recipientList">
            ${recipientRows}
        </div>

        <button class="test" onclick="addRecipient()">
            + Add Email
        </button>

        <hr>

        <h5>Data Integrity Scenarios</h5>
        ${scenarioRows}
    `;
}


function updateDataIntegrityToggleUI() {
    const toggle = document.getElementById('dataIntegrityToggle');
    const stateLabel = document.getElementById('dataIntegrityState');

    const isEnabled = toggle.checked;

    stateLabel.textContent = isEnabled ? "Enabled" : "Disabled";

    stateLabel.classList.toggle('enabled', isEnabled);
    stateLabel.classList.toggle('disabled', !isEnabled);
}


function saveDataIntegrityAgent(workspaceId) {

    const enabled =
        document.getElementById('dataIntegrityToggle').checked;

    const interval_minutes =
        parseInt(document.getElementById("integrityInterval").value) || 5;

    const cooldown_days =
        parseInt(document.getElementById("cooldownDays").value) || 0;

    const cooldown_minutes =
        parseInt(document.getElementById("cooldownMinutes").value) || 60;

    const recipients = Array.from(
        document.querySelectorAll('.agent-email')
    )
    .map(input => input.value.trim())
    .filter(email => email.length > 0);

    const scenarios = DATA_INTEGRITY_SCENARIOS.map(s => ({
        id: s.id,
        name: s.name,
        enabled: document.getElementById(`toggle_${s.id}`).checked,
        sql: document.getElementById(`sql_${s.id}`).value
    }));

    const payload = {
        workspace_id: workspaceId,
        agent_config: {
            agent_type: "data_integrity",
            enabled,
            interval_minutes,
            cooldown_days,
            cooldown_minutes,
            recipients,
            scenarios
        }
    };

    fetch('/api/v0/save_agent_config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage("Data Integrity Agent saved successfully.");
        } else {
            showErrorMessage("Failed to save Data Integrity Agent.");
        }
    })
    .catch(err => showErrorMessage(err));
}



function testIntegritySQL(workspaceId, scenarioId) {

    const sql = document.getElementById(`sql_${scenarioId}`).value;
    const resultArea = document.getElementById(`test_${scenarioId}`);

    resultArea.textContent = "Testing SQL...";
    resultArea.style.color = "blue";

    fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql_query: sql })
    })
    .then(res => res.json())
    .then(data => {
        if (data.type === "error" || data.type === "sql_error") {
            resultArea.textContent = data.error;
            resultArea.style.color = "red";
        } else {
            resultArea.textContent = `Returned ${data.row_count} rows`;
            resultArea.style.color = "green";
        }
    })
    .catch(err => {
        resultArea.textContent = err;
        resultArea.style.color = "red";
    });
}


function testIntegrityAlert(workspaceId, scenarioId) {

    const sql = document.getElementById(`sql_${scenarioId}`).value;

    const recipients = Array.from(
        document.querySelectorAll('.agent-email')
    )
    .map(i => i.value.trim())
    .filter(v => v.length > 0);

    if (recipients.length === 0) {
        showErrorMessage("Please add at least one email recipient.");
        return;
    }

    fetch("/api/v0/test_agent_alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            workspace_id: workspaceId,
            agent_type: "data_integrity",
            scenario_id: scenarioId,
            sql: sql,
            recipients: recipients
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage(data.message);
        } else {
            showErrorMessage(data.error);
        }
    })
    .catch(err => showErrorMessage(err));
}


// ============ RESET DEVICES AGENT - COMPLETE WORKING CODE ============

function deviceResetToast(message, type) {
    const colors = { success: 'linear-gradient(135deg,#38a169,#276749)', error: 'linear-gradient(135deg,#e53e3e,#c53030)', warning: 'linear-gradient(135deg,#d69e2e,#b7791f)', info: 'linear-gradient(135deg,#4299e1,#2b6cb0)' };
    Toastify({ text: message, duration: type === 'error' ? 5000 : 3000, gravity: 'top', position: 'center', style: { background: colors[type] || colors.info }, stopOnFocus: true }).showToast();
}

function showResetDevicesAgent(workspaceId) {
    const contentArea = document.getElementById('contentArea');
    contentArea.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div>
                <h4 style="margin: 0 0 4px;">Reset Devices Agent</h4>
                <p style="margin: 0; color: #718096; font-size: 14px;">Automatically detects and resets stuck RMF/forklift devices. Use Manual Reset to handle specific devices on demand.</p>
            </div>
        </div>
        <input type="hidden" id="deviceResetWorkspaceId" value="${workspaceId}">

        <!-- Tabs -->
        <div style="display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0;">
            <button id="deviceResetTab_auto"   onclick="switchDeviceResetTab('auto')"   style="padding: 8px 20px; border: none; border-bottom: 3px solid #7B83EB; background: none; font-weight: 600; color: #7B83EB; cursor: pointer;">Automated</button>
            <button id="deviceResetTab_manual" onclick="switchDeviceResetTab('manual')" style="padding: 8px 20px; border: none; border-bottom: 3px solid transparent; background: none; color: #718096; cursor: pointer;">Manual Reset</button>
        </div>

        <div id="deviceResetPanel_auto"   style="display: block;"></div>
        <div id="deviceResetPanel_manual" style="display: none;"></div>
    `;
    contentArea.style.display = 'block';

    renderDeviceResetAutoTab(workspaceId);
    renderDeviceResetManualTab(workspaceId);
}

function switchDeviceResetTab(tab) {
    ['auto', 'manual'].forEach(t => {
        const btn   = document.getElementById('deviceResetTab_' + t);
        const panel = document.getElementById('deviceResetPanel_' + t);
        const active = (t === tab);
        if (btn)   { btn.style.borderBottom = active ? '3px solid #7B83EB' : '3px solid transparent'; btn.style.color = active ? '#7B83EB' : '#718096'; btn.style.fontWeight = active ? '600' : '400'; }
        if (panel) panel.style.display = active ? 'block' : 'none';
    });
}

function renderDeviceResetAutoTab(workspaceId) {
    const panel = document.getElementById('deviceResetPanel_auto');
    panel.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div>
                    <h5 style="margin: 0 0 4px;">Background Scheduler</h5>
                    <p style="margin: 0; color: #718096; font-size: 13px;">Scans for stuck devices and resets them automatically. All actions are logged.</p>
                </div>
                <button class="test" onclick="loadDeviceResetSchedulerStatus()" style="white-space: nowrap;">Refresh Status</button>
            </div>

            <div id="deviceResetSchedulerStatus" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                <div style="background: #f7fafc; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 12px; color: #718096; margin-bottom: 4px;">STATUS</div>
                    <div id="deviceResetStatusBadge" style="font-size: 15px; font-weight: 600;">Loading...</div>
                    <button id="deviceResetToggleBtn" onclick="toggleDeviceResetScheduler()" class="save" style="margin-top: 10px; padding: 6px 16px; font-size: 13px;">...</button>
                </div>
                <div style="background: #f7fafc; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 12px; color: #718096; margin-bottom: 4px;">NEXT RUN</div>
                    <div id="deviceResetNextRun" style="font-size: 14px; font-weight: 500;">—</div>
                </div>
            </div>

            <div style="background: #f7fafc; border-radius: 8px; padding: 14px; display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 12px; color: #718096; white-space: nowrap;">RUN EVERY</div>
                <input type="number" id="deviceResetIntervalInput" min="0.25" max="168" step="0.25" value="2" style="width: 80px; padding: 6px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px;">
                <span style="font-size: 14px; color: #4a5568;">hours</span>
                <button class="save" onclick="updateDeviceResetSchedulerInterval()" style="padding: 6px 16px; font-size: 13px;">Apply</button>
                <span id="deviceResetIntervalMsg" style="font-size: 12px; color: #718096;"></span>
            </div>
        </div>

        <div style="display: flex; gap: 8px;">
            <button class="test" onclick="showDeviceResetLogs('${workspaceId}')">
                <i class="fas fa-list-alt"></i> View Automated Logs
            </button>
        </div>
    `;
    loadDeviceResetSchedulerStatus();
}

function loadDeviceResetSchedulerStatus() {
    fetch('/api/v0/device_reset_agent/scheduler_status')
        .then(r => r.json())
        .then(data => {
            const badge    = document.getElementById('deviceResetStatusBadge');
            const toggleBtn = document.getElementById('deviceResetToggleBtn');
            const nextRun  = document.getElementById('deviceResetNextRun');
            const interval = document.getElementById('deviceResetIntervalInput');
            if (!badge) return;
            if (data.paused) {
                badge.innerHTML = '<span style="color:#718096;">&#9675; Paused</span>';
                toggleBtn.textContent = 'Enable';
                toggleBtn.className = 'save';
                toggleBtn.style.background = '';
            } else {
                badge.innerHTML = '<span style="color:#38a169;">&#9679; Running</span>';
                toggleBtn.textContent = 'Disable';
                toggleBtn.className = 'test';
                toggleBtn.style.background = '';
            }
            nextRun.textContent = data.next_run || '—';
            if (interval && data.interval_hours != null) interval.value = data.interval_hours;
        })
        .catch(() => { const b = document.getElementById('deviceResetStatusBadge'); if (b) b.textContent = 'Error loading status'; });
}

function toggleDeviceResetScheduler() {
    fetch('/api/v0/device_reset_agent/scheduler_toggle', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
        .then(r => r.json())
        .then(data => {
            if (data.type === 'error') { deviceResetToast('Error: ' + data.error, 'error'); return; }
            deviceResetToast('Scheduler ' + data.action, data.action === 'paused' ? 'warning' : 'success');
            loadDeviceResetSchedulerStatus();
        })
        .catch(() => deviceResetToast('Failed to toggle scheduler', 'error'));
}

function updateDeviceResetSchedulerInterval() {
    const hours = parseFloat(document.getElementById('deviceResetIntervalInput').value);
    if (isNaN(hours) || hours < 0.25 || hours > 168) { deviceResetToast('Enter a value between 0.25 and 168 hours', 'warning'); return; }
    const msg = document.getElementById('deviceResetIntervalMsg');
    if (msg) msg.textContent = 'Updating...';
    fetch('/api/v0/device_reset_agent/scheduler_interval', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hours })
    })
    .then(r => r.json())
    .then(data => {
        if (data.type === 'error') { deviceResetToast('Error: ' + data.error, 'error'); if (msg) msg.textContent = ''; return; }
        deviceResetToast('Interval updated to ' + hours + ' hour(s)', 'success');
        if (msg) msg.textContent = 'Updated';
        loadDeviceResetSchedulerStatus();
    })
    .catch(() => { deviceResetToast('Failed to update interval', 'error'); if (msg) msg.textContent = ''; });
}

function renderDeviceResetManualTab(workspaceId) {
    const panel = document.getElementById('deviceResetPanel_manual');
    panel.innerHTML = `
        <input type="hidden" id="workspaceId" value="${workspaceId}">

        <!-- Progress Indicator -->
        <div style="margin: 20px 0; padding: 15px; background: #f7fafc; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                    <div id="wizardProgressBar" style="width: 14%; height: 100%; background: #7B83EB; transition: width 0.3s;"></div>
                </div>
                <span id="wizardStepDisplay" style="margin-left: 15px; font-size: 14px; color: #4a5568;">Step 1 of 7</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                <span style="font-size: 12px;">1. Identify User</span>
                <span style="font-size: 12px;">2. Map Fork</span>
                <span style="font-size: 12px;">3. Inventory</span>
                <span style="font-size: 12px;">4. Temp Location</span>
                <span style="font-size: 12px;">5. Confirm</span>
                <span style="font-size: 12px;">6. Relocate</span>
                <span style="font-size: 12px;">7. Logout</span>
            </div>
        </div>

        <!-- Wizard Content Container -->
        <div id="wizardContent" style="background: white; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0;">
            <!-- Step content will be loaded here -->
        </div>

        <!-- Navigation Buttons -->
        <div style="margin-top: 20px; display: flex; justify-content: space-between;">
            <div>
                <button id="wizardAbortBtn" class="test" onclick="abortResetWizard()" style="background: #f56565; color: white; border: none;">
                    <i class="fas fa-times"></i> Abort & Rollback
                </button>
            </div>
            <div>
                <button id="wizardBackBtn" class="test" onclick="wizardGoBack()" style="display: none;">← Back</button>
                <button id="wizardNextBtn" class="save" onclick="wizardGoNext()">Next Step →</button>
            </div>
        </div>

        <!-- Rollback/Status Container -->
        <div id="wizardStatus" style="margin-top: 20px; padding: 12px; border-radius: 8px; display: none;"></div>
    `;

    // Reset wizard state and start at step 1
    resetWizardState = {
        currentStep: 1,
        totalSteps: 7,
        employeeData: null,
        forkLocation: null,
        inventoryItems: null,
        tempLocation: null,
        relocationExecuted: false,
        logoutExecuted: false
    };
    loadWizardStep(workspaceId);
}

// Reset Devices Agent - Wizard Flow
let resetWizardState = {
    currentStep: 1,
    totalSteps: 7,
    employeeData: null,
    forkLocation: null,
    inventoryItems: null,
    tempLocation: null,
    relocationExecuted: false,
    logoutExecuted: false
};

// ============ WIZARD NAVIGATION FUNCTIONS ============

function loadWizardStep(workspaceId) {
    const currentStep = resetWizardState.currentStep;
    const contentDiv = document.getElementById('wizardContent');
    const backBtn = document.getElementById('wizardBackBtn');
    const nextBtn = document.getElementById('wizardNextBtn');
    const progressBar = document.getElementById('wizardProgressBar');
    const stepDisplay = document.getElementById('wizardStepDisplay');

    // Update progress bar (14% per step)
    const progressPercent = (currentStep / resetWizardState.totalSteps) * 100;
    if (progressBar) progressBar.style.width = `${progressPercent}%`;
    if (stepDisplay) stepDisplay.textContent = `Step ${currentStep} of ${resetWizardState.totalSteps}`;

    // Show/hide back button (hide on step 1)
    if (backBtn) backBtn.style.display = currentStep === 1 ? 'none' : 'inline-block';

    // Change Next button text on last step
    if (nextBtn) {
        if (currentStep === resetWizardState.totalSteps) {
            nextBtn.textContent = 'Complete Reset →';
        } else if (currentStep === 6) {
            nextBtn.textContent = 'Execute Relocation →';
        } else {
            nextBtn.textContent = 'Next Step →';
        }
    }

    // Load step-specific content
    switch(currentStep) {
        case 1:
            renderStep1IdentifyUser(workspaceId, contentDiv);
            break;
        case 2:
            renderStep2MapFork(workspaceId, contentDiv);
            break;
        case 3:
            renderStep3InventoryCheck(workspaceId, contentDiv);
            break;
        case 4:
            renderStep4TempLocation(workspaceId, contentDiv);
            break;
        case 5:
            renderStep5ConfirmRelocation(workspaceId, contentDiv);
            break;
        case 6:
            renderStep6ExecuteRelocation(workspaceId, contentDiv);
            break;
        case 7:
            renderStep7LogoutAndClear(workspaceId, contentDiv);
            break;
        default:
            contentDiv.innerHTML = '<p>Unknown step.</p>';
    }
}

function wizardGoNext() {
    const workspaceId = document.getElementById('workspaceId').value;
    const currentStep = resetWizardState.currentStep;

    // Validate current step before proceeding
    if (!validateCurrentStep()) {
        return;
    }

    if (currentStep < resetWizardState.totalSteps) {
        resetWizardState.currentStep++;
        loadWizardStep(workspaceId);
    }
}

function wizardGoBack() {
    const workspaceId = document.getElementById('workspaceId').value;
    const currentStep = resetWizardState.currentStep;

    if (currentStep > 1) {
        resetWizardState.currentStep--;
        loadWizardStep(workspaceId);
    }
}

function validateCurrentStep() {
    const currentStep = resetWizardState.currentStep;

    switch(currentStep) {
        case 1:
            if (!resetWizardState.employeeData) {
                showErrorMessage('Please search and select an employee first');
                return false;
            }
            break;
        case 2:
            if (!resetWizardState.forkLocation) {
                showErrorMessage('Please find and confirm fork location first');
                return false;
            }
            break;
        case 3:
            if (!resetWizardState.inventoryItems) {
                showErrorMessage('Please check inventory first');
                return false;
            }
            break;
        case 4:
            if (!resetWizardState.tempLocation) {
                showErrorMessage('Please validate and confirm a temporary location first');
                return false;
            }
            break;
        case 5:
            // Final confirmation - always valid
            break;
        case 6:
            if (resetWizardState.relocationExecuted) {
                showErrorMessage('Relocation already executed');
                return false;
            }
            break;
        case 7:
            if (resetWizardState.logoutExecuted) {
                showErrorMessage('Logout already executed');
                return false;
            }
            break;
    }

    return true;
}

function abortResetWizard() {
    if (confirm(' Are you sure you want to abort the reset operation?\n\nAny partial changes will be rolled back and you will return to Step 1.')) {
        showErrorMessage('Reset aborted by user. No changes were committed.');

        // Reset wizard state
        resetWizardState = {
            currentStep: 1,
            totalSteps: 7,
            employeeData: null,
            forkLocation: null,
            inventoryItems: null,
            tempLocation: null,
            relocationExecuted: false,
            logoutExecuted: false
        };

        const workspaceId = document.getElementById('workspaceId').value;
        loadWizardStep(workspaceId);
    }
}




// ============ STEP 1: IDENTIFY USER ============

function renderStep1IdentifyUser(workspaceId, container) {
    container.innerHTML = `
        <h5 style="margin-bottom: 16px;">Step 1: Identify User & Device</h5>
        <p>Search for the employee currently assigned to the RMF/forklift device.</p>

        <div style="margin-bottom: 16px;">
            <label for="empSearchType">Search By:</label>
            <select id="empSearchType" style="width: 200px; margin-left: 10px;" onchange="toggleEmpSearchFields()">
                <option value="id">Employee ID</option>
                <option value="name">Username/Name</option>
                <option value="device">Device ID</option>
            </select>
        </div>

        <div id="empIdField" style="margin-bottom: 16px;">
            <label for="empId">Employee ID:</label>
            <input type="text" id="empId" placeholder="Enter employee ID" style="width: 300px; margin-left: 10px;">
        </div>

        <div id="empNameField" style="margin-bottom: 16px; display: none;">
            <label for="empName">Username/Name:</label>
            <input type="text" id="empName" placeholder="Enter username" style="width: 300px; margin-left: 10px;">
        </div>

        <div id="empDeviceField" style="margin-bottom: 16px; display: none;">
            <label for="empDevice">Device ID:</label>
            <input type="text" id="empDevice" placeholder="Enter device ID" style="width: 300px; margin-left: 10px;">
        </div>

        <button class="test" onclick="searchEmployee('${workspaceId}')">Search Employee</button>

        <div id="employeeSearchResult" style="margin-top: 20px; padding: 12px; border-radius: 8px; display: none;"></div>

        <div id="empValidationMessage" style="margin-top: 12px;"></div>
    `;
}

function toggleEmpSearchFields() {
    const searchType = document.getElementById('empSearchType').value;
    document.getElementById('empIdField').style.display = searchType === 'id' ? 'block' : 'none';
    document.getElementById('empNameField').style.display = searchType === 'name' ? 'block' : 'none';
    document.getElementById('empDeviceField').style.display = searchType === 'device' ? 'block' : 'none';
}

function searchEmployee(workspaceId) {
    const searchType = document.getElementById('empSearchType').value;
    let searchValue = '';

    if (searchType === 'id') {
        searchValue = document.getElementById('empId').value.trim();
    } else if (searchType === 'name') {
        searchValue = document.getElementById('empName').value.trim();
    } else {
        searchValue = document.getElementById('empDevice').value.trim();
    }

    if (!searchValue) {
        showErrorMessage('Please enter a search value');
        return;
    }

    // Build query with CAST to handle datetime columns
    let query = '';
    if (searchType === 'id') {
        query = `SELECT id, name, CAST(device AS NVARCHAR(100)) as device, wh_id FROM t_employee WHERE CAST(id AS NVARCHAR(100)) LIKE '%${searchValue}%'`;
    } else if (searchType === 'name') {
        query = `SELECT id, name, CAST(device AS NVARCHAR(100)) as device, wh_id FROM t_employee WHERE name LIKE '%${searchValue}%'`;
    } else {
        query = `SELECT id, name, CAST(device AS NVARCHAR(100)) as device, wh_id FROM t_employee WHERE CAST(device AS NVARCHAR(100)) LIKE '%${searchValue}%'`;
    }

    const resultDiv = document.getElementById('employeeSearchResult');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<span class="loader"></span> Searching...';
    resultDiv.style.background = '#ebf8ff';

    fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql_query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === 'error' || data.type === 'sql_error') {
            resultDiv.innerHTML = `<span style="color: red;"> Error: ${data.error}</span>`;
            resultDiv.style.background = '#fed7d7';
        } else if (data.df && data.df.length > 0) {
            // Store employee data in global variable
            window.selectedEmployeeData = data.df[0];

            const emp = data.df[0];

            // Build display table - clean any HTML entities
            let html = '<strong> Employee Found:</strong><br><br>';
            html += '<div style="background: #e2e8f0; padding: 15px; border-radius: 8px;">';
            html += '<table style="width:100%; border-collapse: collapse;">';

            // Display each field
            const fields = ['id', 'name', 'device', 'wh_id'];
            for (const field of fields) {
                let value = emp[field];
                if (value === null || value === undefined || value === 'NaT') {
                    value = '';
                }
                // Clean the value - remove any HTML entities
                value = String(value).replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
                html += `<tr><td style="padding: 8px; font-weight: bold; width: 100px;">${field}:</td><td style="padding: 8px;">${value}</td></tr>`;
            }

            html += '</table>';
            html += '</div>';
            html += `<br><button class="save" onclick='selectEmployeeFromGlobal("${workspaceId}")'>Select This Employee</button>`;

            resultDiv.innerHTML = html;
            resultDiv.style.background = '#c6f6d5';
        } else {
            resultDiv.innerHTML = '<span style="color: orange;"> No employee found with that search criteria. Device may already be reset or invalid.</span>';
            resultDiv.style.background = '#feebc8';
        }
    })
    .catch(error => {
        resultDiv.innerHTML = `<span style="color: red;"> Error: ${error}</span>`;
        resultDiv.style.background = '#fed7d7';
    });
}

function selectEmployeeFromGlobal(workspaceId) {
    const employee = window.selectedEmployeeData;
    if (!employee) {
        showErrorMessage('No employee selected');
        return;
    }

    resetWizardState.employeeData = employee;
    showSuccessMessage(`Employee selected: ${employee.name || employee.id}`);

    // Auto-advance to next step
    resetWizardState.currentStep = 2;
    loadWizardStep(workspaceId);
}

// Legacy function (kept for compatibility)
function selectEmployee(employee, workspaceId) {
    resetWizardState.employeeData = employee;
    showSuccessMessage(`Employee selected: ${employee.name || employee.id}`);
    resetWizardState.currentStep = 2;
    loadWizardStep(workspaceId);
}



// Step 2: Map Fork Location
function renderStep2MapFork(workspaceId, container) {
    const employee = resetWizardState.employeeData;

    container.innerHTML = `
        <h5 style="margin-bottom: 16px;">Step 2: Locate Fork/Device Assignment</h5>
        <p>Finding the fork location assigned to employee: <strong>${employee.name || employee.id}</strong></p>

        <div style="background: #f0f4f8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong>Employee Details:</strong></p>
            <ul style="margin: 10px 0 0 20px;">
                <li>ID: ${employee.id || 'N/A'}</li>
                <li>Name: ${employee.name || 'N/A'}</li>
                <li>Device: ${employee.device || 'N/A'}</li>
                ${employee.wh_id ? `<li>Warehouse: ${employee.wh_id}</li>` : ''}
            </ul>
        </div>

        <button class="test" onclick="findForkLocation('${workspaceId}')"> Find Fork Location</button>

        <div id="forkLocationResult" style="margin-top: 20px; padding: 12px; border-radius: 8px; display: none;"></div>

        <div id="forkValidationMessage" style="margin-top: 12px;"></div>
    `;
}

function findForkLocation(workspaceId) {
    const employee = resetWizardState.employeeData;
    const whId = employee.wh_id || '';

    // Query t_location where c1 = employee id
    const query = `SELECT location_id, wh_id, status, c1 FROM t_location WHERE c1 = '${employee.id}' AND wh_id = '${whId}'`;

    const resultDiv = document.getElementById('forkLocationResult');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<span class="loader"></span> Locating fork...';
    resultDiv.style.background = '#ebf8ff';

    fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql_query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === 'error' || data.type === 'sql_error') {
            resultDiv.innerHTML = `<span style="color: red;"> Error: ${data.error}</span>`;
            resultDiv.style.background = '#fed7d7';
        } else if (data.df && data.df.length > 0) {
            const fork = data.df[0];
            resetWizardState.forkLocation = fork;

            let html = '<strong> Fork Location Found:</strong><br><br>';
            html += '<table style="width:100%; border-collapse: collapse;">';
            html += '<tr style="background:#e2e8f0;"><th style="padding:8px; border:1px solid #ddd;">Location ID</th><th style="padding:8px; border:1px solid #ddd;">Warehouse</th><th style="padding:8px; border:1px solid #ddd;">Status</th></tr>';
            html += `<tr><td style="padding:8px; border:1px solid #ddd;">${fork.location_id}</td>`;
            html += `<td style="padding:8px; border:1px solid #ddd;">${fork.wh_id}</td>`;
            html += `<td style="padding:8px; border:1px solid #ddd;">${fork.status || 'Active'}</td></tr>`;
            html += '</table>';
            html += `<br><button class="save" onclick="confirmForkLocation('${workspaceId}')"> Confirm & Continue</button>`;

            resultDiv.innerHTML = html;
            resultDiv.style.background = '#c6f6d5';
        } else {
            resultDiv.innerHTML = '<span style="color: orange;"> No fork location found for this employee. Employee may not be assigned to a device/fork.</span>';
            resultDiv.style.background = '#feebc8';
        }
    })
    .catch(error => {
        resultDiv.innerHTML = `<span style="color: red;"> Error: ${error}</span>`;
        resultDiv.style.background = '#fed7d7';
    });
}

function confirmForkLocation(workspaceId) {
    showSuccessMessage(`Fork location confirmed: ${resetWizardState.forkLocation.location_id}`);
    resetWizardState.currentStep = 3;
    loadWizardStep(workspaceId);
}

// Step 3: Inventory Check at Fork Location
function renderStep3InventoryCheck(workspaceId, container) {
    const fork = resetWizardState.forkLocation;

    container.innerHTML = `
        <h5 style="margin-bottom: 16px;">Step 3: Inventory Check at Fork Location</h5>
        <p>Checking inventory at fork location: <strong>${fork.location_id}</strong></p>

        <div style="background: #f0f4f8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong>Location Details:</strong></p>
            <ul style="margin: 10px 0 0 20px;">
                <li>Location ID: ${fork.location_id}</li>
                <li>Warehouse: ${fork.wh_id}</li>
                <li>Status: ${fork.status || 'Active'}</li>
            </ul>
        </div>

        <button class="test" onclick="checkInventoryAtFork('${workspaceId}')"> Check Inventory</button>

        <div id="inventoryCheckResult" style="margin-top: 20px; padding: 12px; border-radius: 8px; display: none;"></div>

        <div id="inventoryValidationMessage" style="margin-top: 12px;"></div>
    `;
}

function checkInventoryAtFork(workspaceId) {
    const fork = resetWizardState.forkLocation;
    const whId = fork.wh_id;
    const locationId = fork.location_id;

    // Three queries to check inventory
    const queries = {
        stored_item: `SELECT * FROM t_stored_item WHERE location_id = '${locationId}' AND wh_id = '${whId}'`,
        hu_master: `SELECT * FROM t_hu_master WHERE location_id = '${locationId}' AND wh_id = '${whId}'`,
        hu_detail: `SELECT * FROM t_hu_detail WHERE location_id = '${locationId}' AND wh_id = '${whId}'`
    };

    const resultDiv = document.getElementById('inventoryCheckResult');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<span class="loader"></span> Checking inventory across all tables...';
    resultDiv.style.background = '#ebf8ff';

    // Execute all three queries
    Promise.all([
        fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql_query: queries.stored_item })
        }).then(r => r.json()),
        fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql_query: queries.hu_master })
        }).then(r => r.json()),
        fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql_query: queries.hu_detail })
        }).then(r => r.json())
    ])
    .then(([storedData, huMasterData, huDetailData]) => {
        const storedCount = storedData.df ? storedData.df.length : 0;
        const huMasterCount = huMasterData.df ? huMasterData.df.length : 0;
        const huDetailCount = huDetailData.df ? huDetailData.df.length : 0;
        const totalItems = storedCount + huMasterCount + huDetailCount;

        resetWizardState.inventoryItems = {
            stored: storedData.df || [],
            huMaster: huMasterData.df || [],
            huDetail: huDetailData.df || [],
            totalCount: totalItems
        };

        let html = `<strong> Inventory Summary:</strong><br><br>`;
        html += '<table style="width:100%; border-collapse: collapse;">';
        html += '<tr style="background:#e2e8f0;"><th style="padding:8px; border:1px solid #ddd;">Table</th><th style="padding:8px; border:1px solid #ddd;">Item Count</th></tr>';
        html += `<tr><td style="padding:8px; border:1px solid #ddd;">t_stored_item</td><td style="padding:8px; border:1px solid #ddd;">${storedCount}</td></tr>`;
        html += `<tr><td style="padding:8px; border:1px solid #ddd;">t_hu_master</td><td style="padding:8px; border:1px solid #ddd;">${huMasterCount}</td></tr>`;
        html += `<tr><td style="padding:8px; border:1px solid #ddd;">t_hu_detail</td><td style="padding:8px; border:1px solid #ddd;">${huDetailCount}</td></tr>`;
        html += `<tr style="background:#e2e8f0;"><td style="padding:8px; border:1px solid #ddd;"><strong>Total Items</strong></td><td style="padding:8px; border:1px solid #ddd;"><strong>${totalItems}</strong></td></tr>`;
        html += '</table>';

        if (totalItems === 0) {
            html += '<br><span style="color: orange;"> No inventory found at this location. Reset can proceed but no items need relocation.</span>';
        } else {
            html += '<br><span style="color: green;"> Inventory found. Items will need to be relocated to a temporary location.</span>';
        }

        html += `<br><br><button class="save" onclick="confirmInventoryCheck('${workspaceId}')"> Confirm & Continue</button>`;

        resultDiv.innerHTML = html;
        resultDiv.style.background = totalItems === 0 ? '#feebc8' : '#c6f6d5';
    })
    .catch(error => {
        resultDiv.innerHTML = `<span style="color: red;"> Error checking inventory: ${error}</span>`;
        resultDiv.style.background = '#fed7d7';
    });
}

function confirmInventoryCheck(workspaceId) {
    const totalItems = resetWizardState.inventoryItems.totalCount;
    showSuccessMessage(`Inventory check complete. ${totalItems} item(s) found at fork location.`);
    resetWizardState.currentStep = 4;
    loadWizardStep(workspaceId);
}


// ============ STEP 4: TEMP LOCATION (UPDATED) ============

function renderStep4TempLocation(workspaceId, container) {
    const fork = resetWizardState.forkLocation;
    const inventory = resetWizardState.inventoryItems;
    const whId = fork.wh_id;

    container.innerHTML = `
        <h5 style="margin-bottom: 16px;">Step 4: Select Temporary Staging Location</h5>
        <p>Items need to be moved from fork <strong>${fork.location_id}</strong> to a temporary staging location.</p>

        <div style="background: #f0f4f8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong> Items to relocate:</strong> ${inventory.totalCount} item(s)</p>
            <p><strong> Source Location:</strong> ${fork.location_id}</p>
            <p><strong> Warehouse:</strong> ${whId}</p>
        </div>

        <div style="margin-bottom: 16px;">
            <label>Select Temporary Staging Location:</label>
            <div style="display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; align-items: center;">
                <select id="tempLocationDropdown" style="width: 400px; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0;" onchange="onTempLocationSelect()">
                    <option value="">-- Loading available staging locations --</option>
                </select>
                <button class="test" onclick="refreshAvailableLocations('${workspaceId}')" style="padding: 8px 12px;">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
                <span style="align-self: center; color: #718096;">OR</span>
                <input type="text" id="tempLocationManual" placeholder="Enter location ID manually" style="width: 250px; padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0;" oninput="onTempLocationManualInput()">
            </div>
            <p style="font-size: 12px; color: #718096; margin-top: 8px;">
                <i class="fas fa-info-circle"></i> Showing empty/available staging locations (status E or P, type S) in warehouse ${whId}
            </p>
        </div>

        <button class="test" onclick="validateTempLocation('${workspaceId}')" style="margin-top: 10px;">  Validate Location</button>

        <div id="tempLocationResult" style="margin-top: 20px; padding: 12px; border-radius: 8px; display: none;"></div>

        <div id="impactPreview" style="margin-top: 20px; display: none;">
            <h6> Impact Preview:</h6>
            <div id="impactContent"></div>
            <button class="save" onclick="confirmTempLocation('${workspaceId}')" style="margin-top: 15px;"> Confirm Temp Location & Continue</button>
        </div>
    `;

    // Fetch available staging locations using the custom query
    fetchAvailableLocations(workspaceId, whId);
}

function fetchAvailableLocations(workspaceId, whId) {
    // Use the custom query to find available staging locations
    const query = `SELECT TOP 10 location_id, status, type, description, stored_qty
                   FROM t_location (NOLOCK)
                   WHERE wh_id = '${whId}'
                     AND (status = 'E' OR status = 'P')
                     AND type = 'S'
                     AND (description LIKE '%STAGE%' OR description LIKE '%STAGING%')
                   ORDER BY
                       status ASC,
                       ISNULL(stored_qty, 0) ASC`;

    const dropdown = document.getElementById('tempLocationDropdown');
    if (dropdown) {
        dropdown.innerHTML = '<option value="">-- Loading available locations --</option>';
    }

    fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql_query: query })
    })
    .then(response => response.json())
    .then(data => {
        const dropdown = document.getElementById('tempLocationDropdown');
        if (!dropdown) return;

        dropdown.innerHTML = '<option value="">-- Select from available staging locations --</option>';

        if (data.df && data.df.length > 0) {
            data.df.forEach(location => {
                const option = document.createElement('option');
                option.value = location.location_id;
                const storedInfo = location.stored_qty ? ` | Qty: ${location.stored_qty}` : ' | Empty';
                const statusText = location.status === 'E' ? 'Empty' : 'Partial';
                option.textContent = `${location.location_id} (${statusText}${storedInfo})`;
                dropdown.appendChild(option);
            });
            showSuccessMessage(`Found ${data.df.length} available staging location(s)`);
        } else {
            dropdown.innerHTML = '<option value="">-- No available staging locations found --</option>';
            showErrorMessage('No available staging locations found. Please check warehouse ID or try manual entry.');
        }
    })
    .catch(error => {
        console.error('Error fetching locations:', error);
        const dropdown = document.getElementById('tempLocationDropdown');
        if (dropdown) {
            dropdown.innerHTML = '<option value="">-- Error loading locations --</option>';
        }
        showErrorMessage('Failed to load available locations: ' + error.message);
    });
}

function refreshAvailableLocations(workspaceId) {
    const whId = resetWizardState.forkLocation.wh_id;
    showSuccessMessage('Refreshing available locations...');
    fetchAvailableLocations(workspaceId, whId);
}

function onTempLocationSelect() {
    const dropdown = document.getElementById('tempLocationDropdown');
    const manualInput = document.getElementById('tempLocationManual');

    if (dropdown.value) {
        manualInput.value = dropdown.value;
        manualInput.disabled = true;
    } else {
        manualInput.disabled = false;
        manualInput.value = '';
    }
}

function onTempLocationManualInput() {
    const dropdown = document.getElementById('tempLocationDropdown');
    const manualInput = document.getElementById('tempLocationManual');

    if (manualInput.value) {
        dropdown.value = '';
        dropdown.disabled = true;
    } else {
        dropdown.disabled = false;
    }
}

function validateTempLocation(workspaceId) {
    const tempLocation = document.getElementById('tempLocationManual').value.trim();
    const whId = resetWizardState.forkLocation.wh_id;

    if (!tempLocation) {
        showErrorMessage('Please enter or select a temporary location ID');
        return;
    }

    // Re-enable dropdown for next time
    document.getElementById('tempLocationDropdown').disabled = false;

    const query = `SELECT location_id, wh_id, status, type, description FROM t_location (NOLOCK) WHERE location_id = '${tempLocation}' AND wh_id = '${whId}'`;

    const resultDiv = document.getElementById('tempLocationResult');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<span class="loader"></span> Validating location...';
    resultDiv.style.background = '#ebf8ff';

    fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql_query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === 'error' || data.type === 'sql_error') {
            resultDiv.innerHTML = `<span style="color: red;"> Error: ${data.error}</span>`;
            resultDiv.style.background = '#fed7d7';
        } else if (data.df && data.df.length > 0) {
            const selectedLocation = data.df[0];

            // Check if trying to move to the same location
            if (selectedLocation.location_id === resetWizardState.forkLocation.location_id) {
                resultDiv.innerHTML = `<span style="color: orange;"> Cannot relocate to the same location (${selectedLocation.location_id}). Please choose a different location.</span>`;
                resultDiv.style.background = '#feebc8';
                document.getElementById('impactPreview').style.display = 'none';
                return;
            }

            resetWizardState.tempLocation = tempLocation;
            resultDiv.innerHTML = `<span style="color: green;"> Location '${tempLocation}' is valid (Type: ${selectedLocation.type || 'N/A'}, Status: ${selectedLocation.status || 'N/A'}).</span>`;
            resultDiv.style.background = '#c6f6d5';

            // Show impact preview
            showImpactPreview(workspaceId);
        } else {
            resultDiv.innerHTML = `<span style="color: orange;"> Location '${tempLocation}' does not exist in t_location for warehouse ${whId}. Please enter a valid location.</span>`;
            resultDiv.style.background = '#feebc8';
            document.getElementById('impactPreview').style.display = 'none';
        }
    })
    .catch(error => {
        resultDiv.innerHTML = `<span style="color: red;"> Error: ${error}</span>`;
        resultDiv.style.background = '#fed7d7';
    });
}

function showImpactPreview(workspaceId) {
    const fork = resetWizardState.forkLocation;
    const tempLoc = resetWizardState.tempLocation;
    const inventory = resetWizardState.inventoryItems;

    const impactDiv = document.getElementById('impactPreview');
    const impactContent = document.getElementById('impactContent');

    impactDiv.style.display = 'block';

    let html = '<table style="width:100%; border-collapse: collapse;">';
    html += '<tr style="background:#e2e8f0;"><th style="padding:8px; border:1px solid #ddd;">Operation</th><th style="padding:8px; border:1px solid #ddd;">From</th><th style="padding:8px; border:1px solid #ddd;">To</th><th style="padding:8px; border:1px solid #ddd;">Rows Affected</th></tr>';
    html += `<tr><td style="padding:8px; border:1px solid #ddd;">t_stored_item</td><td style="padding:8px; border:1px solid #ddd;">${fork.location_id}</td><td style="padding:8px; border:1px solid #ddd;">${tempLoc}</td><td style="padding:8px; border:1px solid #ddd;">${inventory.stored.length}</td></tr>`;
    html += `<tr><td style="padding:8px; border:1px solid #ddd;">t_hu_master</td><td style="padding:8px; border:1px solid #ddd;">${fork.location_id}</td><td style="padding:8px; border:1px solid #ddd;">${tempLoc}</td><td style="padding:8px; border:1px solid #ddd;">${inventory.huMaster.length}</td></tr>`;
    html += `<tr><td style="padding:8px; border:1px solid #ddd;">t_hu_detail</td><td style="padding:8px; border:1px solid #ddd;">${fork.location_id}</td><td style="padding:8px; border:1px solid #ddd;">${tempLoc}</td><td style="padding:8px; border:1px solid #ddd;">${inventory.huDetail.length}</td></tr>`;
    html += `<tr style="background:#e2e8f0;"><td style="padding:8px; border:1px solid #ddd;"><strong>Total</strong></td><td colspan="2"></td><td style="padding:8px; border:1px solid #ddd;"><strong>${inventory.totalCount}</strong></td></tr>`;
    html += '</table>';

    html += `<div style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 8px;">`;
    html += `<strong> Important Notes:</strong><ul style="margin: 10px 0 0 20px;">`;
    html += `<li>This operation will MOVE all inventory from <strong>${fork.location_id}</strong> to <strong>${tempLoc}</strong></li>`;
    html += `<li>The employee's device will be cleared (set to NULL)</li>`;
    html += `<li>The fork location will be reset (c1 = NULL, status = 'E')</li>`;
    html += `<li><strong>This action can be rolled back if interrupted</strong></li>`;
    html += `</ul></div>`;

    impactContent.innerHTML = html;
}

function confirmTempLocation(workspaceId) {
    if (!resetWizardState.tempLocation) {
        showErrorMessage('Please validate a temporary location first');
        return;
    }

    // Re-enable controls for next time
    document.getElementById('tempLocationDropdown').disabled = false;
    document.getElementById('tempLocationManual').disabled = false;

    showSuccessMessage(`Temporary location confirmed: ${resetWizardState.tempLocation}`);
    resetWizardState.currentStep = 5;
    loadWizardStep(workspaceId);
}

// ============ STEP 5: FINAL CONFIRMATION ============

function renderStep5ConfirmRelocation(workspaceId, container) {
    const fork = resetWizardState.forkLocation;
    const tempLoc = resetWizardState.tempLocation;
    const employee = resetWizardState.employeeData;
    const inventory = resetWizardState.inventoryItems;

    container.innerHTML = `
        <h5 style="margin-bottom: 16px;">Step 5: Final Confirmation</h5>

        <div style="background: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h6 style="color: #856404; margin-bottom: 15px;"><i class="fas fa-exclamation-triangle"></i> PRODUCTION ACTION WARNING</h6>
            <p>You are about to execute a <strong>production reset operation</strong> that will:</p>
            <ul style="margin: 15px 0 0 25px;">
                <li>Move <strong>${inventory.totalCount}</strong> item(s) from <strong>${fork.location_id}</strong> → <strong>${tempLoc}</strong></li>
                <li>Clear device assignment for employee: <strong>${employee.name || employee.id}</strong></li>
                <li>Reset fork location status to empty (status = 'E')</li>
                <li>Clear employee assignment from fork (c1 = NULL)</li>
            </ul>
        </div>

        <div style="background: #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong><i class="fas fa-clipboard-list"></i> Execution Summary:</strong></p>
            <ul style="margin: 10px 0 0 20px;">
                <li><strong>TX1</strong> - Relocate inventory (${inventory.totalCount} items) to ${tempLoc}</li>
                <li><strong>TX2</strong> - Logout employee & clear fork location</li>
                <li><strong>Post-validation</strong> - Checks will run automatically</li>
                <li><strong>Audit logs</strong> - Will be recorded for compliance</li>
            </ul>
        </div>

        <div style="background: #fed7d7; border: 1px solid #f56565; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong><i class="fas fa-undo-alt"></i> Rollback Information:</strong></p>
            <p>If any step fails or is interrupted, <strong>ALL database changes will be automatically rolled back</strong> to maintain data integrity.</p>
            <p style="margin-top: 8px;">The wizard will return to Step 1 and you can restart the process.</p>
        </div>

        <div style="background: #c6f6d5; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong><i class="fas fa-check-circle"></i> Pre-execution Validation:</strong></p>
            <ul style="margin: 10px 0 0 20px;">
                <li> Employee: ${employee.name || employee.id} (Device: ${employee.device || 'N/A'})</li>
                <li> Source Fork: ${fork.location_id}</li>
                <li> Target Location: ${tempLoc}</li>
                <li> Items to relocate: ${inventory.totalCount}</li>
            </ul>
        </div>

        <div style="display: flex; gap: 15px; justify-content: center; margin-top: 20px;">
            <button class="test" onclick="abortResetWizard()" style="background: #f56565; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer;">
                <i class="fas fa-times"></i> Cancel Reset
            </button>
            <button class="save" onclick="executeResetOperation('${workspaceId}')" style="background: #48bb78; padding: 12px 24px; border-radius: 8px; cursor: pointer; color:#f0f0f0 ; border-color: #48bb78;">
                <i class="fas fa-play"></i> Execute Reset & Continue
            </button>
        </div>
    `;
}

// ============ STEP 6: EXECUTE RELOCATION (TX1) ============

function renderStep6ExecuteRelocation(workspaceId, container) {
    const fork = resetWizardState.forkLocation;
    const tempLoc = resetWizardState.tempLocation;
    const inventory = resetWizardState.inventoryItems;

    container.innerHTML = `
        <h5 style="margin-bottom: 16px;">Step 6: Executing Inventory Relocation (TX1)</h5>

        <div style="background: #f0f4f8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong> Relocation Details:</strong></p>
            <ul style="margin: 10px 0 0 20px;">
                <li>Source Location: <strong>${fork.location_id}</strong></li>
                <li>Target Location: <strong>${tempLoc}</strong></li>
                <li>Warehouse: <strong>${fork.wh_id}</strong></li>
                <li>Items to relocate: <strong>${inventory.totalCount}</strong></li>
            </ul>
        </div>

        <div id="tx1Progress" style="margin-top: 20px;">
            <div id="tx1Status" style="padding: 12px; border-radius: 8px; margin-bottom: 10px; background: #ebf8ff;">
                 Ready to execute relocation...
            </div>
        </div>

        <div style="display: flex; gap: 15px; justify-content: center; margin-top: 20px;">
            <button class="test" onclick="abortResetWizard()" style="background: #f56565; color: white; border: none; padding: 12px 24px;">
                <i class="fas fa-times"></i> Abort & Rollback
            </button>
            <button class="save" onclick="executeRelocation('${workspaceId}')" style="background: #48bb78; padding: 12px 24px; color : #ffff; border-color: #48bb78;">
                <i class="fas fa-arrow-right"></i> Execute Relocation
            </button>
        </div>
    `;
}

function executeRelocation(workspaceId) {
    const fork = resetWizardState.forkLocation;
    const tempLoc = resetWizardState.tempLocation;
    const whId = fork.wh_id;
    const sourceLoc = fork.location_id;

    const statusDiv = document.getElementById('tx1Status');
    statusDiv.innerHTML = ' Relocating inventory...';
    statusDiv.style.background = '#fefcbf';

    // Single atomic call: backend updates t_stored_item, t_hu_master and t_hu_detail
    // together in one transaction (all rolled back together on failure).
    fetch(`/api/v0/reset_wizard/relocate?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            workspace_id: workspaceId,
            wh_id: whId,
            source_location_id: sourceLoc,
            dest_location_id: tempLoc
        })
    })
        .then(res => res.json())
        .then(result => {
            if (result.type === 'error') {
                throw new Error(result.error || 'Relocation failed');
            }

            statusDiv.innerHTML = '<span style="color: green;"> Relocation completed successfully!</span>';
            statusDiv.style.background = '#c6f6d5';
            resetWizardState.relocationExecuted = true;

            showSuccessMessage(`Inventory relocation completed! Moved ${resetWizardState.inventoryItems.totalCount} item(s) to ${tempLoc}`);

            // Auto-advance to Step 7 after 1.5 seconds
            setTimeout(() => {
                resetWizardState.currentStep = 7;
                loadWizardStep(workspaceId);
            }, 1500);
        })
        .catch(error => {
            statusDiv.innerHTML = `<span style="color: red;"> Error during relocation: ${error.message}</span>`;
            statusDiv.style.background = '#fed7d7';
            showErrorMessage('Relocation failed: ' + error.message);

            // Show rollback button
            const buttonContainer = document.querySelector('#wizardContent > div:last-child');
            if (buttonContainer && !document.getElementById('rollbackBtn')) {
                const rollbackBtn = document.createElement('button');
                rollbackBtn.id = 'rollbackBtn';
                rollbackBtn.className = 'test';
                rollbackBtn.style.cssText = 'background: #ed8936; color: white; margin-top: 10px; margin-left: 10px;';
                rollbackBtn.innerHTML = '<i class="fas fa-undo-alt"></i> Rollback Changes';
                rollbackBtn.onclick = () => rollbackRelocation(workspaceId);
                buttonContainer.appendChild(rollbackBtn);
            }
        });
}


function rollbackRelocation(workspaceId) {
    const fork = resetWizardState.forkLocation;
    const tempLoc = resetWizardState.tempLocation;
    const whId = fork.wh_id;
    const sourceLoc = fork.location_id;

    const statusDiv = document.getElementById('tx1Status');
    statusDiv.innerHTML = ' Rolling back changes...';
    statusDiv.style.background = '#feebc8';

    // Rollback = relocate everything back from the temp location to the source location,
    // as a single atomic call (same endpoint, source/dest swapped).
    fetch(`/api/v0/reset_wizard/relocate?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            workspace_id: workspaceId,
            wh_id: whId,
            source_location_id: tempLoc,
            dest_location_id: sourceLoc
        })
    })
        .then(res => res.json())
        .then(result => {
            if (result.type === 'error') {
                throw new Error(result.error || 'Rollback failed');
            }
        })
    .then(() => {
        statusDiv.innerHTML = '<span style="color: green;"> Rollback completed! No changes were committed.</span>';
        statusDiv.style.background = '#c6f6d5';
        showSuccessMessage('Rollback successful. Returning to Step 1.');

        setTimeout(() => {
            resetWizardState = {
                currentStep: 1,
                totalSteps: 7,
                employeeData: null,
                forkLocation: null,
                inventoryItems: null,
                tempLocation: null,
                relocationExecuted: false,
                logoutExecuted: false
            };
            loadWizardStep(workspaceId);
        }, 2000);
    })
    .catch(error => {
        statusDiv.innerHTML = `<span style="color: red;"> Rollback error: ${error.message}. Manual intervention may be required.</span>`;
        statusDiv.style.background = '#fed7d7';
        showErrorMessage('Rollback failed: ' + error.message);
    });
}

// ============ STEP 7: LOGOUT & CLEAR (TX2) ============

function renderStep7LogoutAndClear(workspaceId, container) {
    const employee = resetWizardState.employeeData;
    const fork = resetWizardState.forkLocation;
    const whId = fork.wh_id;

    container.innerHTML = `
        <h5 style="margin-bottom: 16px;">Step 7: Logout & Clear Device (TX2)</h5>

        <div style="background: #f0f4f8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong> Cleanup Details:</strong></p>
            <ul style="margin: 10px 0 0 20px;">
                <li>Employee: <strong>${employee.name || employee.id}</strong></li>
                <li>Current Device: <strong>${employee.device || 'N/A'}</strong></li>
                <li>Fork Location: <strong>${fork.location_id}</strong></li>
                <li>Warehouse: <strong>${whId}</strong></li>
            </ul>
        </div>

        <div id="tx2Progress" style="margin-top: 20px;">
            <div id="tx2Status" style="padding: 12px; border-radius: 8px; margin-bottom: 10px; background: #ebf8ff;">
                 Ready to execute logout and clear...
            </div>
        </div>

        <div style="display: flex; gap: 15px; justify-content: center; margin-top: 20px;">
            <button class="test" onclick="rollbackRelocation('${workspaceId}')" style="background: #ed8936; color: white; border: none; padding: 12px 24px;">
                <i class="fas fa-undo-alt"></i> Rollback Relocation
            </button>
            <button class="save" onclick="executeLogoutAndClear('${workspaceId}')" style="background: #48bb78; padding: 12px 24px;  color:#ffff ; border-color: #48bb78;">
                <i class="fas fa-check-circle"></i> Execute Logout & Clear
            </button>
        </div>
    `;
}

function executeLogoutAndClear(workspaceId) {
    const employee = resetWizardState.employeeData;
    const fork = resetWizardState.forkLocation;
    const whId = fork.wh_id;
    const deviceId = employee.device || '';

    const statusDiv = document.getElementById('tx2Status');
    statusDiv.innerHTML = ' Clearing employee device...';
    statusDiv.style.background = '#fefcbf';

    // Single atomic call: backend clears t_employee.device and resets t_location
    // status together in one transaction.
    fetch(`/api/v0/reset_wizard/logout_clear?workspace_id=${workspaceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            workspace_id: workspaceId,
            wh_id: whId,
            employee_id: employee.id,
            location_id: fork.location_id
        })
    })
        .then(res => res.json())
        .then(result => {
            const failed = result.type === 'error' ? [result] : [];
            if (failed.length > 0) {
                throw new Error(`${failed.length} update(s) failed: ${failed.map(f => f.error).join(', ')}`);
            }

            statusDiv.innerHTML = '<span style="color: green;"> Logout and clear completed successfully!</span>';
            statusDiv.style.background = '#c6f6d5';
            resetWizardState.logoutExecuted = true;

            showSuccessMessage('Device reset completed! Running post-validation...');

            // Run post-validation
            setTimeout(() => {
                runPostValidation(workspaceId);
            }, 1000);
        })
        .catch(error => {
            statusDiv.innerHTML = `<span style="color: red;"> Error during logout: ${error.message}</span>`;
            statusDiv.style.background = '#fed7d7';
            showErrorMessage('Logout failed: ' + error.message);
        });
}

// ============ POST-VALIDATION ============

function runPostValidation(workspaceId) {
    const employee = resetWizardState.employeeData;
    const fork = resetWizardState.forkLocation;
    const tempLoc = resetWizardState.tempLocation;
    const whId = fork.wh_id;

    const container = document.getElementById('wizardContent');

    // Validation queries
    const checkEmployee = `SELECT id, device FROM t_employee WHERE id = '${employee.id}' AND wh_id = '${whId}'`;
    const checkFork = `SELECT location_id, c1, status FROM t_location WHERE location_id = '${fork.location_id}' AND wh_id = '${whId}'`;
    const checkOldLocationEmpty = `SELECT COUNT(*) as item_count FROM t_stored_item WHERE location_id = '${fork.location_id}' AND wh_id = '${whId}'`;

    container.innerHTML = `
        <h5 style="margin-bottom: 16px;">Post-Validation Check</h5>
        <div id="validationProgress" style="padding: 12px; border-radius: 8px; background: #ebf8ff;">
             Validating reset operation...
        </div>
    `;

    Promise.all([
        fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql_query: checkEmployee })
        }),
        fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql_query: checkFork })
        }),
        fetch(`/api/v0/test_sql_query?workspace_id=${workspaceId}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql_query: checkOldLocationEmpty })
        })
    ])
    .then(responses => Promise.all(responses.map(r => r.json())))
    .then(([empData, forkData, oldLocData]) => {
        let validationHtml = '<h6> Validation Results:</h6><ul style="margin-top: 10px;">';
        let allValid = true;

        // Check employee device cleared
        const employeeDevice = empData.df && empData.df[0] ? empData.df[0].device : null;
        if (!employeeDevice || employeeDevice === 'NULL' || employeeDevice === null) {
            validationHtml += '<li style="color: green;">✓ Employee device cleared successfully</li>';
        } else {
            validationHtml += '<li style="color: red;">✗ Employee device still has value: ' + employeeDevice + '</li>';
            allValid = false;
        }

        // Check fork location cleared
        const forkC1 = forkData.df && forkData.df[0] ? forkData.df[0].c1 : null;
        const forkStatus = forkData.df && forkData.df[0] ? forkData.df[0].status : null;
        if ((!forkC1 || forkC1 === 'NULL' || forkC1 === null) && forkStatus === 'E') {
            validationHtml += '<li style="color: green;">✓ Fork location cleared (c1 = NULL, status = E)</li>';
        } else {
            validationHtml += '<li style="color: orange;"> Fork location: c1=' + (forkC1 || 'NULL') + ', status=' + (forkStatus || 'N/A') + '</li>';
            allValid = false;
        }

        // Check old location has no inventory
        const itemCount = oldLocData.df && oldLocData.df[0] ? oldLocData.df[0].item_count : 0;
        if (itemCount === 0) {
            validationHtml += '<li style="color: green;">✓ Source location is empty (0 items)</li>';
        } else {
            validationHtml += '<li style="color: orange;"> Source location still has ' + itemCount + ' item(s)</li>';
            allValid = false;
        }

        validationHtml += `</ul><hr><p><strong>Items relocated to:</strong> ${tempLoc}</p>`;

        if (allValid) {
            validationHtml += `<div style="background: #c6f6d5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <strong> Device Reset Complete!</strong><br>
                The RMF device has been successfully reset. Employee ${employee.id} is logged out and the fork location is ready for reassignment.
            </div>`;
        } else {
            validationHtml += `<div style="background: #feebc8; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <strong> Partial Issues Detected</strong><br>
                Some validation checks did not pass. Please review the results above and contact system administrator if needed.
            </div>`;
        }

        validationHtml += `<div style="margin-top: 20px; text-align: center;">
            <button class="save" onclick="resetWizardComplete()">Start New Reset</button>
        </div>`;

        document.getElementById('validationProgress').innerHTML = validationHtml;
        document.getElementById('validationProgress').style.background = '#f0f4f8';
    })
    .catch(error => {
        document.getElementById('validationProgress').innerHTML = `
            <span style="color: red;"> Validation error: ${error.message}</span>
            <div style="margin-top: 20px; text-align: center;">
                <button class="save" onclick="resetWizardComplete()">Return to Start</button>
            </div>
        `;
    });
}

function resetWizardComplete() {
    resetWizardState = {
        currentStep: 1,
        totalSteps: 7,
        employeeData: null,
        forkLocation: null,
        inventoryItems: null,
        tempLocation: null,
        relocationExecuted: false,
        logoutExecuted: false
    };
    const workspaceId = document.getElementById('workspaceId').value;
    loadWizardStep(workspaceId);
    showSuccessMessage('Ready for next device reset!');
}

// Update the executeResetOperation function
function executeResetOperation(workspaceId) {
    // Move to Step 6
    resetWizardState.currentStep = 6;
    loadWizardStep(workspaceId);
}

// ============ AUTOMATED DEVICE RESET LOGS ============

function showDeviceResetLogs(workspaceId) {
    const contentArea = document.getElementById('contentArea');
    contentArea.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div>
                <h4 style="margin: 0 0 4px;">Automated Device Reset Logs</h4>
                <p style="margin: 0; color: #718096; font-size: 14px;">Activity log for the automated device reset job. The job scans for stuck RMF/forklift devices and resets them every 2 hours.</p>
            </div>
        </div>

        <div style="display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; align-items: center;">
            <button class="test" onclick="showResetDevicesAgent('${workspaceId}')">Back to Manual Reset</button>
            <button class="test" onclick="loadDeviceResetLogs('${workspaceId}')">Refresh</button>
            <button class="save" onclick="downloadDeviceResetLogs('csv')">Download CSV</button>
            <button class="save" onclick="downloadDeviceResetLogs('txt')">Download TXT</button>
            <span id="deviceResetLogMeta" style="margin-left: auto; font-size: 12px; color: #718096;"></span>
        </div>

        <div id="deviceResetLogContainer" style="background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: auto; max-height: 70vh;">
            <div style="padding: 24px; text-align: center; color: #718096;">Loading logs...</div>
        </div>
    `;
    contentArea.style.display = 'block';
    loadDeviceResetLogs(workspaceId);
}

function loadDeviceResetLogs(workspaceId) {
    const container = document.getElementById('deviceResetLogContainer');
    if (!container) return;
    container.innerHTML = '<div style="padding: 24px; text-align: center; color: #718096;">Loading logs...</div>';

    fetch('/api/v0/device_reset_logs')
        .then(r => r.json())
        .then(data => {
            const logs = data.logs || [];
            const meta = document.getElementById('deviceResetLogMeta');
            if (meta) meta.textContent = `${logs.length} total entries`;
            if (logs.length === 0) {
                container.innerHTML = '<div style="padding: 32px; text-align: center; color: #718096;">No log entries recorded. The automated job has not run yet or no devices have been processed.</div>';
                return;
            }
            renderDeviceResetLogs(logs, container);
        })
        .catch(err => {
            container.innerHTML = '<div style="padding: 24px; text-align: center; color: #e53e3e;">Failed to load logs: ' + err.message + '</div>';
        });
}

function renderDeviceResetLogs(logs, container) {
    // Group entries by run_id, preserving insertion order
    const runs = {};
    const runOrder = [];
    for (const entry of logs) {
        const rid = entry.run_id || 'Unknown Run';
        if (!runs[rid]) {
            runs[rid] = [];
            runOrder.push(rid);
        }
        runs[rid].push(entry);
    }

    let html = '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">';
    html += '<thead><tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0; position: sticky; top: 0;">';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; font-weight: 600; width: 200px;">Timestamp</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; font-weight: 600; width: 90px;">Level</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; font-weight: 600; width: 120px;">Device ID</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; font-weight: 600;">Message</th>';
    html += '</tr></thead><tbody>';

    // Display newest runs first
    for (const rid of [...runOrder].reverse()) {
        const entries = runs[rid];
        const hasError   = entries.some(e => e.level === 'ERROR');
        const hasWarning = entries.some(e => e.level === 'WARNING');
        const runStatus      = hasError ? 'ERROR' : (hasWarning ? 'WARNING' : 'COMPLETED');
        const runStatusColor = hasError ? '#e53e3e' : (hasWarning ? '#d69e2e' : '#38a169');

        html += '<tr style="background: #f0f4f8;">';
        html += '<td colspan="4" style="padding: 8px 14px; font-size: 12px; font-weight: 600; color: #2d3748; border-bottom: 1px solid #e2e8f0;">';
        html += 'Run: ' + rid;
        html += ' <span style="margin-left: 8px; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: white; background: ' + runStatusColor + ';">' + runStatus + '</span>';
        html += ' <span style="margin-left: 8px; color: #718096; font-weight: 400;">' + entries.length + ' event(s)</span>';
        html += '</td></tr>';

        for (const e of entries) {
            const rowBg       = e.level === 'ERROR'   ? '#fff5f5' : (e.level === 'WARNING' ? '#fffbeb' : 'white');
            const levelColor  = e.level === 'ERROR'   ? '#c53030' : (e.level === 'WARNING' ? '#b7791f' : '#276749');
            html += '<tr style="background: ' + rowBg + '; border-bottom: 1px solid #edf2f7;">';
            html += '<td style="padding: 8px 14px; color: #4a5568; white-space: nowrap; font-size: 12px;">' + e.timestamp + '</td>';
            html += '<td style="padding: 8px 14px; font-weight: 600; color: ' + levelColor + '; font-size: 12px;">' + e.level + '</td>';
            html += '<td style="padding: 8px 14px; color: #4a5568; font-family: monospace; font-size: 12px;">' + (e.device_id || '') + '</td>';
            html += '<td style="padding: 8px 14px; color: #2d3748;">' + e.message + '</td>';
            html += '</tr>';
        }
    }

    html += '</tbody></table>';
    container.innerHTML = html;
}

function downloadDeviceResetLogs(format) {
    window.location.href = '/api/v0/device_reset_logs/download?format=' + format;
}


// ============================================================
// UNPICK AGENT
// ============================================================

function unpickToast(message, type) {
    const colors = {
        success: 'linear-gradient(to right, #38a169, #48bb78)',
        error:   'linear-gradient(to right, #e53e3e, #fc8181)',
        warning: 'linear-gradient(to right, #d69e2e, #ecc94b)',
        info:    'linear-gradient(to right, #3182ce, #63b3ed)'
    };
    Toastify({
        text: message,
        duration: type === 'error' ? 5000 : 3000,
        gravity: 'top',
        position: 'center',
        style: { background: colors[type] || colors.info, borderRadius: '8px', fontSize: '14px' },
        stopOnFocus: true
    }).showToast();
}

function unpickConfirm(message, onConfirm) {
    const existing = document.getElementById('unpickConfirmOverlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'unpickConfirmOverlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.45);z-index:9999;display:flex;align-items:center;justify-content:center;';

    overlay.innerHTML = `
        <div style="background:white;border-radius:12px;padding:28px 32px;max-width:420px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
            <p style="margin:0 0 20px;font-size:15px;color:#2d3748;line-height:1.5;">${message}</p>
            <div style="display:flex;justify-content:flex-end;gap:10px;">
                <button id="unpickConfirmNo"  style="padding:8px 20px;border:1px solid #e2e8f0;border-radius:6px;background:white;color:#4a5568;cursor:pointer;font-size:14px;">Cancel</button>
                <button id="unpickConfirmYes" style="padding:8px 20px;border:none;border-radius:6px;background:#7B83EB;color:white;cursor:pointer;font-size:14px;font-weight:600;">Confirm</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById('unpickConfirmYes').onclick = () => { overlay.remove(); onConfirm(); };
    document.getElementById('unpickConfirmNo').onclick  = () => overlay.remove();
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
}

// Global state for the unpick agent
var unpickAgentState = {
    workspaceId: null,
    autoScanRecords: [],      // records returned by auto-scan
    manualRecords: [],        // records added manually or via CSV
    activeTab: 'auto',        // 'auto' | 'manual' | 'logs'
    lastResults: []           // results of last execute run
};

function showUnpickAgent(workspaceId) {
    unpickAgentState.workspaceId = workspaceId;
    unpickAgentState.autoScanRecords = [];
    unpickAgentState.manualRecords = [];
    unpickAgentState.lastResults = [];

    const contentArea = document.getElementById('contentArea');
    contentArea.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div>
                <h4 style="margin: 0 0 4px;">Unpick Agent</h4>
                <p style="margin: 0; color: #718096; font-size: 14px;">Safely revert stuck unpick transactions across t_pick_detail, t_stored_item, t_hu_master, t_hu_detail, and t_work_q. Each record is processed in an atomic transaction.</p>
            </div>
        </div>
        <input type="hidden" id="unpickWorkspaceId" value="${workspaceId}">

        <!-- Tabs -->
        <div style="display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0;">
            <button id="unpickTab_auto"    onclick="switchUnpickTab('auto')"    style="padding: 8px 20px; border: none; border-bottom: 3px solid #7B83EB; background: none; font-weight: 600; color: #7B83EB; cursor: pointer;">Auto-Scan</button>
            <button id="unpickTab_manual"  onclick="switchUnpickTab('manual')"  style="padding: 8px 20px; border: none; border-bottom: 3px solid transparent; background: none; color: #718096; cursor: pointer;">Manual Input</button>
            <button id="unpickTab_partial" onclick="switchUnpickTab('partial')" style="padding: 8px 20px; border: none; border-bottom: 3px solid transparent; background: none; color: #718096; cursor: pointer;">Partial Unpick</button>
            <button id="unpickTab_logs"    onclick="switchUnpickTab('logs')"    style="padding: 8px 20px; border: none; border-bottom: 3px solid transparent; background: none; color: #718096; cursor: pointer;">Log Viewer</button>
        </div>

        <!-- Tab panels -->
        <div id="unpickPanel_auto"    style="display: block;"></div>
        <div id="unpickPanel_manual"  style="display: none;"></div>
        <div id="unpickPanel_partial" style="display: none;"></div>
        <div id="unpickPanel_logs"    style="display: none;"></div>
    `;
    contentArea.style.display = 'block';

    renderUnpickAutoTab(workspaceId);
    renderUnpickManualTab(workspaceId);
    renderUnpickPartialTab(workspaceId);
    renderUnpickLogsPanel(workspaceId);
}

function switchUnpickTab(tab) {
    ['auto', 'manual', 'partial', 'logs'].forEach(t => {
        const btn   = document.getElementById('unpickTab_' + t);
        const panel = document.getElementById('unpickPanel_' + t);
        const active = (t === tab);
        if (btn)   { btn.style.borderBottom = active ? '3px solid #7B83EB' : '3px solid transparent'; btn.style.color = active ? '#7B83EB' : '#718096'; btn.style.fontWeight = active ? '600' : '400'; }
        if (panel) panel.style.display = active ? 'block' : 'none';
    });
    unpickAgentState.activeTab = tab;
    if (tab === 'logs') loadUnpickLogs(unpickAgentState.workspaceId);
}

// ── AUTO-SCAN TAB ────────────────────────────────────────────

function renderUnpickAutoTab(workspaceId) {
    const panel = document.getElementById('unpickPanel_auto');
    panel.innerHTML = `
        <!-- Scheduler Control Card -->
        <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <div>
                    <h5 style="margin: 0 0 3px;">Background Scheduler</h5>
                    <p style="margin: 0; color: #718096; font-size: 13px;">Runs the detection query automatically on a schedule. Each dirty record is processed in its own atomic transaction.</p>
                </div>
                <button class="test" onclick="loadUnpickSchedulerStatus()" style="white-space: nowrap;">Refresh Status</button>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px;">
                <div style="background: #f7fafc; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 12px; color: #718096; margin-bottom: 4px;">STATUS</div>
                    <div id="unpickSchedulerStatusBadge" style="font-size: 15px; font-weight: 600;">Loading...</div>
                    <button id="unpickSchedulerToggleBtn" onclick="toggleUnpickScheduler()" class="save" style="margin-top: 10px; padding: 6px 16px; font-size: 13px;">...</button>
                </div>
                <div style="background: #f7fafc; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 12px; color: #718096; margin-bottom: 4px;">NEXT RUN</div>
                    <div id="unpickSchedulerNextRun" style="font-size: 14px; font-weight: 500;">—</div>
                </div>
            </div>

            <div style="background: #f7fafc; border-radius: 8px; padding: 14px; display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 12px; color: #718096; white-space: nowrap;">RUN EVERY</div>
                <input type="number" id="unpickIntervalInput" min="0.25" max="168" step="0.25" value="2" style="width: 80px; padding: 6px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px;">
                <span style="font-size: 14px; color: #4a5568;">hours</span>
                <button class="save" onclick="updateUnpickSchedulerInterval()" style="padding: 6px 16px; font-size: 13px;">Apply</button>
                <span id="unpickIntervalMsg" style="font-size: 12px; color: #718096;"></span>
            </div>
        </div>

        <!-- On-Demand Scan Card -->
        <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 16px;">
            <h5 style="margin: 0 0 8px;">On-Demand Scan</h5>
            <p style="margin: 0 0 12px; color: #4a5568;">Run an immediate scan outside the scheduled window. Select which records to fix before executing.</p>
            <button class="save" onclick="runUnpickAutoScan('${workspaceId}')">Run Auto-Scan</button>
            <span id="unpickScanStatus" style="margin-left: 12px; font-size: 13px; color: #718096;"></span>
        </div>

        <div id="unpickScanResults" style="display: none;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong id="unpickScanCount"></strong>
                <div style="display: flex; gap: 8px;">
                    <button class="test" onclick="selectAllUnpickScan(true)">Select All</button>
                    <button class="test" onclick="selectAllUnpickScan(false)">Deselect All</button>
                    <button class="save" onclick="executeUnpickFromScan('${workspaceId}')">Execute Unpick</button>
                </div>
            </div>
            <div id="unpickScanTable" style="background: white; border-radius: 8px; border: 1px solid #e2e8f0; overflow: auto; max-height: 55vh;"></div>
        </div>

        <div id="unpickAutoResults" style="display: none; margin-top: 20px;">
            <h5 style="margin: 0 0 10px;">Execution Results</h5>
            <div id="unpickAutoResultsTable"></div>
            <div style="margin-top: 12px; display: flex; gap: 8px;">
                <button class="save" onclick="downloadUnpickResults('auto')">Download CSV</button>
            </div>
        </div>
    `;
    loadUnpickSchedulerStatus();
}

function loadUnpickSchedulerStatus() {
    fetch('/api/v0/unpick_agent/scheduler_status')
        .then(r => r.json())
        .then(data => {
            const badge     = document.getElementById('unpickSchedulerStatusBadge');
            const toggleBtn = document.getElementById('unpickSchedulerToggleBtn');
            const nextRun   = document.getElementById('unpickSchedulerNextRun');
            const interval  = document.getElementById('unpickIntervalInput');
            if (!badge) return;
            if (data.paused) {
                badge.innerHTML = '<span style="color:#718096;">&#9675; Paused</span>';
                toggleBtn.textContent = 'Enable';
                toggleBtn.className = 'save';
                toggleBtn.style.background = '';
            } else {
                badge.innerHTML = '<span style="color:#38a169;">&#9679; Running</span>';
                toggleBtn.textContent = 'Disable';
                toggleBtn.className = 'test';
                toggleBtn.style.background = '';
            }
            nextRun.textContent = data.next_run || '—';
            if (interval && data.interval_hours != null) interval.value = data.interval_hours;
        })
        .catch(() => { const b = document.getElementById('unpickSchedulerStatusBadge'); if (b) b.textContent = 'Error loading status'; });
}

function toggleUnpickScheduler() {
    fetch('/api/v0/unpick_agent/scheduler_toggle', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
        .then(r => r.json())
        .then(data => {
            if (data.type === 'error') { unpickToast('Error: ' + data.error, 'error'); return; }
            unpickToast('Scheduler ' + data.action, data.action === 'paused' ? 'warning' : 'success');
            loadUnpickSchedulerStatus();
        })
        .catch(() => unpickToast('Failed to toggle scheduler', 'error'));
}

function updateUnpickSchedulerInterval() {
    const hours = parseFloat(document.getElementById('unpickIntervalInput').value);
    if (isNaN(hours) || hours < 0.25 || hours > 168) { unpickToast('Enter a value between 0.25 and 168 hours', 'warning'); return; }
    const msg = document.getElementById('unpickIntervalMsg');
    if (msg) msg.textContent = 'Updating...';
    fetch('/api/v0/unpick_agent/scheduler_interval', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hours })
    })
    .then(r => r.json())
    .then(data => {
        if (data.type === 'error') { unpickToast('Error: ' + data.error, 'error'); if (msg) msg.textContent = ''; return; }
        unpickToast('Interval updated to ' + hours + ' hour(s)', 'success');
        if (msg) msg.textContent = 'Updated';
        loadUnpickSchedulerStatus();
    })
    .catch(() => { unpickToast('Failed to update interval', 'error'); if (msg) msg.textContent = ''; });
}

function runUnpickAutoScan(workspaceId) {
    const statusEl = document.getElementById('unpickScanStatus');
    const resultsDiv = document.getElementById('unpickScanResults');
    statusEl.textContent = 'Scanning...';
    resultsDiv.style.display = 'none';

    fetch('/api/v0/unpick_agent/auto_scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.type === 'error') {
            statusEl.textContent = 'Error: ' + data.error;
            statusEl.style.color = '#e53e3e';
            return;
        }
        unpickAgentState.autoScanRecords = data.records || [];
        const count = unpickAgentState.autoScanRecords.length;
        statusEl.textContent = `Scan complete — ${count} record(s) found.`;
        statusEl.style.color = count > 0 ? '#2d3748' : '#38a169';
        document.getElementById('unpickScanCount').textContent = count + ' record(s) require unpick:';
        renderUnpickScanTable(unpickAgentState.autoScanRecords);
        resultsDiv.style.display = 'block';
    })
    .catch(err => {
        statusEl.textContent = 'Error: ' + err.message;
        statusEl.style.color = '#e53e3e';
    });
}

function renderUnpickScanTable(records) {
    const container = document.getElementById('unpickScanTable');
    if (!records.length) {
        container.innerHTML = '<div style="padding: 24px; text-align: center; color: #38a169;">No records found — all pick records are in a clean state.</div>';
        return;
    }
    let html = '<table style="width:100%; border-collapse: collapse; font-size: 13px;">';
    html += '<thead><tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;">';
    html += '<th style="padding: 10px 14px; width: 40px;"><input type="checkbox" id="unpickSelectAllChk" onchange="selectAllUnpickScan(this.checked)" checked></th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">#</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Order Number</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">WH ID</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Item Number</th>';
    html += '</tr></thead><tbody>';
    records.forEach((r, i) => {
        html += `<tr style="border-bottom: 1px solid #edf2f7; background: ${i % 2 === 0 ? 'white' : '#f9fafb'};">`;
        html += `<td style="padding: 8px 14px; text-align: center;"><input type="checkbox" class="unpickScanChk" data-index="${i}" checked></td>`;
        html += `<td style="padding: 8px 14px; color: #718096;">${i + 1}</td>`;
        html += `<td style="padding: 8px 14px; font-family: monospace;">${r.order_number}</td>`;
        html += `<td style="padding: 8px 14px;">${r.wh_id}</td>`;
        html += `<td style="padding: 8px 14px; font-family: monospace;">${r.item_number}</td>`;
        html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

function selectAllUnpickScan(checked) {
    document.querySelectorAll('.unpickScanChk').forEach(chk => chk.checked = checked);
    const masterChk = document.getElementById('unpickSelectAllChk');
    if (masterChk) masterChk.checked = checked;
}

function executeUnpickFromScan(workspaceId) {
    const checks = document.querySelectorAll('.unpickScanChk');
    const selected = [];
    checks.forEach(chk => {
        if (chk.checked) {
            const idx = parseInt(chk.dataset.index);
            selected.push(unpickAgentState.autoScanRecords[idx]);
        }
    });
    if (!selected.length) { unpickToast('Please select at least one record.', 'warning'); return; }
    unpickConfirm(`Execute unpick for <strong>${selected.length}</strong> record(s)? This will update the database and cannot be undone.`, () => {
        executeUnpickRecords(workspaceId, selected, 'auto');
    });
}

// ── MANUAL INPUT TAB ─────────────────────────────────────────

function renderUnpickManualTab(workspaceId) {
    const panel = document.getElementById('unpickPanel_manual');
    panel.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 16px;">
            <h5 style="margin: 0 0 14px;">Add Records Manually</h5>
            <div style="display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap;">
                <div>
                    <label style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 4px;">WH ID</label>
                    <input type="text" id="unpickManualWhId" placeholder="e.g. WH01" style="width: 100px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px;">
                </div>
                <div>
                    <label style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 4px;">Order Number</label>
                    <input type="text" id="unpickManualOrderNum" placeholder="e.g. ORD-10001" style="width: 180px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px;">
                </div>
                <div>
                    <label style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 4px;">Item Number</label>
                    <input type="text" id="unpickManualItemNum" placeholder="e.g. ITEM-999" style="width: 160px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px;">
                </div>
                <button class="test" onclick="addUnpickManualRow()">+ Add Row</button>
            </div>
        </div>

        <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 16px;">
            <h5 style="margin: 0 0 10px;">CSV Import</h5>
            <p style="font-size: 13px; color: #718096; margin: 0 0 10px;">Paste CSV with header row: <code>wh_id,order_number,item_number</code></p>
            <textarea id="unpickCsvPaste" rows="5" placeholder="wh_id,order_number,item_number&#10;WH01,ORD-10001,ITEM-999&#10;WH01,ORD-10002,ITEM-888" style="width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-family: monospace; font-size: 12px; box-sizing: border-box;"></textarea>
            <div style="margin-top: 8px; display: flex; gap: 8px; align-items: center;">
                <button class="test" onclick="parseUnpickCsvPaste()">Import Pasted CSV</button>
                <span style="color: #718096; font-size: 13px;">or</span>
                <label style="cursor: pointer; padding: 7px 14px; background: #edf2f7; border-radius: 6px; font-size: 13px;">
                    Upload CSV File <input type="file" id="unpickCsvFile" accept=".csv" style="display: none;" onchange="parseUnpickCsvFile()">
                </label>
            </div>
            <div id="unpickCsvImportMsg" style="margin-top: 8px; font-size: 13px;"></div>
        </div>

        <!-- Manual records queue -->
        <div id="unpickManualQueue" style="display: none; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong id="unpickManualQueueCount"></strong>
                <div style="display: flex; gap: 8px;">
                    <button class="test" onclick="clearUnpickManualQueue()" style="background: #f56565; color: white; border: none;">Clear All</button>
                    <button class="save" onclick="executeUnpickFromManual('${workspaceId}')">Execute Unpick</button>
                </div>
            </div>
            <div id="unpickManualTable" style="background: white; border-radius: 8px; border: 1px solid #e2e8f0; overflow: auto; max-height: 40vh;"></div>
        </div>

        <div id="unpickManualResults" style="display: none; margin-top: 20px;">
            <h5 style="margin: 0 0 10px;">Execution Results</h5>
            <div id="unpickManualResultsTable"></div>
            <div style="margin-top: 12px; display: flex; gap: 8px;">
                <button class="save" onclick="downloadUnpickResults('manual')">Download CSV</button>
            </div>
        </div>
    `;
}

function addUnpickManualRow() {
    const wh    = document.getElementById('unpickManualWhId').value.trim();
    const order = document.getElementById('unpickManualOrderNum').value.trim();
    const item  = document.getElementById('unpickManualItemNum').value.trim();
    if (!wh || !order || !item) { unpickToast('Please fill in all three fields.', 'warning'); return; }
    unpickAgentState.manualRecords.push({ wh_id: wh, order_number: order, item_number: item });
    document.getElementById('unpickManualWhId').value    = '';
    document.getElementById('unpickManualOrderNum').value = '';
    document.getElementById('unpickManualItemNum').value  = '';
    refreshUnpickManualTable();
}

function refreshUnpickManualTable() {
    const records = unpickAgentState.manualRecords;
    const queueDiv = document.getElementById('unpickManualQueue');
    queueDiv.style.display = records.length ? 'block' : 'none';
    if (!records.length) return;
    document.getElementById('unpickManualQueueCount').textContent = records.length + ' record(s) queued:';
    let html = '<table style="width:100%; border-collapse: collapse; font-size: 13px;">';
    html += '<thead><tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;">';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">#</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Order Number</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">WH ID</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Item Number</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Remove</th>';
    html += '</tr></thead><tbody>';
    records.forEach((r, i) => {
        html += `<tr style="border-bottom: 1px solid #edf2f7; background: ${i % 2 === 0 ? 'white' : '#f9fafb'};">`;
        html += `<td style="padding: 8px 14px; color: #718096;">${i + 1}</td>`;
        html += `<td style="padding: 8px 14px; font-family: monospace;">${r.order_number}</td>`;
        html += `<td style="padding: 8px 14px;">${r.wh_id}</td>`;
        html += `<td style="padding: 8px 14px; font-family: monospace;">${r.item_number}</td>`;
        html += `<td style="padding: 8px 14px;"><button onclick="removeUnpickManualRow(${i})" style="background: none; border: none; color: #e53e3e; cursor: pointer; font-size: 16px;">×</button></td>`;
        html += '</tr>';
    });
    html += '</tbody></table>';
    document.getElementById('unpickManualTable').innerHTML = html;
}

function removeUnpickManualRow(index) {
    unpickAgentState.manualRecords.splice(index, 1);
    refreshUnpickManualTable();
}

function clearUnpickManualQueue() {
    unpickAgentState.manualRecords = [];
    refreshUnpickManualTable();
}

function parseUnpickCsvPaste() {
    const text = document.getElementById('unpickCsvPaste').value;
    parseUnpickCsvText(text);
}

function parseUnpickCsvFile() {
    const file = document.getElementById('unpickCsvFile').files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => parseUnpickCsvText(e.target.result);
    reader.readAsText(file);
}

function parseUnpickCsvText(text) {
    const msgEl = document.getElementById('unpickCsvImportMsg');
    const lines = text.trim().split(/\r?\n/);
    if (lines.length < 2) { msgEl.textContent = 'CSV must have a header row and at least one data row.'; msgEl.style.color = '#e53e3e'; return; }

    const header = lines[0].split(',').map(h => h.trim().toLowerCase());
    const whIdx    = header.indexOf('wh_id');
    const orderIdx = header.indexOf('order_number');
    const itemIdx  = header.indexOf('item_number');
    if (whIdx < 0 || orderIdx < 0 || itemIdx < 0) {
        msgEl.textContent = 'CSV header must contain: wh_id, order_number, item_number';
        msgEl.style.color = '#e53e3e';
        return;
    }

    let added = 0, skipped = 0;
    for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(',').map(c => c.trim().replace(/^"|"$/g, ''));
        const wh    = cols[whIdx]    || '';
        const order = cols[orderIdx] || '';
        const item  = cols[itemIdx]  || '';
        if (!wh || !order || !item) { skipped++; continue; }
        unpickAgentState.manualRecords.push({ wh_id: wh, order_number: order, item_number: item });
        added++;
    }

    msgEl.textContent = `Imported ${added} row(s)${skipped ? `, skipped ${skipped} incomplete row(s)` : ''}.`;
    msgEl.style.color = added > 0 ? '#38a169' : '#e53e3e';
    document.getElementById('unpickCsvPaste').value = '';
    refreshUnpickManualTable();
}

function executeUnpickFromManual(workspaceId) {
    const records = unpickAgentState.manualRecords;
    if (!records.length) { unpickToast('No records in the queue.', 'warning'); return; }
    unpickConfirm(`Execute unpick for <strong>${records.length}</strong> record(s)? This will update the database and cannot be undone.`, () => {
        executeUnpickRecords(workspaceId, records, 'manual');
    });
}

// ── SHARED EXECUTE ────────────────────────────────────────────

function executeUnpickRecords(workspaceId, records, source) {
    const resultsDivId   = source === 'auto' ? 'unpickAutoResults'   : 'unpickManualResults';
    const resultsTableId = source === 'auto' ? 'unpickAutoResultsTable' : 'unpickManualResultsTable';

    document.getElementById(resultsDivId).style.display = 'block';
    document.getElementById(resultsTableId).innerHTML = '<div style="padding: 16px; color: #718096;">Executing unpick — please wait...</div>';

    fetch('/api/v0/unpick_agent/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace_id: workspaceId, records: records })
    })
    .then(r => r.json())
    .then(data => {
        if (data.type === 'error') {
            document.getElementById(resultsTableId).innerHTML = `<div style="padding: 16px; color: #e53e3e;">Error: ${data.error}</div>`;
            return;
        }
        unpickAgentState.lastResults = data.results || [];
        renderUnpickResultsTable(unpickAgentState.lastResults, resultsTableId);
        // Auto-refresh log panel if it's active
        if (unpickAgentState.activeTab === 'logs') loadUnpickLogs(workspaceId);
    })
    .catch(err => {
        document.getElementById(resultsTableId).innerHTML = `<div style="padding: 16px; color: #e53e3e;">Error: ${err.message}</div>`;
    });
}

function renderUnpickResultsTable(results, containerId) {
    const container = document.getElementById(containerId);
    const total   = results.length;
    const success = results.filter(r => r.status === 'SUCCESS').length;
    const warning = results.filter(r => r.status === 'WARNING').length;
    const error   = results.filter(r => r.status === 'ERROR').length;

    let html = `
        <div style="display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;">
            <span style="padding: 4px 12px; background: #c6f6d5; border-radius: 20px; font-size: 13px; font-weight: 600; color: #276749;">${success} Success</span>
            <span style="padding: 4px 12px; background: #fefcbf; border-radius: 20px; font-size: 13px; font-weight: 600; color: #744210;">${warning} Warning</span>
            <span style="padding: 4px 12px; background: #fed7d7; border-radius: 20px; font-size: 13px; font-weight: 600; color: #c53030;">${error} Error</span>
            <span style="padding: 4px 12px; background: #e2e8f0; border-radius: 20px; font-size: 13px; color: #4a5568;">${total} Total</span>
        </div>
    `;
    html += '<div style="background: white; border-radius: 8px; border: 1px solid #e2e8f0; overflow: auto; max-height: 45vh;">';
    html += '<table style="width:100%; border-collapse: collapse; font-size: 13px;">';
    html += '<thead><tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;">';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; width: 80px;">Status</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Order Number</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; width: 80px;">WH ID</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Item Number</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Message</th>';
    html += '</tr></thead><tbody>';
    results.forEach(r => {
        const rowBg     = r.status === 'ERROR' ? '#fff5f5' : (r.status === 'WARNING' ? '#fffff0' : 'white');
        const statusClr = r.status === 'ERROR' ? '#c53030' : (r.status === 'WARNING' ? '#b7791f' : '#276749');
        html += `<tr style="border-bottom: 1px solid #edf2f7; background: ${rowBg};">`;
        html += `<td style="padding: 8px 14px; font-weight: 700; color: ${statusClr};">${r.status}</td>`;
        html += `<td style="padding: 8px 14px; font-family: monospace;">${r.order_number}</td>`;
        html += `<td style="padding: 8px 14px;">${r.wh_id}</td>`;
        html += `<td style="padding: 8px 14px; font-family: monospace;">${r.item_number}</td>`;
        html += `<td style="padding: 8px 14px; color: #4a5568;">${r.message}</td>`;
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function downloadUnpickResults(source) {
    const results = unpickAgentState.lastResults;
    if (!results.length) { unpickToast('No results to download yet. Run an unpick first.', 'info'); return; }
    const rows = [['Status', 'Order Number', 'WH ID', 'Item Number', 'Message']];
    results.forEach(r => rows.push([r.status, r.order_number, r.wh_id, r.item_number, r.message]));
    const csv = rows.map(r => r.map(c => '"' + String(c).replace(/"/g, '""') + '"').join(',')).join('\\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'unpick_results_' + new Date().toISOString().slice(0, 10) + '.csv';
    a.click();
}

// ── PARTIAL UNPICK TAB (Scenario 3) ──────────────────────────

function renderUnpickPartialTab(workspaceId) {
    const panel = document.getElementById('unpickPanel_partial');
    panel.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 16px;">
            <h5 style="margin: 0 0 8px;">Partial Unpick</h5>
            <p style="margin: 0 0 14px; color: #4a5568; font-size: 13px;">
                Reduce the picked quantity by a specific amount without fully releasing the line.
                The work queue status updates conditionally — <strong>'C'</strong> if still fully picked, <strong>'U'</strong> if not.
            </p>

            <div style="display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 16px;">
                <div>
                    <label style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 4px;">WH ID</label>
                    <input type="text" id="partialWhId" placeholder="e.g. WH01" style="width: 90px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px;">
                </div>
                <div>
                    <label style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 4px;">Order Number</label>
                    <input type="text" id="partialOrderNum" placeholder="e.g. ORD-10001" style="width: 180px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px;">
                </div>
                <div>
                    <label style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 4px;">Item Number</label>
                    <input type="text" id="partialItemNum" placeholder="e.g. ITEM-999" style="width: 160px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px;">
                </div>
                <div>
                    <label style="font-size: 13px; color: #4a5568; display: block; margin-bottom: 4px;">Unpick Qty</label>
                    <input type="number" id="partialQty" placeholder="e.g. 5" min="0.001" step="any" style="width: 100px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px;">
                </div>
                <button class="save" onclick="executePartialUnpick('${workspaceId}')">Execute Partial Unpick</button>
            </div>

            <div id="partialUnpickResult" style="display: none; margin-top: 12px; padding: 12px; border-radius: 8px;"></div>
        </div>
    `;
}

function executePartialUnpick(workspaceId) {
    const wh    = document.getElementById('partialWhId').value.trim();
    const order = document.getElementById('partialOrderNum').value.trim();
    const item  = document.getElementById('partialItemNum').value.trim();
    const qty   = parseFloat(document.getElementById('partialQty').value);

    if (!wh || !order || !item) { unpickToast('Please fill in WH ID, Order Number and Item Number.', 'warning'); return; }
    if (isNaN(qty) || qty <= 0) { unpickToast('Unpick Qty must be a positive number.', 'warning'); return; }

    unpickConfirm(`Partially unpick <strong>${qty}</strong> unit(s) for order <strong>${order}</strong> / item <strong>${item}</strong>? This will update the database.`, () => {
        const resultEl = document.getElementById('partialUnpickResult');
        resultEl.style.display = 'block';
        resultEl.style.background = '#ebf8ff';
        resultEl.textContent = 'Executing partial unpick…';

        fetch('/api/v0/unpick_agent/partial_unpick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace_id: workspaceId, wh_id: wh, order_number: order, item_number: item, unpick_qty: qty })
        })
        .then(r => r.json())
        .then(data => {
            if (data.type === 'error') {
                resultEl.style.background = '#fff5f5';
                resultEl.innerHTML = '<span style="color:#c53030;">&#10060; ' + data.message + '</span>';
                unpickToast('Partial unpick failed.', 'error');
            } else if (data.type === 'warning') {
                resultEl.style.background = '#fffbeb';
                resultEl.innerHTML = '<span style="color:#b7791f;">&#9888; ' + data.message + '</span>';
                unpickToast(data.message, 'warning');
            } else {
                resultEl.style.background = '#f0fff4';
                resultEl.innerHTML = '<span style="color:#276749;">&#10003; ' + data.message + '</span>';
                unpickToast('Partial unpick completed.', 'success');
                document.getElementById('partialWhId').value = '';
                document.getElementById('partialOrderNum').value = '';
                document.getElementById('partialItemNum').value = '';
                document.getElementById('partialQty').value = '';
            }
        })
        .catch(err => {
            resultEl.style.background = '#fff5f5';
            resultEl.innerHTML = '<span style="color:#c53030;">&#10060; Error: ' + err.message + '</span>';
            unpickToast('Request failed.', 'error');
        });
    });
}

// ── LOG VIEWER TAB ────────────────────────────────────────────

function renderUnpickLogsPanel(workspaceId) {
    const panel = document.getElementById('unpickPanel_logs');
    panel.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div>
                <h5 style="margin: 0 0 4px;">Unpick Agent Activity Log</h5>
                <p style="margin: 0; color: #718096; font-size: 13px;">Per-record log from both the automated scheduler and manual executions. Each run is grouped and colour-coded by outcome.</p>
            </div>
            <div style="display: flex; gap: 8px;">
                <button class="test" onclick="loadUnpickLogs('${workspaceId}')">Refresh</button>
                <button class="save" onclick="window.location.href='/api/v0/unpick_agent/logs/download?format=csv'">Download CSV</button>
                <button class="save" onclick="window.location.href='/api/v0/unpick_agent/logs/download?format=txt'">Download TXT</button>
            </div>
        </div>
        <span id="unpickLogMeta" style="font-size: 12px; color: #718096;"></span>
        <div id="unpickLogContainer" style="background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: auto; max-height: 65vh; margin-top: 10px;">
            <div style="padding: 24px; text-align: center; color: #718096;">Switch to this tab to load logs.</div>
        </div>
    `;
}

function loadUnpickLogs(workspaceId) {
    const container = document.getElementById('unpickLogContainer');
    if (!container) return;
    container.innerHTML = '<div style="padding: 24px; text-align: center; color: #718096;">Loading logs...</div>';

    fetch('/api/v0/unpick_agent/logs')
        .then(r => r.json())
        .then(data => {
            const logs = data.logs || [];
            const meta = document.getElementById('unpickLogMeta');
            if (meta) meta.textContent = logs.length + ' total log entries';
            if (!logs.length) {
                container.innerHTML = '<div style="padding: 32px; text-align: center; color: #718096;">No log entries yet. Execute an unpick to see activity here.</div>';
                return;
            }
            renderUnpickLogTable(logs, container);
        })
        .catch(err => {
            container.innerHTML = '<div style="padding: 24px; text-align: center; color: #e53e3e;">Failed to load logs: ' + err.message + '</div>';
        });
}

function renderUnpickLogTable(logs, container) {
    // Group by run_id
    const runs = {};
    const runOrder = [];
    logs.forEach(e => {
        const rid = e.run_id || 'Unknown Run';
        if (!runs[rid]) { runs[rid] = []; runOrder.push(rid); }
        runs[rid].push(e);
    });

    let html = '<table style="width:100%; border-collapse: collapse; font-size: 13px;">';
    html += '<thead><tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0; position: sticky; top: 0;">';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; width: 200px;">Timestamp</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; width: 80px;">Level</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; width: 70px;">WH ID</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; width: 140px;">Order Number</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568; width: 130px;">Item Number</th>';
    html += '<th style="padding: 10px 14px; text-align: left; color: #4a5568;">Message</th>';
    html += '</tr></thead><tbody>';

    // Newest runs first
    [...runOrder].reverse().forEach(rid => {
        const entries  = runs[rid];
        const hasError = entries.some(e => e.level === 'ERROR');
        const hasWarn  = entries.some(e => e.level === 'WARNING');
        const runStatus      = hasError ? 'ERROR' : (hasWarn ? 'WARNING' : 'COMPLETED');
        const runStatusColor = hasError ? '#e53e3e' : (hasWarn ? '#d69e2e' : '#38a169');

        html += '<tr style="background: #f0f4f8;">';
        html += `<td colspan="6" style="padding: 8px 14px; font-size: 12px; font-weight: 600; color: #2d3748; border-bottom: 1px solid #e2e8f0;">`;
        html += `Run: ${rid}`;
        html += ` <span style="margin-left: 8px; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: white; background: ${runStatusColor};">${runStatus}</span>`;
        html += ` <span style="margin-left: 8px; color: #718096; font-weight: 400;">${entries.length} event(s)</span>`;
        html += '</td></tr>';

        entries.forEach(e => {
            const rowBg      = e.level === 'ERROR' ? '#fff5f5' : (e.level === 'WARNING' ? '#fffbeb' : 'white');
            const levelColor = e.level === 'ERROR' ? '#c53030' : (e.level === 'WARNING' ? '#b7791f' : '#276749');
            html += `<tr style="background: ${rowBg}; border-bottom: 1px solid #edf2f7;">`;
            html += `<td style="padding: 8px 14px; color: #4a5568; white-space: nowrap; font-size: 12px;">${e.timestamp}</td>`;
            html += `<td style="padding: 8px 14px; font-weight: 600; color: ${levelColor}; font-size: 12px;">${e.level}</td>`;
            html += `<td style="padding: 8px 14px; color: #4a5568; font-family: monospace; font-size: 12px;">${e.wh_id || ''}</td>`;
            html += `<td style="padding: 8px 14px; color: #4a5568; font-family: monospace; font-size: 12px;">${e.order_number || ''}</td>`;
            html += `<td style="padding: 8px 14px; color: #4a5568; font-family: monospace; font-size: 12px;">${e.item_number || ''}</td>`;
            html += `<td style="padding: 8px 14px; color: #2d3748;">${e.message}</td>`;
            html += '</tr>';
        });
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}


function downloadDeviceResetLogs(format) {
    window.location.href = '/api/v0/device_reset_logs/download?format=' + format;
}

    </script>
</body>
</html>
"""

def get_config():
    return {
        "app_name": "Tychons WAI",
        "default_workspace": "default",
        "max_users": 100,
    }