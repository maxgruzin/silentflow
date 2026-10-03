"use strict";
// Keep visible artwork fixed to the viewport, clipped by its scrolling banner.
// Offscreen images retain their normal position so lazy loading stays effective.
(() => {
    const banners = [...document.querySelectorAll('.release-banner')];
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => entry.target.classList.toggle('is-visible', entry.isIntersecting));
    });
    banners.forEach(banner => observer.observe(banner));
})();
