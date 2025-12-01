// Theme Management
class ThemeManager {
  constructor() {
    this.themeToggle = document.getElementById("theme-toggle");
    this.currentTheme = localStorage.getItem("theme") || "dark";
    this.init();
  }

  init() {
    this.setTheme(this.currentTheme);
    if (this.themeToggle) {
      this.themeToggle.addEventListener("click", () => this.toggleTheme());
    }
  }

  setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    this.updateToggleIcon(theme);
    this.applyThemeStyles(theme);
  }

  toggleTheme() {
    const newTheme = this.currentTheme === "dark" ? "light" : "dark";
    this.setTheme(newTheme);
    this.currentTheme = newTheme;

    // Add animation effect
    document.documentElement.style.transition = "all 0.5s ease";
    setTimeout(() => {
      document.documentElement.style.transition = "";
    }, 500);
  }

  updateToggleIcon(theme) {
    if (this.themeToggle) {
      const icon = this.themeToggle.querySelector("i");
      if (icon) {
        icon.className = theme === "dark" ? "fas fa-sun" : "fas fa-moon";
      }
    }
  }

  applyThemeStyles(theme) {
    // Add any theme-specific style adjustments here
    const root = document.documentElement;
    if (theme === "light") {
      root.style.setProperty("--glass-blur", "blur(20px)");
    } else {
      root.style.setProperty("--glass-blur", "blur(10px)");
    }
  }
}

// Mobile Navigation
class MobileNavigation {
  constructor() {
    this.navToggle = document.getElementById("nav-toggle");
    this.navMenu = document.getElementById("nav-menu");
    this.init();
  }

  init() {
    if (this.navToggle && this.navMenu) {
      this.navToggle.addEventListener("click", () => this.toggleMenu());

      // Close menu when clicking on a link
      document.querySelectorAll(".nav-link").forEach((link) => {
        link.addEventListener("click", () => this.closeMenu());
      });

      // Close menu when clicking outside
      document.addEventListener("click", (e) => {
        if (
          !this.navToggle.contains(e.target) &&
          !this.navMenu.contains(e.target)
        ) {
          this.closeMenu();
        }
      });
    }
  }

  toggleMenu() {
    this.navMenu.classList.toggle("active");
    this.navToggle.classList.toggle("active");

    // Prevent body scroll when menu is open
    if (this.navMenu.classList.contains("active")) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
  }

  closeMenu() {
    this.navMenu.classList.remove("active");
    this.navToggle.classList.remove("active");
    document.body.style.overflow = "";
  }
}

// Contact Form Handler
class ContactForm {
  constructor() {
    this.form = document.getElementById("contact-form");
    if (this.form) this.init();
  }

  init() {
    this.form.addEventListener("submit", (e) => this.handleSubmit(e));
    this.initCharacterCounter();
  }

  async handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData(this.form);
    const submitBtn = this.form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    try {
      // Show loading state
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
      submitBtn.disabled = true;

      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(Object.fromEntries(formData)),
      });

      const data = await response.json();

      if (response.ok) {
        this.showMessage("Message sent successfully!", "success");
        this.form.reset();
        this.showSuccessModal();
      } else {
        throw new Error(data.error || "Failed to send message");
      }
    } catch (error) {
      console.error("Contact form error:", error);
      this.showMessage("Failed to send message. Please try again.", "error");
    } finally {
      submitBtn.innerHTML = originalText;
      submitBtn.disabled = false;
    }
  }

  initCharacterCounter() {
    const messageField = document.getElementById("message");
    if (messageField) {
      const charCounter = document.createElement("div");
      charCounter.className = "char-counter";
      charCounter.style.cssText = `
                text-align: right;
                margin-top: 0.5rem;
                color: var(--text-secondary);
                font-size: 0.8rem;
                transition: color 0.3s ease;
            `;
      messageField.parentNode.appendChild(charCounter);

      messageField.addEventListener("input", () => {
        const length = messageField.value.length;
        charCounter.textContent = `${length}/2000 characters`;

        if (length > 1800) {
          charCounter.style.color = "#ff3366";
        } else if (length > 1500) {
          charCounter.style.color = "var(--accent-tertiary)";
        } else {
          charCounter.style.color = "var(--text-secondary)";
        }
      });

      // Initialize counter
      messageField.dispatchEvent(new Event("input"));
    }
  }

  showMessage(text, type) {
    // Create flash message
    const flashDiv = document.createElement("div");
    flashDiv.className = `flash-message ${type} glass`;
    flashDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 2rem;
            z-index: 1000;
            max-width: 400px;
        `;
    flashDiv.innerHTML = `
            <div class="flash-content">
                <i class="fas fa-${
                  type === "success" ? "check-circle" : "exclamation-triangle"
                }"></i>
                <span>${text}</span>
            </div>
            <button class="flash-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

    document.body.appendChild(flashDiv);

    // Remove after 5 seconds
    setTimeout(() => {
      if (flashDiv.parentElement) {
        flashDiv.remove();
      }
    }, 5000);
  }

  showSuccessModal() {
    const modal = document.getElementById("success-modal");
    if (modal) {
      modal.style.display = "flex";
    }
  }
}

