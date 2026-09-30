document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-analysis-form]");
  if (form) {
    const fileInput = form.querySelector("#resume");
    const fileLabel = form.querySelector("[data-file-label]");
    const jobDescription = form.querySelector("#job_description");
    const count = form.querySelector("[data-char-count]");
    const dropZone = form.querySelector("[data-drop-zone]");
    const submitButton = form.querySelector("[data-submit-button]");
    const uploadError = form.parentElement.querySelector("[data-upload-error]");

    const showUploadError = (message) => {
      uploadError.textContent = message;
      uploadError.hidden = !message;
      dropZone.classList.toggle("has-error", Boolean(message));
    };

    const updateFileLabel = () => {
      const file = fileInput.files[0];
      fileLabel.textContent = file
        ? `${file.name} · ${(file.size / (1024 * 1024)).toFixed(2)} MB`
        : "Attach resume (PDF or DOCX)";
      dropZone.classList.toggle("has-file", Boolean(file));
    };

    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (file && file.size > 8 * 1024 * 1024) {
        fileInput.value = "";
        updateFileLabel();
        showUploadError("The resume is larger than 8 MB. Choose a smaller PDF or DOCX file.");
        return;
      }
      updateFileLabel();
      showUploadError("");
    });
    const updateCount = () => {
      count.textContent = `${jobDescription.value.length.toLocaleString()} / 20,000`;
    };
    jobDescription.addEventListener("input", updateCount);
    updateCount();
    ["dragenter", "dragover"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("is-dragging");
      });
    });
    ["dragleave", "drop"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("is-dragging");
      });
    });
    dropZone.addEventListener("drop", (event) => {
      const [file] = event.dataTransfer.files;
      if (!file) return;
      const extension = file.name.split(".").pop().toLowerCase();
      if (!["pdf", "docx"].includes(extension)) {
        showUploadError("Please attach a PDF or DOCX resume.");
        return;
      }
      if (file.size > 8 * 1024 * 1024) {
        showUploadError("The resume is larger than 8 MB. Choose a smaller PDF or DOCX file.");
        return;
      }
      const transfer = new DataTransfer();
      transfer.items.add(file);
      fileInput.files = transfer.files;
      updateFileLabel();
      showUploadError("");
    });
    form.addEventListener("submit", () => {
      showUploadError("");
      submitButton.disabled = true;
      form.querySelector("[data-submit-label]").textContent = "Analyzing...";
      form.querySelector("[data-spinner]").classList.remove("d-none");
    });
  }

  document.querySelectorAll("[data-confirm-delete]").forEach((deleteForm) => {
    deleteForm.addEventListener("submit", (event) => {
      if (!window.confirm("Delete this saved analysis? This cannot be undone.")) {
        event.preventDefault();
      }
    });
  });
});
