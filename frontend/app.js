const form = document.querySelector("#add");
const statusLine = document.querySelector("#status");
const list = document.querySelector("#students");
const detail = document.querySelector("#detail");

async function api(path = "", options = {}) {
  const response = await fetch("/api/students" + path, options);
  if (response.status === 204) return;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || "Request failed (" + response.status + ").");
  return body;
}

function report(error) {
  statusLine.textContent = error.message;
}

function action(label, handler) {
  const button = document.createElement("button");
  button.textContent = label;
  button.onclick = () => handler().catch(report);
  return button;
}

async function refresh() {
  const students = await api();
  list.replaceChildren();
  document.querySelector("#empty").hidden = students.length > 0;
  for (const student of students) {
    const row = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = student.name;
    const path = "/" + student.id;
    row.append(name, action("View", async () => {
      const record = await api(path);
      document.querySelector("#record").textContent =
        "#" + record.id + " · " + record.name + " · " + record.email;
      detail.hidden = false;
      statusLine.textContent = "";
    }), action("Delete", async () => {
      if (!confirm("Delete " + student.name + "?")) return;
      await api(path, {method: "DELETE"});
      detail.hidden = true;
      statusLine.textContent = student.name + " deleted.";
      await refresh();
    }));
    list.append(row);
  }
}

form.onsubmit = async (event) => {
  event.preventDefault();
  try {
    const student = await api("", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    form.reset();
    statusLine.textContent = student.name + " added.";
    await refresh();
  } catch (error) {
    report(error);
  }
};

refresh().catch(report);
