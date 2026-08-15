const interviewForm = document.querySelector(".interview-card form");
const interviewStartLoader = document.getElementById("loadingOverlay");
const startButton = document.querySelector(".interview-btn");

if (interviewForm && interviewStartLoader) {

    interviewForm.addEventListener("submit", function (event) {

        // Browser validation pehle hone do
        if (!interviewForm.checkValidity()) {
            return;
        }

        // Loading show
        interviewStartLoader.style.display = "flex";

        // Page scroll disable
        document.body.style.overflow = "hidden";

        // Button disable
        if (startButton) {
            startButton.disabled = true;
            startButton.textContent = "Preparing Interview...";
        }

        // IMPORTANT:
        // event.preventDefault() nahi lagana hai.
        // Form normally Django ko submit hoga.
    });
}