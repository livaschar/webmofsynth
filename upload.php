<?php
// Check if file upload form was submitted
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_FILES["file"])) {
    $targetDirectory = "uploads/"; // Directory where uploaded files will be stored
    $targetFile = $targetDirectory . basename($_FILES["file"]["name"]);
    $uploadOk = 1;
    $fileType = strtolower(pathinfo($targetFile, PATHINFO_EXTENSION));

    // Check if file already exists
    if (file_exists($targetFile)) {
        echo "Sorry, file already exists.";
        $uploadOk = 0;
    }

    // Check file size (adjust as necessary)
    if ($_FILES["file"]["size"] > 5000000) { // 5MB limit
        echo "Sorry, your file is too large.";
        $uploadOk = 0;
    }

    // Allow only certain file formats (adjust as necessary)
    if ($fileType != "txt" && $fileType != "pdf" && $fileType != "doc" && $fileType != "docx") {
        echo "Sorry, only TXT, PDF, DOC, DOCX files are allowed.";
        $uploadOk = 0;
    }

    // Check if $uploadOk is set to 0 by an error
    if ($uploadOk == 0) {
        echo "Sorry, your file was not uploaded.";
    } else {
        // If everything is ok, try to upload file
        if (move_uploaded_file($_FILES["file"]["tmp_name"], $targetFile)) {
            echo "The file ". htmlspecialchars(basename($_FILES["file"]["name"])). " has been uploaded.";
        } else {
            echo "Sorry, there was an error uploading your file.";
        }
    }
} else {
    echo "Error: No file uploaded or invalid request.";
}
?>
