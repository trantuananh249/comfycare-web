const navToggle = document.querySelector(".nav-toggle");
const mainNav = document.querySelector(".main-nav");

if (navToggle && mainNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = mainNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  mainNav.addEventListener("click", (event) => {
    if (event.target instanceof HTMLAnchorElement) {
      mainNav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    }
  });
}

const reviewViewport = document.querySelector(".review-carousel__viewport");
const reviewSlides = Array.from(document.querySelectorAll(".review-slide"));
const reviewPrev = document.querySelector(".carousel-button--prev");
const reviewNext = document.querySelector(".carousel-button--next");
const reviewDots = document.querySelector(".carousel-dots");
const reviewLightbox = document.querySelector(".review-lightbox");
const reviewLightboxImage = reviewLightbox?.querySelector("img");
const reviewLightboxClose = reviewLightbox?.querySelector(".review-lightbox__close");

if (reviewViewport && reviewSlides.length > 0 && reviewDots) {
  const getVisibleCount = () => (window.matchMedia("(max-width: 700px)").matches ? 1 : 3);

  const getActiveIndex = () => {
    const scrollLeft = reviewViewport.scrollLeft;
    let nearestIndex = 0;
    let nearestDistance = Number.POSITIVE_INFINITY;

    reviewSlides.forEach((slide, index) => {
      const distance = Math.abs(slide.offsetLeft - scrollLeft);
      if (distance < nearestDistance) {
        nearestDistance = distance;
        nearestIndex = index;
      }
    });

    return nearestIndex;
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
    reviewViewport.scrollTo({
      left: reviewSlides[clampedIndex].offsetLeft,
      behavior: "smooth",
    });
  };

  reviewSlides.forEach((_, index) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("aria-label", `Xem review ${index + 1}`);
    dot.addEventListener("click", () => scrollToReview(index));
    reviewDots.append(dot);
  });

  reviewPrev?.addEventListener("click", () => {
    scrollToReview(getActiveIndex() - getVisibleCount());
  });

  reviewNext?.addEventListener("click", () => {
    scrollToReview(getActiveIndex() + getVisibleCount());
  });

  reviewViewport.addEventListener("scroll", () => {
    window.requestAnimationFrame(updateDots);
  });

  window.addEventListener("resize", updateDots);
  updateDots();
}

if (reviewLightbox && reviewLightboxImage) {
  const closeLightbox = () => {
    reviewLightbox.classList.remove("is-open");
    reviewLightbox.setAttribute("aria-hidden", "true");
    reviewLightboxImage.removeAttribute("src");
    document.body.style.overflow = "";
  };

  reviewSlides.forEach((slide) => {
    slide.addEventListener("click", () => {
      const src = slide.getAttribute("data-review-src");
      if (!src) return;
      reviewLightboxImage.src = src;
      reviewLightbox.classList.add("is-open");
      reviewLightbox.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    });
  });

  reviewLightboxClose?.addEventListener("click", closeLightbox);
  reviewLightbox.addEventListener("click", (event) => {
    if (event.target === reviewLightbox) closeLightbox();
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeLightbox();
  });
}
