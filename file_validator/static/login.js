const signUpButton = document.getElementById("signUp");
const signInButton = document.getElementById("signIn");
const container = document.getElementById("container");

signUpButton.addEventListener("click", () => {
  container.classList.add("right-panel-active");
});

signInButton.addEventListener("click", () => {
  container.classList.remove("right-panel-active");
});
const forgotPasswordLink = document.getElementById("forgotPasswordLink");
const signInTitle = document.querySelector(".sign-in-container h1");

forgotPasswordLink.addEventListener("click", () => {
  signInTitle.textContent = "Reset Password";
  const signInForm = document.querySelector(".sign-in-container form");
  let form = document.getElementById("signinform");
  form.action = "/forgot";
  signInForm.innerHTML = `

        <span>Enter your email to reset your password</span>
        <input type="email" name="email" placeholder="Email" />
        
        <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}" />
        <button type="submit">Reset Password</button>
    `;
});
function getCSRFToken() {
  const cookieString = document.cookie;
  const csrfTokenCookie = cookieString
    .split(";")
    .find((cookie) => cookie.trim().startsWith("csrftoken="));

  if (csrfTokenCookie) {
    return csrfTokenCookie.split("=")[1];
  }

  return null;
}
