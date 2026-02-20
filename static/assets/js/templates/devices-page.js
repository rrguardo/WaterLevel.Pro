(function () {
  /**
   * Reads the cached device key list from localStorage.
   * @returns {string[]}
   */
  function getStorageDevices() {
    var devices = localStorage.getItem("devices");
    if (!devices) {
      return [];
    }
    return devices.split("|");
  }

  /**
   * Selects badge color and icon based on the device label.
   * @param {string} label
   * @returns {{color: string, icon: string}}
   */
  function buildDeviceTypeVisual(label) {
    var color = "bg-warning";
    var icon = "ti-router";

    if ((label || "").indexOf("Switch") !== -1) {
      color = "bg-dark rounded-pill";
      icon = "ti-settings-automation";
    }

    return { color: color, icon: icon };
  }

  /**
   * Displays the standard success toast used across device operations.
   * @param {Object} config
   */
  function showToast(config) {
    var toastHead = document.getElementById("toast-info-head");
    var toastBody = document.getElementById("toast-info-body");
    var toastElement = document.getElementById("liveToast");

    if (!toastElement || !window.bootstrap) {
      return;
    }

    toastHead.innerHTML = '<strong class="me-auto">' + config.addSuccessTitle + "</strong>";
    toastBody.innerHTML = '<div class="toast-body">' + config.addSuccessBody + "</div>";

    var toast = bootstrap.Toast.getOrCreateInstance(toastElement);
    toast.show();
  }

  /**
   * Initializes camera QR scanning and redirects when a valid WLP URL is detected.
   * @param {Object} config
   */
  function mountQrScanner(config) {
    var button = document.getElementById("scanQR");
    if (!button) {
      return;
    }

    button.addEventListener("click", function () {
      if (!("mediaDevices" in navigator) || !("getUserMedia" in navigator.mediaDevices)) {
        alert(config.cameraUnsupportedMsg);
        return;
      }

      navigator.mediaDevices
        .getUserMedia({ video: { facingMode: "environment" } })
        .then(function (stream) {
          var video = document.createElement("video");
          document.body.appendChild(video);
          video.srcObject = stream;
          video.play();

          var canvasElement = document.createElement("canvas");
          var canvas = canvasElement.getContext("2d");

          function tick() {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
              canvasElement.width = video.videoWidth;
              canvasElement.height = video.videoHeight;
              canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);

              var imageData = canvas.getImageData(0, 0, canvasElement.width, canvasElement.height);
              var code = jsQR(imageData.data, imageData.width, imageData.height, {
                inversionAttempts: "dontInvert",
              });

              if (code && code.data && code.data.indexOf(config.domainPrefix) === 0) {
                video.pause();
                stream.getTracks().forEach(function (track) {
                  track.stop();
                });
                video.remove();
                window.location.href = code.data;
                return;
              }
            }
            requestAnimationFrame(tick);
          }

          tick();
        })
        .catch(function () {
          alert(config.cameraErrorMsg);
        });
    });
  }

  /**
   * Renders local/user devices and wires add/remove actions.
   * @param {Object} config
   */
  function mountDeviceList(config) {
    var userDevices = config.userDevices || {};

    /**
     * Synchronizes server-provided devices into localStorage.
     */
    function updateLocalStorage() {
      var devices = localStorage.getItem("devices");
      Object.keys(userDevices).forEach(function (key) {
        if (!devices) {
          devices = key;
        } else if (devices.indexOf(key) === -1) {
          devices += "|" + key;
        }
        localStorage.setItem("devices", devices);
        localStorage.setItem("info-" + key, userDevices[key][3]);
      });
    }

    updateLocalStorage();

    var list = document.getElementById("devices_list");
    getStorageDevices().forEach(function (value, index) {
      var infoLabel = localStorage.getItem("info-" + value) || "";
      var visual = buildDeviceTypeVisual(infoLabel);

      var addToUser = "";
      if (config.authUser) {
        addToUser =
          '<span class="badge btn d-flex btn-primary ms-3 add_to_user" user-device="' +
          value +
          '"><i class="ti ti-circle-plus fs-5 me-1"></i> <span class="d-none d-sm-block" user-device="' +
          value +
          '">' +
          config.addToUserMsg +
          "</span></span>";
      }

      var removeDevice =
        '<span device="' +
        value +
        '" class="remove_device badge btn d-flex btn-primary ms-3 bg-danger"><i class="ti ti-circle-minus fs-5 me-1"></i> <span class="d-none d-sm-block">' +
        config.removeMsg +
        "</span></span>";

      var badge =
        '<span class="badge d-flex align-items-center ' +
        visual.color +
        ' ms-auto text-truncate d-none d-sm-block">' +
        infoLabel +
        "</span>";

      var bgColor = index % 2 === 0 ? "bg-secondary text-white" : "bg-light";
      var linkValue =
        '<a href="' +
        config.deviceInfoBaseUrl +
        "?public_key=" +
        value +
        '" class="text-decoration-underline text-truncate">' +
        value +
        "</a>";

      var localName = localStorage.getItem("name-" + value);
      if (userDevices[value]) {
        addToUser = "";
        var nameToUse = userDevices[value][0] || localName || "";
        var btnName = '<button class="btn ' + visual.color + ' btn-sm mx-1">' + nameToUse + "</button>";
        linkValue =
          '<a href="' +
          config.deviceInfoBaseUrl +
          "?public_key=" +
          value +
          '" class="text-decoration-underline text-truncate">' +
          btnName +
          " [" +
          value +
          "]</a>";
      } else if (localName) {
        var btnName2 = '<button class="btn ' + visual.color + ' btn-sm mx-1">' + localName + "</button>";
        linkValue =
          '<a href="' +
          config.deviceInfoBaseUrl +
          "?public_key=" +
          value +
          '" class="text-decoration-underline text-truncate">' +
          btnName2 +
          " [" +
          value +
          "]</a>";
      }

      list.insertAdjacentHTML(
        "beforeend",
        '<li device="' +
          value +
          '" class="list-group-item d-flex ' +
          bgColor +
          '"><i class="ti ' +
          visual.icon +
          ' fs-5 me-2"></i>' +
          linkValue +
          addToUser +
          removeDevice +
          badge +
          "</li>"
      );
    });

    $(document).on("click", ".remove_device", function () {
      var pubKey = $(this).attr("device");
      alert(config.removingMsg + pubKey);

      if (config.authUser) {
        var nameValue = localStorage.getItem("name-" + pubKey) || "";
        $.post(config.devicesPostUrl, { action: "remove", public_key: pubKey, name: nameValue }).done(function (data) {
          if (data.status !== "success") {
            alert(config.removeFailMsg);
          }
        });
      }

      $('[device="' + pubKey + '"]').remove();
      var filtered = getStorageDevices().filter(function (item) {
        return item !== pubKey;
      });
      localStorage.setItem("devices", filtered.join("|"));
    });

    $(document).on("click", ".add_to_user", function () {
      var deviceKey = $(this).attr("user-device");
      var nameValue = localStorage.getItem("name-" + deviceKey) || "";

      $.post(config.devicesPostUrl, { action: "add", public_key: deviceKey, name: nameValue }).done(function () {
        $('[user-device="' + deviceKey + '"]' + ".badge").addClass("d-none");
      });

      showToast(config);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!window.WLP_DEVICES_CONFIG) {
      return;
    }

    mountQrScanner(window.WLP_DEVICES_CONFIG);
    mountDeviceList(window.WLP_DEVICES_CONFIG);
  });
})();
