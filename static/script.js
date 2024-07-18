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


    $.ajax({
        url: '/upload',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            document.getElementById('uploadStatus').innerHTML = '<p>Files uploaded successfully</p>';
            console.log(response);
            // Optionally, reset form or perform other actions upon success
        },
        error: function(error) {
            document.getElementById('uploadStatus').innerHTML = '<p>Error uploading files: ' + error.responseJSON.error + '</p>';
            console.error(error);
            // Handle error response as needed
        }
    });

}



function submitJob() {
    var form = document.getElementById('submitForm');
    var formData = new FormData(form);
    var selectedOption = formData.get('option');

    document.getElementById('loader').style.display = 'block'; // Show loader
    document.getElementById('submitButton').disabled = true;

    $.ajax({
        url: '/submit-job',
        method: 'POST',
        data: { option: selectedOption },
        success: function(response) {
            document.getElementById('loader').style.display = 'none'; // Hide loader
            document.getElementById('jobStatus').innerText = response.message;
            document.getElementById('submitButton').disabled = false;
        },
        error: function(error) {
            document.getElementById('submitButton').disabled = false;
            document.getElementById('loader').style.display = 'none'; // Hide loader
            document.getElementById('jobStatus').innerText = 'An error occurred while submitting the job.';
        }
    });
}


function fetchResults(){
    console.log("Fetching results...");
    
    document.getElementById('loader').style.display = 'block'; // Show loader

    $.ajax({
        url: '/fetch-results',
        method: 'GET',
        success: function(response) {
            document.getElementById('loader').style.display = 'none'; // Hide loader
            document.getElementById('results').innerText = response.message;
        },
        error: function(error) {
            document.getElementById('loader').style.display = 'none'; // Hide loader
            document.getElementById('results').innerText = 'An error occurred';
        }
    });
}


function showCSV() {
    console.log("Reading file...");

    $.ajax({
        url: '/show-csv',
        method: 'GET',
        success: function(response) {
            if (response.table) {
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

// function downloadButton(){
//     console.log("Downloading file...");
    
//     $.ajax({
//         url: '/download-csv',
//         method: 'GET',
//         success: function(response) {
//             document.getElementById('results').innerText = response.message;
//         },
//         error: function(error) {
//             document.getElementById('results').innerText = 'An error occurred';
//         }
//         });
// }

function downloadButton() {
    console.log("Button clicked. Initiating download...");
    window.location.href = '/download-csv';
}

// PRINT WITHOUT CHANGING SCREEN
// function readCSV(){
//     console.log("Reading file...");
    
//     $.ajax({
//         url: '/read-csv',
//         method: 'GET',
//         success: function(response) {
//             if (response.table) {
//                 document.getElementById('results').innerHTML = response.table;
//             } else {
//                 document.getElementById('results').innerText = 'Error: ' + response.error;
//             }
//         },
//         error: function(error) {
//             document.getElementById('results').innerText = 'An error occurred';
//         }
//     });
// }



// TESTS



function readFile(){
    console.log("Reading file...");
    
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

