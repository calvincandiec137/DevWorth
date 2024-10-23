const docSelect = document.getElementById("documentation-select");
const pdfSection = document.getElementById("pdf-section");
const pdfViewer = document.getElementById("pdf-viewer");
const closePdfBtn = document.getElementById("close-pdf");

docSelect.addEventListener("change", function () {
  if (this.value) {
    pdfSection.classList.remove("hidden");
    pdfViewer.src = `/static/assests/${this.value}.pdf`;
  } else {
    pdfSection.classList.add("hidden");
    pdfViewer.src = "/static/assests/c.pdf";
  }
});

closePdfBtn.addEventListener("click", function () {
  pdfSection.classList.add("hidden");
  pdfViewer.src = "";
  docSelect.value = "";
});
