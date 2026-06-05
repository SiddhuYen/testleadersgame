const API_BASE_URL = "http://127.0.0.1:8000";

const statusElement = document.getElementById("status");
const matchupElement = document.getElementById("matchup");

async function loadMatchup() {
  showStatus("Loading leaders...");

  try {
    const response = await fetch(`${API_BASE_URL}/matchup`);
    if (!response.ok) {
      throw new Error("Could not load matchup.");
    }

    const data = await response.json();
    renderMatchup(data.leaders);
  } catch (error) {
    showStatus("Could not load the matchup. Start the backend and try again.");
  }
}

function renderMatchup(leaders) {
  matchupElement.innerHTML = "";

  leaders.forEach((leader, index) => {
    const card = document.createElement("button");
    card.className = "leader-card";
    card.type = "button";
    card.innerHTML = `
      <article>
        <img class="leader-photo" src="${leader.photo_url}" alt="${leader.name}" />
        <div class="leader-copy">
          <h2 class="leader-name">${leader.name}</h2>
          <p class="leader-meta">${leader.country}</p>
          <p class="leader-meta">Current Elo: ${leader.elo}</p>
        </div>
      </article>
    `;
    card.addEventListener("click", () => {
      const otherLeader = leaders[(index + 1) % 2];
      submitVote(leader.id, otherLeader.id);
    });
    matchupElement.appendChild(card);
  });

  statusElement.classList.add("hidden");
  matchupElement.classList.remove("hidden");
}

async function submitVote(winnerId, loserId) {
  showStatus("Saving vote...");
  matchupElement.classList.add("hidden");

  try {
    const response = await fetch(`${API_BASE_URL}/vote`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        winner_id: winnerId,
        loser_id: loserId,
      }),
    });

    if (!response.ok) {
      throw new Error("Could not save vote.");
    }

    await loadMatchup();
  } catch (error) {
    showStatus("Vote failed. Check the backend and try again.");
  }
}

function showStatus(message) {
  statusElement.textContent = message;
  statusElement.classList.remove("hidden");
}

loadMatchup();
