
function fetchResults(){
    console.log("Ok")
}


// const form = document.getElementById('uploadForm');
// const progressBarFill = document.querySelector('.progress-bar-fill');

// form.addEventListener('submit', function(event) {
//     event.preventDefault();

//     const formData = new FormData(form);
//     const xhr = new XMLHttpRequest();

//     xhr.open('POST', 'upload.php', true);

//     xhr.upload.addEventListener('progress', function(e) {
//         if (e.lengthComputable) {
//             const percentComplete = (e.loaded / e.total) * 100;
//             progressBarFill.style.width = percentComplete + '%';
//         }
//     });

//     xhr.addEventListener('load', function() {
//         if (xhr.status == 200) {
//             alert('File uploaded successfully!');
//         } else {
//             alert('File upload failed.');
//         }
//     });

//     xhr.send(formData);
// });

// const optionsForm = document.querySelector('.options-container form');

// optionsForm.addEventListener('submit', function(event) {
//     event.preventDefault(); // Prevent default form submission

//     const formData = new FormData(optionsForm);
//     const xhr = new XMLHttpRequest();

//     xhr.open('POST', 'submit_options.php', true); // Replace with your server-side script     URL

//     xhr.addEventListener('load', function() {
//         if (xhr.status == 200) {
//             alert('Options submitted successfully!');
//             // Optionally, you can handle response data or redirect the user
//         } else {
//             alert('Submission failed.');
//         }
//     });

//     xhr.send(formData); // Send form data asynchronously
// });
