/** Radial mind-map renderer for archetype weight trees (D3 v7). */

(function () {
  const KIND_COLORS = {
    weight: "#c084fc",
    tag: "#60a5fa",
    attribute: "#fbbf24",
    attributes: "#fbbf24",
    skill: "#4ade80",
    skills: "#4ade80",
    discipline: "#f87171",
    disciplines: "#f87171",
    background: "#2dd4bf",
    sphere: "#38bdf8",
    modifier: "#a78bfa",
    merit: "#86efac",
    flaw: "#fb923c",
    power: "#e879f9",
    section: "#9ca3af",
    archetype: "#8b1538",
    predator: "#dc2626",
    clan: "#6366f1",
    category: "#0891b2",
    root: "#e8e4dc",
  };

  function biasColor(value) {
    if (value == null) return "#6b7280";
    if (value >= 1.35) return "#4ade80";
    if (value >= 1.05) return "#a3e635";
    if (value >= 0.85) return "#9ca3af";
    if (value >= 0.5) return "#fb923c";
    return "#ef4444";
  }

  function nodeRadius(d) {
    if (d.data.kind === "root" || d.data.kind === "archetype") return 10;
    if (d.data.kind === "section") return 6;
    if (d.data.value != null) return 4 + Math.min(8, Math.abs(d.data.value - 1) * 6);
    return 5;
  }

  function parseTreeData(treeData) {
    if (typeof treeData === "string") {
      return JSON.parse(treeData);
    }
    return treeData;
  }

  function navigateWeightMap(params) {
    const q = new URLSearchParams(params).toString();
    window.location.hash = q ? `weights?${q}` : "weights";
  }

  function handleNodeNav(d) {
    const data = d.data;
    if (!data.nav || !data.lens) return;
    const params = { lens: data.lens, mode: "profile" };
    if (data.lens === "archetype") {
      params.arch = data.id;
      params.sub = data.sub || "";
      params.type = data.type || "vampire";
    } else if (data.lens === "predator" || data.lens === "clan" || data.lens === "category") {
      params.id = data.id;
    }
    navigateWeightMap(params);
  }

  function showCanvasError(container, message) {
    container.innerHTML = "";
    const box = document.createElement("div");
    box.className = "weight-map-error";
    box.textContent = message;
    container.appendChild(box);
  }

  function destroy(container) {
    container.innerHTML = "";
  }

  function renderWeightMap(container, treeData) {
    if (!container) {
      throw new Error("Weight map container missing");
    }
    if (typeof d3 === "undefined") {
      showCanvasError(container, "D3 failed to load. Check your network connection and reload.");
      return false;
    }

    let data;
    try {
      data = parseTreeData(treeData);
    } catch (err) {
      showCanvasError(container, `Invalid weight map data: ${err.message || err}`);
      return false;
    }

    destroy(container);

    const width = Math.min(container.clientWidth || 960, 1100);
    const height = Math.max(640, Math.min(window.innerHeight - 220, 900));
    const outerRadius = Math.min(width, height) / 2 - 48;

    const svg = d3
      .select(container)
      .append("svg")
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .attr("width", "100%")
      .attr("height", height)
      .attr("class", "weight-map-svg")
      .style("max-width", "100%");

    const g = svg.append("g");

    const zoom = d3
      .zoom()
      .scaleExtent([0.35, 3])
      .on("zoom", (event) => g.attr("transform", event.transform));

    svg.call(zoom);

    const root = d3.hierarchy(data);
    const treeLayout = d3
      .tree()
      .size([2 * Math.PI, outerRadius])
      .separation((a, b) => (a.parent === b.parent ? 1 : 1.6) / (a.depth || 1));

    treeLayout(root);

    const linkGen = d3
      .linkRadial()
      .angle((d) => d.x)
      .radius((d) => d.y);

    g.append("g")
      .attr("fill", "none")
      .attr("stroke", "#3f3f50")
      .attr("stroke-opacity", 0.65)
      .selectAll("path")
      .data(root.links())
      .join("path")
      .attr("d", linkGen)
      .attr("stroke-width", (d) => Math.max(0.5, 2.2 - d.target.depth * 0.35));

    const tip = d3
      .select("body")
      .selectAll(".weight-map-tooltip")
      .data([0])
      .join("div")
      .attr("class", "weight-map-tooltip")
      .style("opacity", 0);

    const nodes = g
      .append("g")
      .selectAll("g")
      .data(root.descendants())
      .join("g")
      .attr("transform", (d) => `rotate(${(d.x * 180) / Math.PI - 90}) translate(${d.y},0)`);

    nodes
      .append("circle")
      .attr("r", nodeRadius)
      .attr("fill", (d) => {
        if (d.data.value != null) return biasColor(d.data.value);
        return KIND_COLORS[d.data.kind] || "#9ca3af";
      })
      .attr("stroke", "#0d0d0f")
      .attr("stroke-width", 1.2)
      .style("cursor", (d) => (d.data.nav ? "pointer" : "default"))
      .on("mouseover", function (event, d) {
        d3.select(this).attr("stroke", "#e8e4dc").attr("stroke-width", 2);
        let html = `<strong>${d.data.name}</strong>`;
        if (d.data.value != null) html += `<br/>Bias: <strong>${d.data.value}</strong>`;
        if (d.data.kind) html += `<br/><span class="text-stone-400">${d.data.kind}</span>`;
        if (d.data.id) html += `<br/><code>${d.data.id}</code>`;
        tip.style("opacity", 1).html(html);
      })
      .on("mousemove", (event) => {
        tip.style("left", `${event.pageX + 12}px`).style("top", `${event.pageY - 8}px`);
      })
      .on("mouseout", function () {
        d3.select(this).attr("stroke", "#0d0d0f").attr("stroke-width", 1.2);
        tip.style("opacity", 0);
      })
      .on("click", (_, d) => {
        handleNodeNav(d);
      });

    nodes
      .append("text")
      .attr("dy", "0.31em")
      .attr("x", (d) => (d.x < Math.PI === !d.children ? 8 : -8))
      .attr("text-anchor", (d) => (d.x < Math.PI === !d.children ? "start" : "end"))
      .attr("transform", (d) => (d.x >= Math.PI ? "rotate(180)" : null))
      .attr("font-size", (d) => (d.depth <= 1 ? "11px" : "9px"))
      .attr("fill", "#d6d3d1")
      .text((d) => {
        const label = d.data.name;
        if (d.data.value != null && d.depth > 2) {
          return `${label} (${d.data.value})`;
        }
        return label.length > 22 ? `${label.slice(0, 20)}…` : label;
      })
      .clone(true)
      .lower()
      .attr("stroke", "#0d0d0f")
      .attr("stroke-width", 3)
      .attr("stroke-linejoin", "round")
      .attr("fill", "none");

    return true;
  }

  window.renderWeightMap = renderWeightMap;
  window.weightMapAssetsReady = function () {
    return typeof d3 !== "undefined" && typeof window.renderWeightMap === "function";
  };
})();
