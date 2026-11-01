(() => {
  const search = document.getElementById("workspaceSearch");
  const themeToggle = document.getElementById("themeToggle");
  const copyFeedback = document.getElementById("copyFeedback");

  if (search) {
    search.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
      document.querySelectorAll(".order-row").forEach((row) => {
        row.hidden = !row.textContent.toLowerCase().includes(query);
      });
    });

    document.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        search.focus();
        search.select();
      }
    });
  }

  const setTheme = (isDark) => {
    document.body.classList.toggle("dark-mode", isDark);
    if (themeToggle) {
      themeToggle.setAttribute("aria-pressed", String(isDark));
      themeToggle.setAttribute(
        "aria-label",
        isDark ? "Switch to light mode" : "Switch to dark mode",
      );
    }
  };

  if (themeToggle) {
    try {
      setTheme(localStorage.getItem("packwise-theme") === "dark");
    } catch {
      setTheme(false);
    }
    themeToggle.addEventListener("click", () => {
      const isDark = !document.body.classList.contains("dark-mode");
      setTheme(isDark);
      try {
        localStorage.setItem("packwise-theme", isDark ? "dark" : "light");
      } catch {
        return;
      }
    });
  }

  if (copyFeedback) {
    document.querySelectorAll("[data-copy]").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(button.dataset.copy);
          copyFeedback.textContent = "Order ID copied";
          copyFeedback.classList.add("visible");
          window.setTimeout(() => copyFeedback.classList.remove("visible"), 1800);
        } catch {
          copyFeedback.textContent = "Could not copy the order ID";
          copyFeedback.classList.add("visible");
          window.setTimeout(() => copyFeedback.classList.remove("visible"), 2400);
        }
      });
    });
  }
})();
