const form = document.querySelector("form");
const loading = document.getElementById("loading-overlay");
const submitButton = form.querySelector("button[type='submit']");

let submitted = false;

form.addEventListener("submit", function (e) {

    if (submitted) {
        e.preventDefault();
        return;
    }

    submitted = true;

    loading.style.display = "flex";

    submitButton.disabled = true;

    submitButton.textContent = "Analyzing...";

});