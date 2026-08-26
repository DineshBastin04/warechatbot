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

 #algorithm, #processSelect, #openai_model, #model_type{
    width: 97.9% !important;
}




.loading { color: #4299e1; font-style: italic; }
.error { color: #f56565; }


    </style>
</head>
<body>

    <div id="globalLoader" style="display: none; text-align: center; margin-top: 20px;">
    <span class="loader"></span> Please wait...
</div>


    <div id="successMessage" class="success-message"></div>
    <div id="errorMessage" class="error-message"></div>

       <div class="logo">
        <h2 class="logo-title">∞ Tychons <span class="logo-ai" >wi</span> </h2>
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
                        password: data.db_config.password || ''
                    },
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
                    showSuccessMessage(data.message || 'Connected to Vanna successfully!');
                    isVannaConnected = true;
                    setTimeout(() => {
                        window.location.href = `/home?workspace_id=${workspaceId}`;
                    }, 1000);
                } else {
                    showErrorMessage(data.error || 'Failed to connect to Vanna.');
                    isVannaConnected = false;
                }
            })
            .catch(error => showErrorMessage('Error connecting to Vanna: ' + error));
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
                    showSuccessMessage(data.message || 'Vanna initialized successfully!');
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
                    showErrorMessage(data.error || 'Failed to initialize Vanna.');
                    isVannaConnected = false;
                }
            })
            .catch(error => {
                showErrorMessage('Error initializing Vanna: ' + error);
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
                            db_details: data.db_config
                        })
                    });
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        isVannaConnected = true;
                        showSuccessMessage(data.message || 'Vanna initialized successfully!');
                        updatePredictionToggleUI(true); //  Explicitly enable toggle
                        
                    } else {
                        throw new Error(data.error || 'Failed to initialize Vanna.');
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
                showErrorMessage("Please initialize Vanna (LLM and DB) before accessing database schema.");
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
                showErrorMessage("Please initialize Vanna (LLM and DB) before accessing database schema.");
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
                showErrorMessage("Please initialize Vanna (LLM and DB) before accessing database schema.");
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
                showErrorMessage("Please initialize Vanna (LLM and DB) before testing SQL queries.");
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
                showErrorMessage("Please initialize Vanna (LLM and DB) before previewing data.");
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
        showErrorMessage("Please initialize Vanna (LLM and DB) before previewing data.");
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
                <button class="test" onclick="testConnection()">Test Connection</button>
                <p id="test-db-result"></p>
                <button class="save" onclick="saveDBConfig()">Save</button>
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
            fetch(`/api/v0/get_prediction_suggestions?workspace_name=${encodeURIComponent(workspaceName)}&table_name=${tableNamesParam}&query=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
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
        showErrorMessage("Please initialize Vanna (LLM and DB) before running predictions.");
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
        showErrorMessage("Please initialize Vanna (LLM and DB) before running predictions.");
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
        showErrorMessage("Please initialize Vanna (LLM and DB) before running predictions.");
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
        showErrorMessage("Please initialize Vanna (LLM and DB) before running predictions.");
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
            .then(response => response.json())
            .then(data => {
                showSuccessMessage(data.message || "Workspace created!");
                closeWorkspaceModal();
                fetchSavedWorkspaces();
            })
            .catch(error => showErrorMessage("Error saving workspace: " + error));
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

        function testConnection() {
            const payload = {
                serverName: document.getElementById('serverName').value,
                port: document.getElementById('port').value,
                databaseName: document.getElementById('databaseName').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            };
            const resultField = document.getElementById('test-db-result');
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

        function saveDBConfig() {
            const workspaceId = document.getElementById('workspaceId').value;
            const payload = {
                workspace_id: workspaceId,
                serverName: document.getElementById('serverName').value,
                port: document.getElementById('port').value,
                databaseName: document.getElementById('databaseName').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value
            };
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
                                    <li onclick="showAIProviders('${workspace.id}')"><i class="fas fa-robot"></i>AI Providers</li>
                                    <li onclick="showDBConfig('${workspace.id}')"><i class="fas fa-server"></i>DB Config</li>
                                    <li onclick="showPredictions('${workspace.id}')"><i class="fas fa-chart-line"></i>Predictions</li>
                                    <li onclick="showTrainingModule('${workspace.id}')"><i class="fas fa-book"></i>Training Data</li>
                                    <li onclick="showTeamsConfig('${workspace.id}')"><i class="fab fa-microsoft"></i> Teams Configuration</li>
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
                                
                                const csvContent = csvRows.join('\n');
                                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
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
                showErrorMessage("Please initialize Vanna (LLM and DB) before running predictions.");
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
                    showSuccessMessage(data.message || 'Vanna initialized successfully!');
                    updateAnomalyToggleUI(true);
                } else {
                    throw new Error(data.error || 'Failed to initialize Vanna.');
                }
            })
            .catch(err => {
                isVannaConnected = false;
                showErrorMessage(`Error initializing Vanna: ${err.message}`);
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
                `/api/v0/get_anomaly_suggestions?workspace_name=${encodeURIComponent(workspaceName)}` +
                `&table_name=${tableNamesParam}&query=${encodeURIComponent(query)}`,
                { method: 'GET', headers: { 'Content-Type': 'application/json' } }
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
        showErrorMessage("Please initialize Vanna (LLM and DB) before running anomaly detection.");
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
        showErrorMessage("Please initialize Vanna (LLM and DB) before running anomaly detection.");
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