// Typing Animation
class TypingAnimation {
  constructor(elementId, texts, speed = 100) {
    this.element = document.getElementById(elementId);
    this.texts = texts;
    this.speed = speed;
    this.textIndex = 0;
    this.charIndex = 0;
    this.currentText = "";
    this.isDeleting = false;

    if (this.element) this.type();
  }

  type() {
    const current = this.textIndex % this.texts.length;
    const fullText = this.texts[current];

    if (this.isDeleting) {
      this.currentText = fullText.substring(0, this.charIndex - 1);
      this.charIndex--;
    } else {
      this.currentText = fullText.substring(0, this.charIndex + 1);
      this.charIndex++;
    }

    this.element.innerHTML = this.currentText;
    this.element.classList.add("typing-text");

    let typeSpeed = this.speed;

    if (this.isDeleting) {
      typeSpeed /= 2;
    }

    if (!this.isDeleting && this.charIndex === fullText.length) {
      typeSpeed = 2000; // Pause at end
      this.isDeleting = true;
    } else if (this.isDeleting && this.charIndex === 0) {
      this.isDeleting = false;
      this.textIndex++;
      typeSpeed = 500;
    }

    setTimeout(() => this.type(), typeSpeed);
  }
}

// Smooth Scrolling
class SmoothScroller {
  constructor() {
    this.init();
  }

  init() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute("href"));
        if (target) {
          target.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      });
    });

    // Add scroll event for navbar background
    window.addEventListener("scroll", () => {
      const navbar = document.querySelector(".navbar");
      if (navbar) {
        if (window.scrollY > 100) {
          navbar.style.background = "rgba(10, 10, 10, 0.95)";
          navbar.style.backdropFilter = "blur(20px)";
        } else {
          navbar.style.background = "rgba(10, 10, 10, 0.9)";
          navbar.style.backdropFilter = "blur(10px)";
        }
      }
    });
  }
}

// Project Filtering
class ProjectFilter {
  constructor() {
    this.categoryFilter = document.getElementById("category-filter");
    this.techFilter = document.getElementById("tech-filter");
    this.projectCards = document.querySelectorAll(".project-card");
    this.init();
  }

  init() {
    if (this.categoryFilter) {
      this.categoryFilter.addEventListener("change", () =>
        this.filterProjects()
      );
    }
    if (this.techFilter) {
      this.techFilter.addEventListener("change", () => this.filterProjects());
    }
  }

  filterProjects() {
    const selectedCategory = this.categoryFilter
      ? this.categoryFilter.value
      : "all";
    const selectedTech = this.techFilter
      ? this.techFilter.value.toLowerCase()
      : "";

    this.projectCards.forEach((card) => {
      const category = card.getAttribute("data-category") || "";
      const technologies = card.getAttribute("data-technologies") || "";

      let categoryMatch =
        selectedCategory === "all" || category === selectedCategory;
      let techMatch =
        !selectedTech || technologies.toLowerCase().includes(selectedTech);

      if (categoryMatch && techMatch) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });
  }
}

// Animation Manager
class AnimationManager {
  constructor() {
    this.init();
  }

  init() {
    // Ensure buttons are always visible immediately
    this.ensureButtonVisibility();

    // Intersection Observer for fade-in animations
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          if (
            !entry.target.classList.contains("btn") &&
            !entry.target.closest(".hero-buttons") &&
            !entry.target.closest(".resume-actions") &&
            !entry.target.closest(".cta-buttons") &&
            !entry.target.closest(".nav-actions")
          ) {
            entry.target.classList.add("fade-in");
          }

          if (
            entry.target.classList.contains("project-card") ||
            entry.target.classList.contains("card")
          ) {
            if (
              !entry.target.closest(".hero-buttons") &&
              !entry.target.closest(".resume-actions") &&
              !entry.target.closest(".cta-buttons")
            ) {
              entry.target.style.animationDelay = `${Math.random() * 0.3}s`;
            }
          }
        }
      });
    }, observerOptions);

    document
      .querySelectorAll(
        ".card:not(.btn):not(.hero-buttons *):not(.resume-actions *):not(.cta-buttons *):not(.nav-actions *), .project-card:not(.btn), .reveal-text:not(.btn)"
      )
      .forEach((el) => {
        observer.observe(el);
      });
  }

  ensureButtonVisibility() {
    const buttonSelectors = [
      ".btn",
      ".hero-buttons",
      ".resume-actions",
      ".cta-buttons",
      ".nav-actions",
      ".project-links",
      ".modal-footer",
    ];

    buttonSelectors.forEach((selector) => {
      document.querySelectorAll(selector).forEach((element) => {
        element.style.opacity = "1";
        element.style.visibility = "visible";
        element.style.display = getComputedStyle(element).display;
        element.style.animation = "none";
        element.style.transition = "none";
        element.style.transform = "none";

        if (
          element.classList.contains("hero-buttons") ||
          element.classList.contains("resume-actions") ||
          element.classList.contains("cta-buttons")
        ) {
          element.style.display = "flex";
        } else if (element.classList.contains("btn")) {
          element.style.display = "inline-flex";
        }
      });
    });

    const heroButtons = document.querySelector(".hero-buttons");
    if (heroButtons) {
      heroButtons.style.opacity = "1";
      heroButtons.style.visibility = "visible";
      heroButtons.style.display = "flex";
      heroButtons.style.animation = "none";
      heroButtons.style.transition = "none";

      heroButtons.querySelectorAll(".btn").forEach((btn) => {
        btn.style.opacity = "1";
        btn.style.visibility = "visible";
        btn.style.display = "inline-flex";
        btn.style.animation = "none";
        btn.style.transition = "none";
        btn.style.transform = "none";
      });
    }
  }
}

