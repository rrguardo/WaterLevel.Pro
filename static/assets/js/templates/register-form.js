(function () {
  /**
   * Validates registration password confirmation before sending the form.
   */
  document.addEventListener("DOMContentLoaded", function () {
    var form = document.querySelector("form[data-register-form='true']");
    if (!form) {
      return;
    }

    form.addEventListener("submit", function (event) {
      var password = document.getElementById("exampleInputPassword1");
      var confirmPassword = document.getElementById("exampleInputPassword2");
      if (!password || !confirmPassword) {
        return;
      }

      if (password.value !== confirmPassword.value) {
        alert(form.dataset.passwordMismatchMsg || "Passwords do not match!");
        event.preventDefault();
      }
    });
  });
})();
