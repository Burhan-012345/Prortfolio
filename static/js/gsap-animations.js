// GSAP Animations and Scroll Triggers
document.addEventListener("DOMContentLoaded", function () {
  // Register ScrollTrigger plugin
  gsap.registerPlugin(ScrollTrigger);

  // Hero section animations
  const heroTimeline = gsap.timeline();
  heroTimeline
    .from(".hero-title", {
      duration: 1,
      y: 100,
      opacity: 0,
      ease: "power3.out",
    })
    .from(
      ".hero-subtitle",
      {
        duration: 0.8,
        y: 50,
        opacity: 0,
        ease: "power2.out",
      },
      "-=0.5"
    )
    .from(
      ".btn",
      {
        duration: 0.6,
        scale: 0,
        rotation: 360,
        ease: "back.out(1.7)",
      },
      "-=0.3"
    );

  // Animate cards on scroll
  gsap.utils.toArray(".card, .project-card").forEach((card) => {
    gsap.fromTo(
      card,
      {
        y: 100,
        opacity: 0,
      },
      {
        y: 0,
        opacity: 1,
        duration: 0.8,
        ease: "power2.out",
        scrollTrigger: {
          trigger: card,
          start: "top 80%",
          end: "bottom 20%",
          toggleActions: "play none none reverse",
        },
      }
    );
  });

  // Parallax effect for hero background
  gsap.to(".hero", {
    backgroundPosition: "50% 100%",
    ease: "none",
    scrollTrigger: {
      trigger: ".hero",
      start: "top top",
      end: "bottom top",
      scrub: true,
    },
  });

  // Animate skill bars
  gsap.utils.toArray(".skill-bar").forEach((bar) => {
    const width = bar.style.width;
    gsap.fromTo(
      bar,
      {
        width: "0%",
      },
      {
        width: width,
        duration: 1.5,
        ease: "power2.out",
        scrollTrigger: {
          trigger: bar,
          start: "top 80%",
          toggleActions: "play none none reverse",
        },
      }
    );
  });

  // Floating animation for elements
  gsap.to(".floating", {
    y: -20,
    duration: 2,
    repeat: -1,
    yoyo: true,
    ease: "sine.inOut",
  });

  // Stagger animation for project grid
  gsap.from(".projects-grid .project-card", {
    duration: 0.8,
    y: 60,
    opacity: 0,
    stagger: 0.1,
    ease: "power2.out",
    scrollTrigger: {
      trigger: ".projects-grid",
      start: "top 70%",
      toggleActions: "play none none reverse",
    },
  });

  // Navbar background on scroll
  gsap.to(".navbar", {
    background: "rgba(10, 10, 10, 0.9)",
    backdropFilter: "blur(10px)",
    duration: 0.3,
    scrollTrigger: {
      trigger: "main",
      start: "top top",
      end: "max",
      toggleActions: "play reverse play reverse",
    },
  });

  // Text reveal animations
  gsap.utils.toArray(".reveal-text").forEach((text) => {
    gsap.fromTo(
      text,
      {
        y: 100,
        opacity: 0,
      },
      {
        y: 0,
        opacity: 1,
        duration: 1,
        ease: "power3.out",
        scrollTrigger: {
          trigger: text,
          start: "top 80%",
          toggleActions: "play none none reverse",
        },
      }
    );
  });

  // Pulse animation for CTA buttons
  gsap.to(".pulse", {
    scale: 1.05,
    duration: 1,
    repeat: -1,
    yoyo: true,
    ease: "power1.inOut",
  });

  // Magnetic button effect
  document.querySelectorAll(".magnetic").forEach((button) => {
    button.addEventListener("mousemove", (e) => {
      const rect = button.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;

      gsap.to(button, {
        x: x * 0.3,
        y: y * 0.3,
        duration: 0.3,
        ease: "power2.out",
      });
    });

    button.addEventListener("mouseleave", () => {
      gsap.to(button, {
        x: 0,
        y: 0,
        duration: 0.3,
        ease: "power2.out",
      });
    });
  });
});

// Additional utility animations
class PortfolioAnimations {
  static fadeInUp(element, delay = 0) {
    gsap.fromTo(
      element,
      {
        y: 50,
        opacity: 0,
      },
      {
        y: 0,
        opacity: 1,
        duration: 0.8,
        delay: delay,
        ease: "power2.out",
      }
    );
  }

  static staggerFadeIn(selector, stagger = 0.1) {
    gsap.fromTo(
      selector,
      {
        y: 30,
        opacity: 0,
      },
      {
        y: 0,
        opacity: 1,
        duration: 0.6,
        stagger: stagger,
        ease: "power2.out",
      }
    );
  }

  static scaleIn(element) {
    gsap.fromTo(
      element,
      {
        scale: 0,
        rotation: -180,
      },
      {
        scale: 1,
        rotation: 0,
        duration: 0.8,
        ease: "back.out(1.7)",
      }
    );
  }
}
