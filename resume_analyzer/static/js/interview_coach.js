const interviewForm = document.querySelector(".interview-card form");
const interviewStartLoader = document.getElementById("interviewStartLoader");
const startButton = document.querySelector(".interview-btn");

if (interviewForm && interviewStartLoader) {

    interviewForm.addEventListener("submit", function (event) {

        // Browser validation ko pehle run hone do
        if (!interviewForm.checkValidity()) {
            return;
        }

        event.preventDefault();

        // Loading show
        interviewStartLoader.style.display = "flex";

        // Page scroll disable
        document.body.style.overflow = "hidden";

        // Button disable
        if (startButton) {
            startButton.disabled = true;
            startButton.textContent = "Preparing Interview...";
        }

        // Actual form submit
        interviewForm.submit();
    });
}