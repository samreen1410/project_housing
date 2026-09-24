// Lets a city picked on one page (e.g. the Rent Explorer) carry over to
// another (e.g. the Calculator), without needing a framework's state
// management. Backed by sessionStorage — persists across pages in this
// tab, clears when the tab closes.

function setSelectedRegion(regionId, regionName) {
  sessionStorage.setItem("selectedRegionId", regionId);
  sessionStorage.setItem("selectedRegionName", regionName);
}

function getSelectedRegion() {
  const id = sessionStorage.getItem("selectedRegionId");
  const name = sessionStorage.getItem("selectedRegionName");
  return id ? { id: Number(id), name } : null;
}
