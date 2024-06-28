<?php
// Check if options form was submitted
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST["option"])) {
    $selectedOption = $_POST["option"];

    // Process the selected option (example processing)
    switch ($selectedOption) {
        case "none":
            echo "You selected: None (Nan)";
            break;
        case "5":
            echo "You selected: 5";
            break;
        case "10":
            echo "You selected: 10";
            break;
        case "15":
            echo "You selected: 15";
            break;
        case "20":
            echo "You selected: 20";
            break;
        default:
            echo "Invalid option selected.";
            break;
    }
} else {
    echo "Error: No options submitted or invalid request.";
}
?>
