const state = { services: [], selectedService: null, selectedTime: null };
const $ = (selector) => document.querySelector(selector);
const money = (value) => value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

function showScreen(name) {
  ["catalogScreen", "scheduleScreen", "successScreen"].forEach((id) => {
    document.getElementById(id).hidden = id !== `${name}Screen`;
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
  document.getElementById("app").focus({ preventScroll: true });
}

async function loadServices() {
  const list = $("#serviceList");
  try {
    const response = await fetch("/api/servicos");
    if (!response.ok) throw new Error("Falha ao carregar");
    state.services = await response.json();
    list.innerHTML = state.services.map((service) => `
      <article class="service-card">
        <div><h3>${service.nome}</h3><p>${service.duracao} min</p></div>
        <div style="text-align:right"><span class="price">${money(service.preco)}</span>
          <button class="select-button" type="button" data-service="${service.id}" aria-label="Selecionar ${service.nome}">SELECIONAR</button></div>
      </article>`).join("");
  } catch (_) {
    list.innerHTML = '<p class="message" role="alert">Não foi possível carregar os serviços. Recarregue a página.</p>';
  }
}

function populateServiceSelect() {
  const select = $("#serviceSelect");
  select.innerHTML = state.services.map((service) => `<option value="${service.id}">${service.nome} — ${money(service.preco)}</option>`).join("");
  if (state.selectedService) select.value = String(state.selectedService.id);
  updateServiceSummary();
}

function updateServiceSummary() {
  const id = Number($("#serviceSelect").value);
  state.selectedService = state.services.find((service) => service.id === id) || null;
  $("#serviceSummary").textContent = state.selectedService
    ? `${state.selectedService.duracao} minutos • ${money(state.selectedService.preco)}` : "";
}

function openScheduling(serviceId) {
  if (serviceId) state.selectedService = state.services.find((service) => service.id === Number(serviceId)) || null;
  showScreen("schedule");
  populateServiceSelect();
  history.pushState({}, "", "/agendar");
}

async function loadTimes() {
  const date = $("#dateInput").value;
  const grid = $("#timeGrid");
  state.selectedTime = null;
  grid.innerHTML = "";
  if (!date) return;
  grid.innerHTML = '<p class="loading">Consultando horários…</p>';
  try {
    const response = await fetch(`/api/agendamentos?data=${encodeURIComponent(date)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    grid.innerHTML = data.disponiveis.length ? data.disponiveis.map((time) =>
      `<button class="time-pill" type="button" role="radio" aria-checked="false" data-time="${time}">${time}</button>`
    ).join("") : '<p class="message">Não há horários disponíveis nesta data.</p>';
  } catch (error) {
    grid.innerHTML = `<p class="message" role="alert">${error.message}</p>`;
  }
}

function maskPhone(input) {
  let digits = input.value.replace(/\D/g, "").slice(0, 11);
  if (digits.length > 2) digits = `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length > 10) digits = `${digits.slice(0, 10)}-${digits.slice(10)}`;
  input.value = digits;
}

function showFormMessage(text) {
  const message = $("#formMessage");
  message.textContent = text;
  message.hidden = false;
}

async function submitAppointment(event) {
  event.preventDefault();
  const name = $("#customerName").value.trim();
  const phone = $("#customerPhone").value;
  const date = $("#dateInput").value;
  if (!state.selectedService) return showFormMessage("Selecione um serviço.");
  if (!date) return showFormMessage("Selecione uma data.");
  if (!state.selectedTime) return showFormMessage("Selecione um horário disponível.");
  if (name.length < 3) return showFormMessage("Informe seu nome completo.");
  if (phone.replace(/\D/g, "").length !== 11) return showFormMessage("Informe um telefone válido com DDD.");

  const button = $("#confirmButton");
  button.disabled = true;
  button.textContent = "CONFIRMANDO…";
  $("#formMessage").hidden = true;
  try {
    const response = await fetch("/api/agendamentos", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ service_id: state.selectedService.id, data: date, hora: state.selectedTime, nome: name, telefone: phone })
    });
    const data = await response.json();
    if (!response.ok) throw { status: response.status, message: data.error };
    renderConfirmation(data);
    showScreen("success");
    history.pushState({}, "", "/sucesso");
  } catch (error) {
    showFormMessage(error.status === 409 ? `CONFLITO: ${error.message}` : `ERRO: ${error.message || "Não foi possível concluir o agendamento."}`);
    if (error.status === 409) loadTimes();
  } finally {
    button.disabled = false;
    button.textContent = "CONFIRMAR AGENDAMENTO";
  }
}

function renderConfirmation(data) {
  const date = new Date(`${data.data}T12:00:00`).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
  $("#appointmentSummary").innerHTML = `
    <div><dt>Serviço</dt><dd>${data.servico}</dd></div>
    <div><dt>Data</dt><dd>${date}</dd></div>
    <div><dt>Hora</dt><dd>${data.hora}</dd></div>
    <div><dt>Nome do Cliente</dt><dd>${data.nome}</dd></div>
    <div><dt>Telefone</dt><dd>${data.telefone}</dd></div>
    <div><dt>Preço</dt><dd>${money(data.preco)}</dd></div>`;
}

function goHome(event) {
  event?.preventDefault();
  showScreen("catalog");
  history.pushState({}, "", "/");
}

const today = new Date();
const localToday = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
$("#dateInput").min = localToday;

loadServices();

$("#serviceList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-service]");
  if (button) openScheduling(button.dataset.service);
});
$("#serviceSelect").addEventListener("change", updateServiceSummary);
$("#dateInput").addEventListener("change", loadTimes);
$("#customerPhone").addEventListener("input", (event) => maskPhone(event.target));
$("#timeGrid").addEventListener("click", (event) => {
  const button = event.target.closest("[data-time]");
  if (!button) return;
  document.querySelectorAll("[data-time]").forEach((item) => { item.classList.remove("selected"); item.setAttribute("aria-checked", "false"); });
  button.classList.add("selected"); button.setAttribute("aria-checked", "true"); state.selectedTime = button.dataset.time;
});
$("#appointmentForm").addEventListener("submit", submitAppointment);
$("[data-action='back']").addEventListener("click", goHome);
document.querySelectorAll("[data-action='home'], [data-action='services']").forEach((link) => link.addEventListener("click", goHome));
$("[data-action='agenda']").addEventListener("click", (event) => { event.preventDefault(); openScheduling(); });

const path = location.pathname;
if (path === "/agendar") openScheduling();
else if (path === "/sucesso") showScreen("success");
else showScreen("catalog");
