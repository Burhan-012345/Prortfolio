// Admin Dashboard JavaScript
class AdminDashboard {
  constructor() {
    this.init();
  }

  init() {
    this.initDataTables();
    this.initForms();
    this.initToggle();
  }

  initDataTables() {
    // Simple table sorting functionality
    document.querySelectorAll(".admin-table th").forEach((header) => {
      header.addEventListener("click", () => {
        this.sortTable(header);
      });
    });
  }

  sortTable(header) {
    const table = header.closest("table");
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const rows = Array.from(table.querySelectorAll("tbody tr"));

    const isAscending = header.classList.contains("asc");
    header.classList.toggle("asc", !isAscending);
    header.classList.toggle("desc", isAscending);

    rows.sort((a, b) => {
      const aValue = a.children[columnIndex].textContent.trim();
      const bValue = b.children[columnIndex].textContent.trim();

      if (!isAscending) {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });

    const tbody = table.querySelector("tbody");
    tbody.innerHTML = "";
    rows.forEach((row) => tbody.appendChild(row));
  }

  initForms() {
    // Form validation and enhancements
    document.querySelectorAll("form").forEach((form) => {
      form.addEventListener("submit", (e) => {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
      });
    });

    // Image preview for file inputs
    document.querySelectorAll('input[type="file"]').forEach((input) => {
      input.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
          this.previewImage(file, input);
        }
      });
    });
  }

  previewImage(file, input) {
    const previewId = input.id + "-preview";
    let preview = document.getElementById(previewId);

    if (!preview) {
      preview = document.createElement("div");
      preview.id = previewId;
      preview.className = "image-preview";
      input.parentNode.appendChild(preview);
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      preview.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button type="button" class="remove-preview" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;
    };
    reader.readAsDataURL(file);
  }

  initToggle() {
    // Toggle switches
    document.querySelectorAll(".toggle-switch").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const input = toggle.querySelector('input[type="checkbox"]');
        input.checked = !input.checked;
        toggle.classList.toggle("active", input.checked);
      });
    });
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new AdminDashboard();
});

// Utility functions
const AdminUtils = {
  confirmAction(message = "Are you sure you want to proceed?") {
    return confirm(message);
  },

  showNotification(message, type = "success") {
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${
                  type === "success" ? "check" : "exclamation-triangle"
                }"></i>
                <span>${message}</span>
            </div>
        `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.classList.add("show");
    }, 100);

    setTimeout(() => {
      notification.classList.remove("show");
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  },

  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
  },
};
