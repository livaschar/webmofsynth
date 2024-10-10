// Disable buttons on page load
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('submitButton').disabled = true; // Initially disable the submit button
    document.getElementById('showResultsButton').disabled = true; // Initially disable the Show Results button
    document.getElementById('downloadCSVButton').disabled = true; // Initially disable the Download CSV button
    // Check if we are on results.html
    if (window.location.pathname.includes("results.html")) {
        // Enable buttons if on results.html
        document.getElementById('downloadCSVButton').disabled = false; 
        }
});


function showSelectedFiles() {
    var input = document.getElementById('file');
    var fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    // Check if number of selected files exceeds the limit (10)
    if (input.files.length > 10) {
        alert('You can select up to 10 files.');
        // Reset file input to clear selected files
        input.value = '';
        return;
    }

    for (var i = 0; i < input.files.length; i++) {
        var fileName = input.files[i].name;
        var listItem = document.createElement('p');
        listItem.textContent = fileName;
        fileList.appendChild(listItem);
    }
}

function uploadFiles() {
    var formData = new FormData();
    var fileInput = document.getElementById('file');

    for (var i = 0; i < fileInput.files.length; i++) {
        formData.append('file', fileInput.files[i]);
    }
    
    document.getElementById('uploadStatus').innerText = '';

    $.ajax({
        url: '/upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            // Join the filenames array with a newline character
            let filenamesList = response.filenames.join('<br>'); // Using <br> for line breaks in HTML
            // Display the success message and the filenames
            document.getElementById('uploadStatus').innerHTML = response.message + '<br>' + filenamesList;
            // console.log(response);
            document.getElementById('submitButton').disabled = false;
        },
        error: function(response) {
            // Check if the response has a JSON error object
            if (response.responseJSON && response.responseJSON.error) {
                const errorMessage = response.responseJSON.error;
                if (errorMessage.includes('An error occured')) {
                    // Perform specific action for this error
                    document.getElementById('uploadStatus').innerText = "Error: " + errorMessage;
                    alert("Please Reload the page")
                } else if (errorMessage.includes('404')) {
                    // Handle other errors generically
                    document.getElementById('uploadStatus').innerText = "Error: " + errorMessage
                    alert("Please Reload the page")
                } else {
                    // Handle other errors generically
                    document.getElementById('uploadStatus').innerText = "Error: " + errorMessage
                }
            } else {
                // Fallback message for unknown errors
                document.getElementById('uploadStatus').innerText = "Error: Uploading.\nIf error persists please contact us";
                alert("Please Reload the page")
            }
        }
    });

}



function submitJob() {
    var form = document.getElementById('submitForm');
    var formData = new FormData(form);
    var selectedOption = formData.get('option');

    document.getElementById('jobStatus').innerText = '';
    document.getElementById('loader').style.display = 'block'; // Show loader
    document.getElementById('submitButton').disabled = true;

    $.ajax({
        url: '/submit-job',
        method: 'POST',
        data: { option: selectedOption },
        success: function(response) {
            document.getElementById('loader').style.display = 'none'; // Hide loader
            document.getElementById('submitButton').disabled = false;
            document.getElementById('showResultsButton').disabled = false;
            document.getElementById('downloadCSVButton').disabled = false;
            document.getElementById('jobStatus').innerText = response.message;
            // console.log(response)
        },
        error: function(response) {
            // Check if the response has a JSON error object
            if (response.responseJSON && response.responseJSON.error) {
                // Get the error message
                const errorMessage = response.responseJSON.error;
        
                // Check for the specific error message
                if (errorMessage.includes('No option selected.')) {
                    // Perform specific action for this error
                    document.getElementById('jobStatus').innerText = "Error: " + errorMessage;
                    document.getElementById('submitButton').disabled = false;
                } else {
                    // Handle other errors generically
                    document.getElementById('jobStatus').innerText = "Error: " + errorMessage
                    document.getElementById('submitButton').disabled = true;
                    document.getElementById('loader').style.display = 'none'; // Hide loader
                    alert("Please Reload the page")
                }
            } else {
                // Fallback message for unknown errors
                document.getElementById('jobStatus').innerText = "An error occurred while uploading.";
                document.getElementById('submitButton').disabled = true;
                document.getElementById('loader').style.display = 'none'; // Hide loader
                alert("Please Reload the page")
            }
        }
    });
}



function showCSV() {
    $.ajax({
        url: '/show-csv',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                // Redirect to the results page with the table data
                window.location.href = '/print-results';
            } else {
                alert('Error: ' + response.error);
            }
        },
        error: function(error) {
            alert('An error occurred');
        }
    });
}


function downloadButton() {
    // console.log("Button clicked. Initiating download...");
    window.location.href = '/download-csv';
}


// TESTS



function readFile(){
    // console.log("Reading file...");
    
    $.ajax({
        url: '/read-file',
        method: 'GET',
        success: function(response) {
            if (response.file_contents) {
                document.getElementById('results').innerText = 'File Contents: ' + response.file_contents;
            } else {
                document.getElementById('results').innerText = 'Error: ' + response.error;
            }
        },
        error: function(error) {
            document.getElementById('results').innerText = 'An error occurred';
        }
    });
}

function notifyServerOfReload() {
    fetch('/reload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: 'Page reloaded' })
    })
    .then(response => response.json())
    .then(data => {
        // console.log('Server response:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

window.addEventListener("beforeunload", function (event) {
    notifyServerOfReload();
});

