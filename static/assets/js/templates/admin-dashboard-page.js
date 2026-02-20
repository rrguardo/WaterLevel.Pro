(function () {
  /**
   * Builds DataTable columns for sensor/relay device lists.
   * @param {Object} config
   * @returns {Array}
   */
  function buildDeviceColumns(config) {
    return [
      { data: "id" },
      { data: "private_key" },
      {
        data: "public_key",
        render: function (data, type) {
          if (type === "display") {
            return '<a href="' + config.deviceInfoBaseUrl + "?public_key=" + data + '">' + data + "</a>";
          }
          return data;
        },
      },
      { data: "note" },
    ];
  }

  /**
   * Creates a DataTable bound to the admin endpoint and action.
   * @param {string} selector
   * @param {string} action
   * @param {Array} columns
   * @param {Object} config
   */
  function initTable(selector, action, columns, config) {
    var element = document.querySelector(selector);
    if (!element) {
      return;
    }

    new DataTable(selector, {
      layout: {
        bottomEnd: {
          paging: { boundaryNumbers: false },
        },
      },
      ajax: {
        url: config.adminDashboardUrl,
        dataSrc: "",
        type: "POST",
        data: { action: action },
      },
      columns: columns,
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!window.WLP_ADMIN_CONFIG) {
      return;
    }

    var config = window.WLP_ADMIN_CONFIG;

    initTable("#sensors_table", "list-sensor", buildDeviceColumns(config), config);
    initTable("#relays_table", "list-relay", buildDeviceColumns(config), config);
    initTable(
      "#users_table",
      "list-users",
      [{ data: "id" }, { data: "email" }, { data: "phone" }, { data: "confirmed" }],
      config
    );
    initTable(
      "#users_support",
      "list-users-support",
      [
        { data: "id" },
        { data: "email" },
        { data: "message" },
        { data: "created_at" },
        { data: "support_type" },
      ],
      config
    );
  });
})();
