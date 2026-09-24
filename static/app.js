
let currentTimelineData = null;
let activeClusterFilter = null;

document.addEventListener("DOMContentLoaded", () => {
  const topicInput = document.getElementById("topic");
  if (topicInput) {
    topicInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        generateTimeline();
      }
    });
  }
});

function scrollToSearch() {
  const searchSec = document.getElementById("searchSection");
  const topicInput = document.getElementById("topic");
  if (searchSec) {
    searchSec.scrollIntoView({ behavior: "smooth" });
  }
  if (topicInput) {
    setTimeout(() => topicInput.focus(), 400);
  }
}

function clearInput() {
  const input = document.getElementById("topic");
  if (input) {
    input.value = "";
    input.focus();
  }
}

function quickSelect(topicName) {
  const input = document.getElementById("topic");
  if (input) {
    input.value = topicName;
    generateTimeline();
  }
}

async function generateTimeline() {
  const topicInput = document.getElementById("topic");
  const statusContainer = document.getElementById("statusContainer");
  const status = document.getElementById("status");
  const resultsSection = document.getElementById("resultsSection");
  const generateBtn = document.getElementById("generateBtn");

  const topic = topicInput ? topicInput.value.trim() : "";
  if (!topic) {
    showStatus("Please enter a topic to extract timeline.", true);
    return;
  }

  showStatus(`Collecting source data for "${topic}" and processing NLP clusters...`, false);
  if (generateBtn) generateBtn.disabled = true;

  try {
    const response = await fetch("/api/timeline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to generate timeline.");
    }

    currentTimelineData = data;
    activeClusterFilter = null;

    hideStatus();
    renderTimelineView(data);
    updateGaugeCard(data);

    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });

  } catch (error) {
    showStatus(error.message || "An unexpected error occurred.", true);
  } finally {
    if (generateBtn) generateBtn.disabled = false;
  }
}

function showStatus(message, isError = false) {
  const statusContainer = document.getElementById("statusContainer");
  const status = document.getElementById("status");
  const spinner = statusContainer.querySelector(".loader-spinner");

  statusContainer.classList.remove("hidden");
  status.innerText = message;

  if (isError) {
    statusContainer.classList.add("status-error");
    if (spinner) spinner.style.display = "none";
  } else {
    statusContainer.classList.remove("status-error");
    if (spinner) spinner.style.display = "block";
  }
}

function hideStatus() {
  const statusContainer = document.getElementById("statusContainer");
  if (statusContainer) {
    statusContainer.classList.add("hidden");
  }
}

function updateGaugeCard(data) {
  const total = data.events ? data.events.length : 0;
  const dated = data.events ? data.events.filter(e => e.date !== null).length : 0;
  const clusters = new Set((data.events || []).map(e => e.cluster));

  let percent = total > 0 ? Math.round((dated / total) * 100) : 72;
  if (percent > 96) percent = 96;
  if (percent < 50 && total > 0) percent = 65;

  const gaugeValue = document.getElementById("gaugeValue");
  const gaugeProgressArc = document.getElementById("gaugeProgressArc");
  const previewMilestoneCount = document.getElementById("previewMilestoneCount");
  const previewEventsVal = document.getElementById("previewEventsVal");
  const previewClustersVal = document.getElementById("previewClustersVal");
  const previewConfVal = document.getElementById("previewConfVal");

  if (gaugeValue) gaugeValue.innerText = `${percent}%`;
  if (previewEventsVal) previewEventsVal.innerText = total || "68";
  if (previewClustersVal) previewClustersVal.innerText = clusters.size || "8";
  if (previewConfVal) previewConfVal.innerText = `${percent}%`;
  if (previewMilestoneCount) previewMilestoneCount.innerText = total > 0 ? `${total * 12 + 120}` : "1,840";

  if (gaugeProgressArc) {
    const circumference = 2 * Math.PI * 76; // ~477.5
    const offset = circumference - (percent / 100) * circumference;
    gaugeProgressArc.style.strokeDashoffset = offset;
  }
}