// Utility Functions
const PortfolioUtils = {
  // Debounce function for performance
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // Format date
  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  },

  // Copy to clipboard
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      this.showToast("Copied to clipboard!", "success");
      return true;
    } catch (err) {
      console.error("Failed to copy: ", err);
      this.showToast("Failed to copy", "error");
      return false;
    }
  },

  // Show toast notification
  showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.style.cssText = `
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            padding: 1rem 1.5rem;
            background: var(--bg-glass);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius);
            color: var(--text-primary);
            z-index: 1000;
        `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove();
      }
    }, 3000);
  },

  // Load visitor count (mock function)
  loadVisitorCount() {
    const visitorElement = document.getElementById("visitor-count");
    if (visitorElement) {
      // Simulate loading
      setTimeout(() => {
        const randomVisitors = Math.floor(Math.random() * 1000) + 500;
        visitorElement.textContent = `Visitors: ${randomVisitors}+`;
      }, 1000);
    }
  },

  // Format file size
  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  },

  // Generate random ID
  generateId() {
    return Math.random().toString(36).substr(2, 9);
  },

  // Check if element is in viewport
  isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <=
        (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  },
};

// Initialize everything when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  console.log("Portfolio: DOM loaded, initializing...");

  // First, ensure all buttons are immediately visible
  const ensureImmediateButtonVisibility = () => {
    const buttonContainers = [
      ".hero-buttons",
      ".resume-actions",
      ".cta-buttons",
      ".nav-actions",
    ];

    buttonContainers.forEach((selector) => {
      const containers = document.querySelectorAll(selector);
      containers.forEach((container) => {
        container.style.opacity = "1";
        container.style.visibility = "visible";
        container.style.display = "flex";
        container.style.animation = "none";
        container.style.transition = "none";

        container.querySelectorAll(".btn").forEach((btn) => {
          btn.style.opacity = "1";
          btn.style.visibility = "visible";
          btn.style.display = "inline-flex";
          btn.style.animation = "none";
          btn.style.transition = "none";
          btn.style.transform = "none";
        });
      });
    });

    document.querySelectorAll(".btn").forEach((btn) => {
      btn.style.opacity = "1";
      btn.style.visibility = "visible";
      btn.style.display = "inline-flex";
      btn.style.animation = "none";
      btn.style.transition = "none";
      btn.style.transform = "none";
    });
  };

  // Run immediately
  ensureImmediateButtonVisibility();

  // Initialize all managers
  new ThemeManager();
  new MobileNavigation();
  new ContactForm();
  new SmoothScroller();
  new ProjectFilter();
  new AnimationManager();

  // Initialize typing animation if element exists
  const typingElement = document.getElementById("typing-text");
  if (typingElement) {
    const texts = JSON.parse(
      typingElement.getAttribute("data-texts") ||
        '["Full Stack Developer", "Python Expert", "UI/UX Enthusiast"]'
    );
    new TypingAnimation("typing-text", texts);
  }

  // Load visitor count
  PortfolioUtils.loadVisitorCount();

  // Add click outside handler for modals
  document.addEventListener("click", (e) => {
    const modal = document.getElementById("success-modal");
    if (modal && e.target === modal) {
      closeSuccessModal();
    }
  });

  // Final button visibility checks
  setTimeout(ensureImmediateButtonVisibility, 100);
  setTimeout(ensureImmediateButtonVisibility, 500);
  setTimeout(ensureImmediateButtonVisibility, 1000);

  console.log("Portfolio website initialized successfully!");
});

// Global functions for modals
function closeSuccessModal() {
  const modal = document.getElementById("success-modal");
  if (modal) {
    modal.style.display = "none";
  }
}

// Export for global access
window.Portfolio = {
  ThemeManager,
  MobileNavigation,
  ContactForm,
  PortfolioUtils,
  closeSuccessModal,
};
