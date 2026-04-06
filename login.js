(function () {
  const form = document.getElementById("login-form");
  const usernameInput = document.getElementById("username-input");
  const passwordInput = document.getElementById("password-input");
  const loginButton = document.getElementById("login-button");
  const errorBox = document.getElementById("login-error");
  const destinationCopy = document.getElementById("login-destination");

  const params = new URLSearchParams(window.location.search);
  const nextPath = params.get("next") || "/";

  function setError(message) {
    if (!errorBox) {
      return;
    }
    if (!message) {
      errorBox.style.display = "none";
      errorBox.textContent = "";
      return;
    }
    errorBox.style.display = "block";
    errorBox.textContent = message;
  }

  function destinationLabel(path) {
    if (!path || path === "/") {
      return "the main dashboard overview";
    }
    if (path.includes("structure-showcase")) {
      return "the structure showcase window";
    }
    if (path.includes("assistant")) {
      return "the assistant workspace";
    }
    return "your requested workspace";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    loginButton.disabled = true;
    loginButton.textContent = "Signing in...";

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          username: usernameInput.value.trim(),
          password: passwordInput.value,
          next: nextPath,
        }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || "Sign-in failed. Please check the credentials and try again.");
      }

      window.location.href = payload.redirect_to || "/";
    } catch (error) {
      setError(error.message || "Sign-in failed. Please try again.");
      passwordInput.value = "";
      passwordInput.focus();
    } finally {
      loginButton.disabled = false;
      loginButton.textContent = "Enter Dashboard";
    }
  }

  if (destinationCopy) {
    destinationCopy.textContent = `Enter the project credentials to open the ECMO research dashboard and return to ${destinationLabel(nextPath)}.`;
  }

  form.addEventListener("submit", handleSubmit);
  usernameInput.focus();
})();
