(function () {
  /**
   * Validates Google reCAPTCHA before form submission.
   * Returns true when reCAPTCHA is not available to avoid blocking non-protected forms.
   * @param {HTMLFormElement} form
   * @returns {boolean}
   */
  function validateRecaptcha(form) {
    if (typeof grecaptcha === "undefined") {
      return true;
    }

    var response = grecaptcha.getResponse();
    if (response.length > 0) {
      return true;
    }

    var message = form.dataset.recaptchaMsg || "Please verify that you are not a robot.";
    alert(message);
    return false;
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Binds submit validation for every form explicitly marked as reCAPTCHA-protected.
    var forms = document.querySelectorAll("form[data-recaptcha-form='true']");
    forms.forEach(function (form) {
      form.addEventListener("submit", function (event) {
        if (!validateRecaptcha(form)) {
          event.preventDefault();
        }
      });
    });
  });
})();
