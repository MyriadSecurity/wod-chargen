/** Hash routing for generator vs weight map (works with PyScript hashchange handler). */
(function () {
  function currentPage() {
    return (location.hash || "").replace(/^#/, "").split("?")[0];
  }

  function dispatchHashChange() {
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  }

  function navigate(page) {
    const target =
      page === "weights" ? "weights" : page === "strategy" ? "strategy" : "";
    if (!target) {
      const base = location.pathname;
      if (location.search || location.hash) {
        history.pushState(null, "", base);
      }
      dispatchHashChange();
      return;
    }
    if (currentPage() === target) {
      dispatchHashChange();
      return;
    }
    location.hash = target;
  }

  window.wodAppNavigate = navigate;
})();