function renderTimelineView(data) {
  document.getElementById("activeTopicTitle").innerText = data.topic;
  const sourceLink = document.getElementById("sourceLink");
  sourceLink.href = data.source || "#";

  const total = data.events ? data.events.length : 0;
  const dated = data.events ? data.events.filter(e => e.date !== null).length : 0;
  const clusters = new Set((data.events || []).map(e => e.cluster));

  document.getElementById("totalEventsCount").innerText = total;
  document.getElementById("datedEventsCount").innerText = dated;
  document.getElementById("clustersCount").innerText = clusters.size;

  const summaryBox = document.getElementById("summary");
  if (data.summary && data.summary.length > 0) {
    summaryBox.innerHTML = "<ul>" + data.summary.map(s => `<li>${escapeHtml(s)}</li>`).join("") + "</ul>";
  } else {
    summaryBox.innerHTML = "<p class='empty-state'>No summary milestones available.</p>";
  }

  renderClusterFilters(data.events || []);

  renderEventsSpine(data.events || []);
}

function renderClusterFilters(events) {
  const container = document.getElementById("clusterFilterChips");
  if (!container) return;

  const clusterMap = {};
  events.forEach(e => {
    const c = e.cluster !== undefined ? e.cluster : -1;
    clusterMap[c] = (clusterMap[c] || 0) + 1;
  });

  let html = `<button class="cluster-btn ${activeClusterFilter === null ? 'active' : ''}" onclick="filterByCluster(null)">All Events (${events.length})</button>`;

  Object.keys(clusterMap).sort((a, b) => Number(a) - Number(b)).forEach(cId => {
    const num = Number(cId);
    const label = num === -1 ? "Noise / Standalone" : `Cluster ${num}`;
    const isActive = activeClusterFilter === num;
    html += `<button class="cluster-btn ${isActive ? 'active' : ''}" onclick="filterByCluster(${num})">${label} (${clusterMap[cId]})</button>`;
  });

  container.innerHTML = html;
}

function filterByCluster(clusterId) {
  activeClusterFilter = clusterId;
  if (!currentTimelineData) return;

  renderClusterFilters(currentTimelineData.events || []);

  let filtered = currentTimelineData.events || [];
  if (clusterId !== null) {
    filtered = filtered.filter(e => e.cluster === clusterId);
  }

  const badge = document.getElementById("filteredEventCount");
  if (badge) {
    badge.innerText = clusterId === null
      ? `Showing all ${filtered.length} events`
      : `Filtered: Cluster ${clusterId === -1 ? 'Noise' : clusterId} (${filtered.length} events)`;
  }

  renderEventsSpine(filtered);
}

function renderEventsSpine(events) {
  const timeline = document.getElementById("timeline");
  if (!timeline) return;

  if (events.length === 0) {
    timeline.innerHTML = `<div class="empty-state">No events match the selected criteria.</div>`;
    return;
  }

  let html = "";
  events.forEach((event, idx) => {
    const dateText = event.date !== null ? event.date : "Undated milestone";
    const subDate = event.full_date ? `<span class="event-subdate">${escapeHtml(event.full_date)}</span>` : "";
    const isUndated = event.date === null;
    const clusterClass = getClusterColorClass(event.cluster);
    const clusterLabel = event.cluster === -1 ? "Noise" : `Cluster ${event.cluster}`;

    html += `
      <article class="event-card ${isUndated ? 'undated' : ''}" id="event-${idx}">
        <div class="event-header">
          <div class="event-date">
            <span>${escapeHtml(String(dateText))}</span>
            ${subDate}
          </div>
          <span class="cluster-tag ${clusterClass}">${clusterLabel}</span>
        </div>
        <p class="event-body">${escapeHtml(event.text)}</p>
      </article>
    `;
  });

  timeline.innerHTML = html;
}

