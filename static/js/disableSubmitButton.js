/* jshint esversion: 11 */

document.addEventListener("DOMContentLoaded", function() {
    var submitButton = document.getElementById("submitButton");
    var resetForm = document.getElementById("resetForm");

    submitButton.addEventListener("click", function() {
        submitButton.disabled = true;
        resetForm.submit();
    });
});