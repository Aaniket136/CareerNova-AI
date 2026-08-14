const interviewForm = document.querySelector("form");
const interviewLoader = document.getElementById("interviewLoader");
const answerBox = document.getElementById("answer");
const charCount = document.getElementById("charCount");


// =========================
// CHARACTER COUNTER
// =========================

if (answerBox && charCount) {
    answerBox.addEventListener("input", function () {
        const count = answerBox.value.length;
        charCount.textContent = `${count} / 3000 characters`;
    });
}


// =========================
// FINAL SUBMISSION LOADING
// =========================

if (interviewForm && interviewLoader) {

    interviewForm.addEventListener("submit", function (event) {

        if (!answerBox.value.trim()) {
            return;
        }

        const submitButton = interviewForm.querySelector(".submit-btn");
        const isFinalQuestion = submitButton &&
            submitButton.textContent.includes("Finish Interview");

        if (!isFinalQuestion) {
            return;
        }

        event.preventDefault();

        interviewLoader.style.display = "flex";
        document.body.style.overflow = "hidden";

        submitButton.disabled = true;

        setTimeout(function () {
            interviewForm.submit();
        }, 700);
    });
}