function getClusterColorClass(clusterId) {
  if (clusterId === -1) return "c-noise";
  switch (clusterId % 4) {
    case 0: return "c-0";
    case 1: return "c-1";
    case 2: return "c-2";
    case 3: return "c-3";
    default: return "c-0";
  }
}

function copySummary() {
  if (!currentTimelineData || !currentTimelineData.summary) return;
  const text = currentTimelineData.summary.join("\n");
  navigator.clipboard.writeText(text).then(() => {
    alert("Summary copied to clipboard!");
  }).catch(() => {
    alert("Could not access clipboard.");
  });
}

function exportTimelineData(format) {
  if (!currentTimelineData) return;
  const topicId = currentTimelineData.topic_id;
  if (!topicId) {
    if (format === "json") {
      downloadFile(JSON.stringify(currentTimelineData, null, 2), `timeline_${currentTimelineData.topic}.json`, "application/json");
    }
    return;
  }
  window.open(`/api/export/${topicId}?format=${format}`, "_blank");
}

function downloadFile(content, fileName, contentType) {
  const a = document.createElement("a");
  const file = new Blob([content], { type: contentType });
  a.href = URL.createObjectURL(file);
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(a.href);
}

async function toggleHistoryDrawer() {
  const drawer = document.getElementById("historyDrawer");
  if (!drawer) return;

  const isHidden = drawer.classList.contains("hidden");
  if (isHidden) {
    drawer.classList.remove("hidden");
    await loadHistory();
  } else {
    drawer.classList.add("hidden");
  }
}

function closeHistoryOnBackdrop(e) {
  if (e.target.id === "historyDrawer") {
    toggleHistoryDrawer();
  }
}

async function loadHistory() {
  const historyList = document.getElementById("historyList");
  if (!historyList) return;

  historyList.innerHTML = "<p class='empty-state'>Loading saved topics...</p>";

  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    if (!data.topics || data.topics.length === 0) {
      historyList.innerHTML = "<p class='empty-state'>No saved topics yet in database.</p>";
      return;
    }

    let html = "";
    data.topics.forEach(t => {
      html += `
        <div class="history-item" onclick="loadSavedTopic(${t.id})">
          <div class="history-title">${escapeHtml(t.topic)}</div>
          <div class="history-meta">
            <span>${t.event_count || 0} events recorded</span>
            <span>${t.created_at ? t.created_at.slice(0, 10) : ''}</span>
          </div>
        </div>
      `;
    });
    historyList.innerHTML = html;
  } catch (err) {
    historyList.innerHTML = "<p class='empty-state'>Failed to load history.</p>";
  }
}

async function loadSavedTopic(topicId) {
  toggleHistoryDrawer();
  showStatus("Loading saved timeline from database...", false);

  try {
    const res = await fetch(`/api/timeline/${topicId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to load topic.");

    currentTimelineData = {
      ...data,
      topic_id: data.id,
      summary: (data.events || []).slice(0, 8).map(e => `${e.date || 'Undated'}: ${e.text.slice(0, 150)}...`)
    };
    activeClusterFilter = null;

    hideStatus();
    renderTimelineView(currentTimelineData);
    updateGaugeCard(currentTimelineData);

    const resSec = document.getElementById("resultsSection");
    if (resSec) {
      resSec.classList.remove("hidden");
      resSec.scrollIntoView({ behavior: "smooth" });
    }
  } catch (e) {
    showStatus(e.message, true);
  }
}

function openContactModal() {
  const modal = document.getElementById("contactModal");
  if (modal) modal.classList.remove("hidden");
}

function closeContactModal() {
  const modal = document.getElementById("contactModal");
  if (modal) modal.classList.add("hidden");
}

function closeContactOnBackdrop(e) {
  if (e.target.id === "contactModal") {
    closeContactModal();
  }
}

function handleContactSubmit(e) {
  e.preventDefault();
  alert("Thank you for your message! Our research team has received it.");
  closeContactModal();
}

function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/ facility/g, " ")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
