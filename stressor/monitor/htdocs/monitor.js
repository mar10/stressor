(function() {
  var interval = 3000,
    pollTimer = null,
    pollMap = { 0: 0, 1: 60000, 2: 30000, 3: 10000, 4: 3000, 5: 1000 };

  function poll() {
    const tag = "Poll status from stressor";
    console.time(tag);
    $(".flash-on-update").removeClass("flash");
    $.ajax({
      url: "getStats"
      // data: { arg1: "bar" }
    })
      .done(function(result) {
        $(".flash-on-update").addClass("flash");
        update(result);
        pollTimer = setTimeout(poll, interval);
      })
      .fail(function(err) {
        status = "error";
        console.error("ERROR: " + JSON.stringify(err), arguments);
        $("#statusContainer")
          .text(JSON.stringify(err))
          .addClass("error");
        // alert("Ajax error")
        // pollTimer = setTimeout(poll, interval);
      })
      .always(function() {
        console.timeEnd(tag);
      });
  }

  function updateTable(table, data, emptyMsg) {
    var tbody = table.tBodies[0];
    // The lowest header row defines column style:
    var colgroup = table.getElementsByTagName("colgroup")[0].children;
    var colCount = colgroup.length;

    // console.log(data, colCount);

    if (!data || !data.length) {
      emptyMsg = emptyMsg || "No data.";
      tbody.innerHTML = `<tr class="no-data"><td colspan="${colCount}">${emptyMsg}</td></tr>`;
      return;
    }
    tbody.innerHTML = "";
    data.forEach((row, i) => {
      var tr = table.insertRow(i);
      row.forEach((val, j) => {
        var cell = tr.insertCell(j);
        if (typeof val === "number") {
          cell.innerHTML = val.toLocaleString();
        } else {
          cell.innerHTML = val;
        }
        // Copy class from related <col> element
        var cl = colgroup[j].classList;
        cell.classList = cl;
        if (cl.contains("err-num")) {
          cell.classList.add(val === 0 ? "ok" : "warn");
        }
      });
      tbody.appendChild(tr);
    });
  }

  function update(result) {
    var table,
      stage = result.stage;

    $("#btnStop").attr(
      "disabled",
      !(stage === "running" || stage === "waiting")
    );

    $("span.value").each(function() {
      var $this = $(this);
      $this.text(result[$this.data("value")]);
    });
    $("body")
      .removeClass(function(index, className) {
        return (className.match(/(^|\s)stage-\S+/g) || []).join(" ");
      })
      .addClass("stage-" + result.stage)
      .toggleClass("has-errors", !!result.hasErrors);

    table = document.getElementById("run-metrics");
    updateTable(table, result.stats.seq_stats); //, result.sessions);

    table = document.getElementById("session-metrics");
    updateTable(table, result.stats.sess_stats);

    table = document.getElementById("special-metrics");
    updateTable(
      table,
      result.stats.act_stats,
      "No data (use `monitor` option to mark activities)."
    );
  }

  console.info("loaded...");
  // alert("loaded...");
  $(function() {
    console.info("start...");
    // alert("start...");
    $("#btnStop").on("click", function() {
      $(this).prop("disabled", true);
      $.ajax({ url: "stopManager" }).done(function(result) {
        clearTimeout(pollTimer);
        $("#btnStop").text("Cancelled.");
      });
    });
    $("#pollFreq").on("change", function() {
      interval = parseInt($(this).val(), 10);
      interval = pollMap[interval];
      clearTimeout(pollTimer);
      if (interval) {
        poll();
      }
    });
    setTimeout(function() {
      poll();
    }, 1000);
  });
})();
