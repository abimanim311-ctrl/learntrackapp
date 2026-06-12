// LearnTrack Client-Side Utilities

document.addEventListener("DOMContentLoaded", function () {
    // 1. Sidebar Toggle for Mobile Views
    const sidebarCollapse = document.getElementById("sidebarCollapse");
    const sidebar = document.getElementById("sidebar");

    if (sidebarCollapse && sidebar) {
        sidebarCollapse.addEventListener("click", function () {
            sidebar.classList.toggle("active");
        });
    }

    // 2. Auto-Dismiss Flash Alerts
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            // Check if alert is still in DOM
            if (alert) {
                // Using Bootstrap's Alert instance transition
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000); // 5 seconds
    });

    // 3. Delete Confirmation Hook
    const deleteButtons = document.querySelectorAll(".confirm-delete");
    deleteButtons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            const itemName = this.getAttribute("data-item-name") || "this item";
            const message = `Are you absolutely sure you want to delete ${itemName}? This action cannot be undone and will delete all associated logs and records.`;
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // 4. Highlight Active Navigation Item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll("#sidebar ul.components li a");
    
    navLinks.forEach(function (link) {
        const href = link.getAttribute("href");
        // Exact match or prefix match for subpages (e.g., goals/add)
        if (href && (currentPath === href || (href !== "/" && currentPath.startsWith(href)))) {
            // Find parent li
            const parentLi = link.closest("li");
            if (parentLi) {
                parentLi.classList.add("active");
            }
        }
    });
});
