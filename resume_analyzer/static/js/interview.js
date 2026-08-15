const interviewForm = document.querySelector("form");
const interviewLoader = document.getElementById("loadingOverlay");
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

        const answer = answerBox ? answerBox.value.trim() : "";

        // Empty answer -> Django/browser validation handle karega
        if (!answer) {
            return;
        }

        const submitButton = interviewForm.querySelector(".submit-btn");

        if (!submitButton) {
            return;
        }

        const isFinalQuestion =
            submitButton.textContent.includes("Finish Interview");

        // Q1-Q7 -> normal submit, NO LOADING
        if (!isFinalQuestion) {
            return;
        }

        // Q8 -> FINAL SUBMISSION
        event.preventDefault();

        interviewLoader.style.display = "flex";
        document.body.style.overflow = "hidden";

        submitButton.disabled = true;

        setTimeout(function () {
            interviewForm.submit();
        }, 700);
    });
}