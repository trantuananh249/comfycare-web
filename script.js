const navToggle = document.querySelector(".nav-toggle");
const mainNav = document.querySelector(".main-nav");

if (navToggle && mainNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = mainNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  mainNav.querySelectorAll("details").forEach((details) => {
    details.addEventListener("toggle", () => {
      if (!details.open) return;
      mainNav.querySelectorAll("details[open]").forEach((otherDetails) => {
        if (otherDetails !== details) otherDetails.removeAttribute("open");
      });
    });
  });

  mainNav.addEventListener("click", (event) => {
    const target = event.target;
    const link = target instanceof Element ? target.closest("a") : null;
    if (link) {
      mainNav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
      mainNav.querySelectorAll("details[open]").forEach((details) => details.removeAttribute("open"));
    }
  });
}

const sizeGuidePage = document.querySelector(".size-guide-page");

if (sizeGuidePage) {
  const openSizeDetails = (hash) => {
    if (!hash || !hash.startsWith("#")) return;
    const target = document.querySelector(hash);
    if (!target) return;
    const details = target instanceof HTMLDetailsElement ? target : target.closest("details");
    if (details) details.open = true;
  };

  document.querySelectorAll("[data-size-target]").forEach((link) => {
    link.addEventListener("click", () => {
      openSizeDetails(link.getAttribute("href"));
    });
  });

  openSizeDetails(window.location.hash);
  window.addEventListener("hashchange", () => openSizeDetails(window.location.hash));
}

const reviewCarousel = document.querySelector(".review-carousel");

if (reviewCarousel) {
  let reviewInitialized = false;

  const initializeReviews = () => {
    if (reviewInitialized) return;
    reviewInitialized = true;

    const reviewViewport = reviewCarousel.querySelector(".review-carousel__viewport");
    const reviewSlides = Array.from(reviewCarousel.querySelectorAll(".review-slide"));
    const reviewPrev = reviewCarousel.querySelector(".carousel-button--prev");
    const reviewNext = reviewCarousel.querySelector(".carousel-button--next");
    const reviewDots = reviewCarousel.querySelector(".carousel-dots");
    const reviewLightbox = document.querySelector(".review-lightbox");
    const reviewLightboxImage = reviewLightbox?.querySelector("img");
    const reviewLightboxClose = reviewLightbox?.querySelector(".review-lightbox__close");

    if (!reviewViewport || reviewSlides.length === 0 || !reviewDots) return;

    const getVisibleCount = () => (window.matchMedia("(max-width: 700px)").matches ? 1 : 3);
    const getActiveIndex = () => {
      const firstOffset = reviewSlides[0].offsetLeft;
      const step = reviewSlides[1] ? reviewSlides[1].offsetLeft - firstOffset : reviewSlides[0].offsetWidth;
      return step > 0 ? Math.round((reviewViewport.scrollLeft - firstOffset) / step) : 0;
    };

    const updateDots = () => {
      const activeIndex = getActiveIndex();
      reviewDots.querySelectorAll("button").forEach((dot, index) => {
        dot.classList.toggle("is-active", index === activeIndex);
        dot.setAttribute("aria-current", index === activeIndex ? "true" : "false");
      });
    };

    const scrollToReview = (index) => {
      const clampedIndex = Math.max(0, Math.min(index, reviewSlides.length - 1));
      reviewViewport.scrollTo({ left: reviewSlides[clampedIndex].offsetLeft, behavior: "smooth" });
    };

    reviewSlides.forEach((_, index) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.setAttribute("aria-label", `Xem review ${index + 1}`);
      dot.addEventListener("click", () => scrollToReview(index));
      reviewDots.append(dot);
    });

    reviewPrev?.addEventListener("click", () => scrollToReview(getActiveIndex() - getVisibleCount()));
    reviewNext?.addEventListener("click", () => scrollToReview(getActiveIndex() + getVisibleCount()));

    let scrollUpdateQueued = false;
    reviewViewport.addEventListener(
      "scroll",
      () => {
        if (scrollUpdateQueued) return;
        scrollUpdateQueued = true;
        window.requestAnimationFrame(() => {
          updateDots();
          scrollUpdateQueued = false;
        });
      },
      { passive: true },
    );
    window.addEventListener("resize", updateDots, { passive: true });
    updateDots();

    if (reviewLightbox && reviewLightboxImage) {
      const closeLightbox = () => {
        reviewLightbox.classList.remove("is-open");
        reviewLightbox.setAttribute("aria-hidden", "true");
        reviewLightboxImage.removeAttribute("src");
        document.body.style.overflow = "";
      };

      reviewCarousel.addEventListener("click", (event) => {
        const slide = event.target instanceof Element ? event.target.closest(".review-slide") : null;
        const src = slide?.getAttribute("data-review-src");
        if (!src) return;
        reviewLightboxImage.src = src;
        reviewLightbox.classList.add("is-open");
        reviewLightbox.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
      });

      reviewLightboxClose?.addEventListener("click", closeLightbox);
      reviewLightbox.addEventListener("click", (event) => {
        if (event.target === reviewLightbox) closeLightbox();
      });
      window.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeLightbox();
      });
    }
  };

  if ("IntersectionObserver" in window) {
    const reviewObserver = new IntersectionObserver(
      (entries, observer) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        observer.disconnect();
        initializeReviews();
      },
      { rootMargin: "400px 0px" },
    );
    reviewObserver.observe(reviewCarousel);
  } else {
    window.setTimeout(initializeReviews, 0);
  }
}
