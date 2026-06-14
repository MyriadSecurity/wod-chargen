/** Hash routing for generator vs weight map (works with PyScript hashchange handler). */
(function () {
  function currentPage() {
    return (location.hash || "").replace(/^#/, "").split("?")[0];
  }

  function dispatchHashChange() {
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  }

  function navigate(page) {
    const target = page === "weights" ? "weights" : "";
    if (currentPage() === target) {
      dispatchHashChange();
      return;
    }
    if (target) {
      location.hash = target;
      return;
    }
    const base = location.pathname + location.search;
    if (location.hash) {
      history.pushState(null, "", base);
    }
    dispatchHashChange();
  }

  window.wodAppNavigate = navigate;
})();
