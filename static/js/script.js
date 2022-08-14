const alertContainer = document.querySelector(".alert-container");
const alertButton = document.querySelector(".alert-btn");

alertButton.addEventListener("click", () => {
    alertContainer.classList.remove("active");
    localStorage.setItem("alertBannerDisplayed", "true")
});

setTimeout(() => {
    if(!localStorage.getItem("alertBannerDisplayed"))
    alertContainer.classList.add("active");
}, 2000);

