const API_BASE_URL = "http://127.0.0.1:8000";

const statusElement = document.getElementById("leaderboard-status");
const tableElement = document.getElementById("leaderboard-table");
const tableBodyElement = tableElement.querySelector("tbody");

async function loadLeaderboard() {
  try {
    const response = await fetch(`${API_BASE_URL}/leaderboard`);
    if (!response.ok) {
      throw new Error("Could not load leaderboard.");
    }

    const data = await response.json();
    renderLeaderboard(data.leaders);
  } catch (error) {
    statusElement.textContent = "Could not load leaderboard. Start the backend and try again.";
  }
}

function renderLeaderboard(leaders) {
  tableBodyElement.innerHTML = "";

  leaders.forEach((leader, index) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${index + 1}</td>
      <td>
        <div class="leader-cell">
          <img class="leader-thumb" src="${leader.photo_url}" alt="${leader.name}" />
          <strong>${leader.name}</strong>
        </div>
      </td>
      <td>${leader.country}</td>
      <td>${leader.elo}</td>
      <td>${leader.wins}</td>
      <td>${leader.losses}</td>
    `;
    tableBodyElement.appendChild(row);
  });

  statusElement.classList.add("hidden");
  tableElement.classList.remove("hidden");
}

loadLeaderboard();
