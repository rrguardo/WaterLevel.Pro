(function () {
  /**
   * Parses the local device list from storage.
   * @returns {string[]}
   */
  function parseStorageDevices() {
    var devices = localStorage.getItem("devices");
    if (!devices) {
      return [];
    }
    return devices.split("|");
  }

  /**
   * Resolves the display name priority between user profile and local cache.
   * @param {Object} config
   * @returns {string}
   */
  function getNameToDisplay(config) {
    var localName = localStorage.getItem("name-" + config.deviceKey);
    if (localName || config.userDeviceName) {
      return config.userDeviceName || localName;
    }
    return "";
  }

  /**
   * Updates the device title area with the resolved name.
   * @param {Object} config
   */
  function loadDeviceName(config) {
    if (!config.deviceNameSelector) {
      return;
    }
    var name = getNameToDisplay(config);
    $(config.deviceNameSelector).html(name + '<i class="ti ti-edit fs-4 ms-2"></i>');
  }

  /**
   * Adds the current device to local storage caches.
   * @param {Object} config
   * @param {string} newDevice
   */
  function syncDeviceToStorage(config, newDevice) {
    var devices = localStorage.getItem("devices");
    if (!devices) {
      devices = newDevice;
    } else if (devices.indexOf(newDevice) === -1) {
      devices += "|" + newDevice;
    }
    localStorage.setItem("devices", devices);
    if (config.modelLongName) {
      localStorage.setItem("info-" + newDevice, config.modelLongName);
    }
  }

  /**
   * Toggles the "add device" button visibility depending on cached devices.
   * @param {Object} config
   */
  function checkCurrentDevice(config) {
    if (!config.addDeviceSelector) {
      return;
    }
    var devices = localStorage.getItem("devices");
    if (devices && devices.indexOf(config.deviceKey) !== -1) {
      $(config.addDeviceSelector).addClass("d-none");
    } else {
      $(config.addDeviceSelector).removeClass("d-none");
    }
  }

  /**
   * Sends the add-device request for authenticated users.
   * @param {Object} config
   * @param {string} key
   * @param {string} name
   */
  function postAddDevice(config, key, name) {
    if (!config.authUser || !config.devicesPostUrl) {
      return;
    }
    $.post(config.devicesPostUrl, { action: "add", public_key: key, name: name || "" });
  }

  /**
   * Shows a bootstrap toast when title/body were provided.
   * @param {Object} config
   */
  function showToast(config) {
    if (!config.toastTitle || !config.toastBody) {
      return;
    }
    $("#toast-info-head").html('<strong class="me-auto">' + config.toastTitle + "</strong>");
    $("#toast-info-body").html('<div class="toast-body">' + config.toastBody + "</div>");
    var toastEl = document.getElementById("liveToast");
    if (toastEl && window.bootstrap) {
      bootstrap.Toast.getOrCreateInstance(toastEl).show();
    }
  }

  /**
   * Binds the save-name action.
   * @param {Object} config
   */
  function bindSetName(config) {
    if (!config.setNameButtonSelector || !config.setNameInputSelector) {
      return;
    }

    $(config.setNameButtonSelector).on("click", function () {
      var value = $(config.setNameInputSelector).val();
      localStorage.setItem("name-" + config.deviceKey, value);
      postAddDevice(config, config.deviceKey, value);
      if (config.changeNameModalSelector) {
        $(config.changeNameModalSelector).modal("hide");
      }
      if (config.deviceNameSelector) {
        $(config.deviceNameSelector).text(value);
      }
    });
  }

  /**
   * Binds the add-device action to persist and sync user ownership.
   * @param {Object} config
   */
  function bindAddDevice(config) {
    if (!config.addDeviceSelector) {
      return;
    }

    $(document).on("click", config.addDeviceSelector, function () {
      syncDeviceToStorage(config, config.deviceKey);
      checkCurrentDevice(config);
      var localName = localStorage.getItem("name-" + config.deviceKey) || "";
      postAddDevice(config, config.deviceKey, localName);
      showToast(config);
    });
  }

  /**
   * Binds browser bookmark shortcut fallback behavior.
   * @param {Object} config
   */
  function bindBookmark(config) {
    if (!config.bookmarkSelector) {
      return;
    }

    $(document).on("click", config.bookmarkSelector, function () {
      var pageTitle = document.title;
      var pageUrl = window.location.href;

      if (window.sidebar && window.sidebar.addPanel) {
        window.sidebar.addPanel(pageTitle, pageUrl, "");
      } else if (window.external && "AddFavorite" in window.external) {
        window.external.AddFavorite(pageUrl, pageTitle);
      } else {
        var ctrlKey = navigator.userAgent.toLowerCase().indexOf("mac") !== -1 ? "Cmd" : "Ctrl";
        alert("Press " + ctrlKey + "+D " + (config.bookmarkMessage || "to bookmark this page."));
      }
    });
  }

  /**
   * Enables editing controls for admin/support views.
   * @param {Object} config
   */
  function bindAdminEditing(config) {
    if (!config.enableAdminEditing) {
      return;
    }
    $("input").prop("disabled", false);
    if (config.canEditButtonSelector) {
      $(config.canEditButtonSelector).removeClass("d-none");
    }
    if (config.cantEditSelector) {
      $(config.cantEditSelector).addClass("d-none");
    }
  }

  /**
   * Binds public/private QR render actions.
   * @param {Object} config
   */
  function bindShowQr(config) {
    if (config.showPublicQrSelector && config.publicQrTargetSelector && config.publicQrText) {
      $(config.showPublicQrSelector).on("click", function () {
        new QRCode(document.querySelector(config.publicQrTargetSelector), {
          text: config.publicQrText,
          width: 256,
          height: 256,
          colorDark: "#000000",
          colorLight: "#ffffff",
          correctLevel: QRCode.CorrectLevel.H,
        });
        $(this).hide();
      });
    }

    if (config.showPrivateQrSelector && config.privateQrTargetSelector) {
      $(config.showPrivateQrSelector).on("click", function () {
        var pk = $(this).attr("pk");
        new QRCode(document.querySelector(config.privateQrTargetSelector), {
          text: config.privateQrTextPrefix + pk,
          width: 256,
          height: 256,
          colorDark: "#000000",
          colorLight: "#ffffff",
          correctLevel: QRCode.CorrectLevel.H,
        });
        $(this).hide();
        if (config.privateKeyTextSelector) {
          $(config.privateKeyTextSelector).removeClass("d-none");
        }
      });
    }
  }

  /**
   * Starts camera scanning to read private-key QR links.
   * @param {Object} config
   */
  function bindPrivateQrScanner(config) {
    if (!config.privateScanButtonSelector) {
      return;
    }

    $(config.privateScanButtonSelector).on("click", function () {
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

                if (config.scanResultSelector) {
                  $(config.scanResultSelector).text("QR Result : " + code.data);
                }

                if (config.requirePrivateKeyParam && code.data.indexOf(config.requirePrivateKeyParam) === -1) {
                  alert(config.privateKeyMissingMsg);
                  return;
                }

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
   * Initializes shared device page interactions.
   * @param {Object} config
   */
  function init(config) {
    loadDeviceName(config);
    checkCurrentDevice(config);
    bindSetName(config);
    bindAddDevice(config);
    bindBookmark(config);
    bindAdminEditing(config);
    bindShowQr(config);
    bindPrivateQrScanner(config);
  }

  window.WLPDevicePage = { init: init };
})();
