(function() {
  var interval = 3000,
    pollTimer = null,
    pollMap = {0: 0, 1: 60000, 2:30000, 3: 10000, 4: 3000, 5: 1000},
    status = null;

  function poll() {
    console.time("Poll status from stressor");
    $.ajax({
      url: "getStats",
      data: { arg1: "bar" }
    })
      .done(function(result) {
        console.timeEnd("Poll status from stressor");
        update(result);
        pollTimer = setTimeout(poll, interval);
      })
      .fail(function(err) {
        status = "error";
        console.error("ERROR: " + JSON.stringify(err), arguments);
        $("#statusContainer")
          .text(JSON.stringify(err))
          .addClass("error");
        // alert("ERROR\n" + JSON.stringify(err));
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
        cell.innerHTML = val;
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

    $("span.stage").text(stage);
    $("span.name").text(result.name);
    $("#btnStop").attr(
      "disabled",
      !(stage === "running" || stage === "waiting")
    );

    $("body")
      .removeClass(function(index, className) {
        return (className.match(/(^|\s)stage-\S+/g) || []).join(" ");
      })
      .addClass("stage-" + result.stage)
      .toggleClass("has-errors", !!result.hasErrors);

    // $("#statusContainer").text(JSON.stringify(result));

    table = document.getElementById("run-metrics");
    updateTable(table, result.stats.seq_stats, result.sessions);

    table = document.getElementById("session-metrics");
    updateTable(table, result.sessions);

    table = document.getElementById("special-metrics");
    updateTable(
      table,
      result.stats.act_stats,
      "No data (use `monitor` option to mark activities)."
    );
  }

  $(function() {
    $("#btnStop").on("click", function() {
      $(this).prop("disabled", true);
      $.ajax({ url: "stopManager" }).done(function(result) {
        clearTimeout(pollTimer);
        $("#btnStop").text("Cancelled.");
      });
    });
    $("#pollFreq").on("change", function(){
      interval = parseInt($(this).val(), 10);
      interval = pollMap[interval];
      // console.info(interval, pollMap[interval])
      clearTimeout(pollTimer);
      if(interval){
        poll();
        // pollTimer = setTimeout(poll, interval);
      }
    });
    poll();
  });
})();
