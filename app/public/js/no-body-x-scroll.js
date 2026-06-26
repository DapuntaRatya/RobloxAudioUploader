(function () {
  "use strict";

  var ALLOW_X_SCROLL_SELECTOR = [
    ".asset-table-wrap",
    ".filter-toolbar",
    ".assets-sidebar",
    ".app-sidebar",
    ".grant-result-list",
    ".progress-list",
    ".asset-list",
    ".result-log",
    ".item-list"
  ].join(",");

  var startX = 0;
  var startY = 0;
  var ticking = false;

  function canScrollInside(element) {
    if (!element || !element.closest) {
      return false;
    }

    var scrollBox = element.closest(ALLOW_X_SCROLL_SELECTOR);
    if (!scrollBox) {
      return false;
    }

    return scrollBox.scrollWidth > scrollBox.clientWidth + 2;
  }

  function clampBodyX() {
    ticking = false;

    var root = document.documentElement;
    var body = document.body;

    if (root) {
      root.scrollLeft = 0;
    }

    if (body) {
      body.scrollLeft = 0;
    }

    if (window.scrollX !== 0) {
      window.scrollTo(0, window.scrollY || 0);
    }
  }

  function requestClamp() {
    if (ticking) {
      return;
    }

    ticking = true;
    window.requestAnimationFrame(clampBodyX);
  }

  window.addEventListener("load", requestClamp, { passive: true });
  window.addEventListener("resize", requestClamp, { passive: true });
  window.addEventListener("orientationchange", requestClamp, { passive: true });

  window.addEventListener("scroll", function () {
    if (window.scrollX !== 0 || document.documentElement.scrollLeft !== 0 || document.body.scrollLeft !== 0) {
      requestClamp();
    }
  }, { passive: true });

  document.addEventListener("touchstart", function (event) {
    if (!event.touches || event.touches.length === 0) {
      return;
    }

    startX = event.touches[0].clientX;
    startY = event.touches[0].clientY;
  }, { passive: true });

  document.addEventListener("touchmove", function (event) {
    if (!event.touches || event.touches.length === 0) {
      return;
    }

    var dx = event.touches[0].clientX - startX;
    var dy = event.touches[0].clientY - startY;
    var horizontalGesture = Math.abs(dx) > Math.abs(dy) + 4;

    if (horizontalGesture && !canScrollInside(event.target)) {
      event.preventDefault();
      requestClamp();
    }
  }, { passive: false });

  document.addEventListener("wheel", function (event) {
    var horizontalWheel = Math.abs(event.deltaX) > Math.abs(event.deltaY);

    if (horizontalWheel && !canScrollInside(event.target)) {
      event.preventDefault();
      requestClamp();
    }
  }, { passive: false });

  requestClamp();
})();
