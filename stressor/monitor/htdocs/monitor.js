const pollMap = { 0: 0, 1: 60000, 2: 30000, 3: 10000, 4: 3000, 5: 1000 };

let interval = 3000;
let pollTimer = null;

function toggleClassByPrefix(elemOrSelector, prefix, addName = null) {
  const regex = new RegExp("\\b" + prefix + "[^ ]*[ ]?\\b", "g");

  function _process(elem) {
    elem.className = elem.className.replace(regex, "");
    if (addName) {
      elem.classList.add(addName)
    }
  }
  if (typeof elemOrSelector === "string") {
    for (let elem of document.querySelectorAll(selector)) {
      _process(elem)
    }
  } else {
    _process(elemOrSelector)
  }
}

function poll() {
  const tag = "Poll status from stressor";
  console.time(tag);

  for (let elem of document.querySelectorAll(".flash-on-update")) {
    elem.classList.remove("flash");
  }

  fetch("getStats")
    .then((response) => response.json())
    .then((data) => {
      for (let elem of document.querySelectorAll(".flash-on-update")) {
        elem.classList.add("flash");
      }
      update(data);
      pollTimer = setTimeout(poll, interval);
    })
    .catch((err) => {
      console.error("ERROR", err);
      const sc = document.getElementById("statusContainer")
      sc.textContent = JSON.stringify(err)
      sc.classList.add("error");
    })
    .finally(() => {
      console.timeEnd(tag);
    });
}

function updateTable(table, data, emptyMsg) {
  const tbody = table.tBodies[0];
  // The lowest header row defines column style:
  const colgroup = table.getElementsByTagName("colgroup")[0].children;
  const colCount = colgroup.length;

  if (!data || !data.length) {
    emptyMsg = emptyMsg || "No data.";
    tbody.innerHTML = `<tr class="no-data"><td colspan="${colCount}">${emptyMsg}</td></tr>`;
    return;
  }
  tbody.innerHTML = "";
  data.forEach((row, i) => {
    const tr = table.insertRow(i);
    row.cols.forEach((val, j) => {
      const cell = tr.insertCell(j);
      if (typeof val === "number") {
        cell.innerHTML = val.toLocaleString();
      } else {
        cell.innerHTML = val;
      }
      // Copy class from related <col> element
      const cl = colgroup[j].classList;
      cell.classList = cl;
      if (cl.contains("err-text") && val !== "n.a.") {
        cell.classList.add("warn");
      }
      if (cl.contains("err-num")) {
        cell.classList.add(val === 0 ? "ok" : "warn");
        if (val > 0 && row.key) {
          cell.innerHTML =
            "<a href='getErrorInfo?type=" +
            row.type +
            "&key=" +
            row.key +
            "' target=_blank>" +
            // " <img src='info_red_16.png' width=16 heigth=16> &nbsp;" +
            cell.innerHTML +
            "</a>";
        }
      }
    });
    tbody.appendChild(tr);
  });
}

function update(result) {
  let table;
  const stage = result.stage;

  document.getElementById("btnStop").toggleAttribute("disabled",
    !(stage === "running" || stage === "waiting")
  )
  document.getElementById("baseUrl").setAttribute("href", result.baseUrl);
  document.getElementById("version").textContent = result.version;

  for (let elem of document.querySelectorAll("span.value")) {
    elem.textContent = result[elem.dataset.value];
  }

  const body = document.querySelector("body")
  toggleClassByPrefix(body, "stage-", "stage-" + result.stage)
  body.classList.toggle("has-errors", !!result.hasErrors)

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

/* -----------------------------------------------------------------------------
 *  
 */

document.addEventListener("DOMContentLoaded", (event) => {
  console.info("Document loaded.");

  document.getElementById("btnStop").addEventListener("click", (event) => {
    event.target.disabled = true;
    fetch("stopManager")
      .catch((err) => {
        console.error(err);
      })
      .finally(() => {
        clearTimeout(pollTimer);
        event.target.textContent = "Cancelled.";
      });
  });

  document.getElementById("pollFreq").addEventListener("change", (event) => {
    interval = parseInt(event.target.value, 10);
    interval = pollMap[interval];
    clearTimeout(pollTimer);
    if (interval) {
      poll();
    }
  });

  setTimeout(() => {
    poll();
  }, 1000);
})
