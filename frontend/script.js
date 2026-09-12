const queryInput = document.getElementById("query");
const searchBtn = document.getElementById("searchBtn");

const results = document.getElementById("results");
const resultsTitle = document.getElementById("resultsTitle");
const resultCount = document.getElementById("resultCount");

const agentMessage = document.getElementById("agentMessage");
const agentStatus = document.getElementById("agentStatus");

const steps = [
  document.getElementById("step1"),
  document.getElementById("step2"),
  document.getElementById("step3"),
  document.getElementById("step4")
];

function setStep(index) {
  steps.forEach((step, i) => {
    step.classList.remove("active", "done");

    if (i < index) {
      step.classList.add("done");
    } else if (i === index) {
      step.classList.add("active");
    }
  });
}

function renderResults(opportunities) {
  results.innerHTML = "";

  resultsTitle.textContent = "Opportunities Found";
  resultCount.textContent = `${opportunities.length} results`;

  if (!opportunities.length) {
    results.innerHTML = `
      <div class="empty-state">
        No matching opportunities found.
      </div>
    `;
    return;
  }

  opportunities.forEach((item) => {
    const card = document.createElement("div");
    card.className = "result-card";

    card.innerHTML = `
      <div class="result-card-top">
        <span class="result-type">${item.type || "Opportunity"}</span>
        <span class="result-source">${item.source || "Web"}</span>
      </div>

      <h3>${item.name}</h3>

      ${
        item.deadline
          ? `<p><strong>Deadline:</strong> ${item.deadline}</p>`
          : ""
      }

      ${
        item.eligibility
          ? `<p><strong>Eligibility:</strong> ${item.eligibility}</p>`
          : ""
      }

      ${
        item.location
          ? `<p><strong>Location:</strong> ${item.location}</p>`
          : ""
      }

      ${
        item.link
          ? `<a href="${item.link}" target="_blank">View Opportunity →</a>`
          : ""
      }
    `;

    results.appendChild(card);
  });
}

async function searchOpportunities() {
  const query = queryInput.value.trim();

  if (!query) {
    agentMessage.textContent = "Please enter what you are looking for.";
    return;
  }

  searchBtn.disabled = true;
  searchBtn.textContent = "Agent Running...";

  agentStatus.textContent = "Working";
  agentMessage.textContent = "Starting browser agent...";

  setStep(0);

  results.innerHTML = "";
  resultCount.textContent = "";

  try {
    setStep(0);
    agentMessage.textContent = "Searching live opportunity sources...";

    await new Promise(resolve => setTimeout(resolve, 700));

    setStep(1);
    agentMessage.textContent = "Browsing Devfolio with Webcmd...";

    await new Promise(resolve => setTimeout(resolve, 700));

    setStep(2);
    agentMessage.textContent = "Extracting opportunity information...";

    const response = await fetch("http://localhost:5000/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        query: query
      })
    });

    if (!response.ok) {
      throw new Error("Backend request failed");
    }

    const data = await response.json();

    setStep(3);
    agentMessage.textContent = "Verified results successfully.";
    agentStatus.textContent = "Complete";

    renderResults(data.opportunities || []);

  } catch (error) {
    console.error(error);

    agentStatus.textContent = "Error";
    agentMessage.textContent =
      "The browser agent could not complete the search.";

    results.innerHTML = `
      <div class="empty-state">
        Something went wrong. Make sure the OpportunityScout backend is running.
      </div>
    `;

  } finally {
    searchBtn.disabled = false;
    searchBtn.textContent = "Find Opportunities";
  }
}

searchBtn.addEventListener("click", searchOpportunities);

queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    searchOpportunities();
  }
});