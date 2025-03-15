// Open Project Modal
function openModal(projectFile) {
    document.getElementById("modalFrame").src = projectFile;
    document.getElementById("projectModal").style.display = "block";
}

// Close Modal
function closeModal() {
    document.getElementById("projectModal").style.display = "none";
    document.getElementById("modalFrame").src = "";
}
