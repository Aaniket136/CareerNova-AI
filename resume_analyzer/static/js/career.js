const form = document.getElementById("careerForm");
const loading = document.getElementById("loading-overlay");
const submitButton = document.getElementById("generateButton");
const buttonText = document.getElementById("buttonText");

let submitted = false;

form.addEventListener("submit", function (e) {

    if (submitted) {
        e.preventDefault();
        return;
    }

    submitted = true;

    loading.style.display = "flex";

    submitButton.disabled = true;

    buttonText.innerText = "AI is creating your roadmap...";

});