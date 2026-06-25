import { postJson } from "./api.js";

const form = document.getElementById("loginForm");
const apiKeyInput = document.getElementById("apiKey");
const message = document.getElementById("loginMessage");
const button = document.getElementById("loginButton");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  message.textContent = "";
  button.disabled = true;
  button.textContent = "Checking...";

  try {
    await postJson("/api/login", {
      "x-api-key": apiKeyInput.value.trim(),
    });
    window.location.href = "/";
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "Login";
  }
});
