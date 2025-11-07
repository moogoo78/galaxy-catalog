// Global state
let currentView = 'table';
let currentFilter = null;
let currentCollectionId = null; // Store current collection filter
let gridInstance = null;
let allSpeciesData = []; // Store all data for filtering and row clicks

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
  initializeTaxonomyTree();
  initializeGrid();
  //renderGalleryView(filteredSpecies);
  initializeEventListeners();
  // updateResultsInfo() will be called after Grid.js loads data
});
const STATUS_MAP = {
  1: ['現用有效學名', 'Current combination'],
  2: ['臺灣產亞種之種級原始組合名', 'Original combination of species'],
  3: ['誤拼', 'Misspelling'],
  4: ['過去使用學名', 'Previous accepted name'],
  5: ['同物異名', 'Junior synonym'],
  7: ['誤鑑定', 'Misidentification'],
  8: ['新紀錄種', ''],
  9: ['新種', ''],
  11: ['原始組合名', 'Original combination'],
  12: ['非合法名變異種', ''],
  13: ['過去使用學名之同物異名', ''],
  14: ['同物異名過去使用學名', '']
};

// Initialize Grid.js
function initializeGrid(searchQuery = '', collectionId = null) {
  const baseUrl = '/api/library/1/items';

  // Build URL with query parameters
  const params = new URLSearchParams();
  if (searchQuery) {
    params.append('q', searchQuery);
  }
  if (collectionId) {
    params.append('collection_id', collectionId);
  }
  const urlWithParams = params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;

  const gridSpinner = document.getElementById('gridSpinner');

  // Show spinner
  if (gridSpinner) {
    gridSpinner.classList.remove('hidden');
  }

  // Safety timeout - force hide spinner after 10 seconds regardless
  const hideSpinnerTimeout = setTimeout(() => {
    if (gridSpinner) {
      console.warn('Grid loading took too long, hiding spinner');
      gridSpinner.classList.add('hidden');
    }
  }, 10000);

  gridInstance = new gridjs.Grid({
    columns: [
      {
        id: 'scientificName',
        name: 'Scientific Name',
        formatter: (cell) => gridjs.html(`<em>${cell}</em>`)
      },
      {
        id: 'commonName',
        name: 'Common Name',
        formatter: (cell, row) => {
          return gridjs.html(`${cell}`);
        }
      },
      {
        id: 'otherCommonName',
        name: 'Other Common Name',
        formatter: (cell, row) => {
          return gridjs.html(`${cell}`);
        }
      },
      {
        id: 'status',
        name: 'Status',
        formatter: (cell) => {
          const statusType = (cell === '1') ? 'common' : 'rare';
          const statusText = STATUS_MAP[cell] ? STATUS_MAP[cell][0] : cell;
          return gridjs.html(`<span class="status-badge status-${statusType}">${statusText}</span>`);
        }
      }
    ],
    server: {
      url: urlWithParams,
      then: data => {
        // Store raw data for row clicks and filtering
        allSpeciesData = data;
        console.log(data);
        // Transform data for Grid.js
        return data.items.map(item => [
          item.scientificName || item.name || '',
          item.commonName || item.name_zh || '',
          item.otherCommonName || item.name_zh_other || '',
          item.status_id || '',
        ]);
      },
      total: data => data.total,
      handle: (res) => {
        // Handle the response - Grid.js expects json()
        if (!res.ok) {
          // Hide spinner on error
          if (gridSpinner) {
            gridSpinner.classList.add('hidden');
          }
          return Promise.reject(res);
        }
        gridSpinner.classList.add('hidden');
        return res.json();
      }
    },
    search: false, // Using custom search inputs instead
    sort: true, // Client-side sorting enabled
    // pagination: {
    //   enabled: true,
    //   limit: 20,
    //   summary: true
    // },
    pagination: {
      limit: 20,
      server: {
        url: (prev, page, limit) => {
          const separator = prev.includes('?') ? '&' : '?';
          return `${prev}${separator}limit=${limit}&offset=${page * limit}`;
        }
      }
    },
    style: {
      table: {
        'width': '100%'
      }
    }
  });

  gridInstance.render(document.getElementById('gridTable'));

  // Add click event to rows
  gridInstance.on('rowClick', (...args) => {
    // args[1] is the row event, args[2] is the row data
    const e = args[0];
    const rowData = args[2];

    // Find the species in allSpeciesData by matching scientific name
    if (rowData && rowData.cells && rowData.cells[0]) {
      const scientificName = rowData.cells[0].data;
      const species = allSpeciesData.items.find(s =>
        (s.scientificName || s.scientific_name) === scientificName
      );
      if (species) {
        showSpeciesDetail(species);
      }
    }
  });

  // Update results info after data is loaded
  gridInstance.on('load', () => {
    clearTimeout(hideSpinnerTimeout);
    updateResultsInfo();
    // Hide spinner
    if (gridSpinner) {
      gridSpinner.classList.add('hidden');
    }
  });

  // Also hide spinner on ready event as a fallback
  gridInstance.on('ready', () => {
    clearTimeout(hideSpinnerTimeout);
    setTimeout(() => {
      if (gridSpinner) {
        gridSpinner.classList.add('hidden');
      }
    }, 100);
  });

  // Handle errors
  gridInstance.on('error', (error) => {
    console.error('Grid error:', error);
    clearTimeout(hideSpinnerTimeout);
    if (gridSpinner) {
      gridSpinner.classList.add('hidden');
    }
  });
}

// Reload Grid with search query and/or collection filter
function reloadGridWithSearch(searchQuery, collectionId = undefined) {
  if (gridInstance) {
    // Destroy the old grid instance
    gridInstance.destroy();
  }
  // Update current collection ID if explicitly provided
  if (collectionId !== undefined) {
    currentCollectionId = collectionId;
  }
  // Reinitialize with new search query and collection filter
  initializeGrid(searchQuery, currentCollectionId);
}

// Refresh Grid layout (useful after container resize)
function refreshGridLayout() {
  if (gridInstance) {
    gridInstance.forceRender();
  }
}

// Filter taxonomy tree
function filterTaxonomyTree(searchTerm) {
  const treeNodes = document.querySelectorAll('.tree-node');
  const lowerSearchTerm = searchTerm.toLowerCase().trim();

  if (!lowerSearchTerm) {
    // Show all nodes when search is empty
    treeNodes.forEach(node => {
      node.classList.remove('hidden-by-filter');
    });
    return;
  }

  // First, mark all nodes as hidden
  treeNodes.forEach(node => {
    node.classList.add('hidden-by-filter');
  });

  // Find matching nodes and show them with their ancestors and descendants
  treeNodes.forEach(node => {
    const label = node.querySelector('.tree-label');
    if (label) {
      const text = label.textContent.toLowerCase();

      // If this node matches the search
      if (text.includes(lowerSearchTerm)) {
        // Show this node
        node.classList.remove('hidden-by-filter');

        // Show all ancestors
        let parent = node.parentElement;
        while (parent) {
          if (parent.classList.contains('tree-node')) {
            parent.classList.remove('hidden-by-filter');
          }
          parent = parent.parentElement;
        }

        // Show all descendants
        const descendants = node.querySelectorAll('.tree-node');
        descendants.forEach(desc => {
          desc.classList.remove('hidden-by-filter');
        });

        // Auto-expand matching nodes and their parents
        const childContainer = node.querySelector('.tree-children');
        if (childContainer) {
          childContainer.classList.add('expanded');
          const toggle = node.querySelector('.tree-toggle');
          if (toggle) {
            toggle.textContent = '▼';
          }
        }

        // Expand parent containers
        let parentContainer = node.parentElement;
        while (parentContainer) {
          if (parentContainer.classList.contains('tree-children')) {
            parentContainer.classList.add('expanded');
            const parentNode = parentContainer.parentElement;
            if (parentNode) {
              const toggle = parentNode.querySelector('.tree-toggle');
              if (toggle) {
                toggle.textContent = '▼';
              }
            }
          }
          parentContainer = parentContainer.parentElement;
        }
      }
    }
  });
}

// Initialize event listeners
function initializeEventListeners() {
    // Taxonomy filter
    const taxonomyFilterInput = document.getElementById('taxonomyFilterInput');
    let filterTimeout;

    if (taxonomyFilterInput) {
      taxonomyFilterInput.addEventListener('input', (e) => {
        const searchValue = e.target.value;

        // Debounce filter to improve performance
        clearTimeout(filterTimeout);
        filterTimeout = setTimeout(() => {
          filterTaxonomyTree(searchValue);
        }, 300);
      });
    }

    // Sidebar toggle
    const toggleSidebarBtn = document.getElementById('toggleSidebar');
    const closeSidebarBtn = document.getElementById('closeSidebar');
    const sidebar = document.getElementById('sidebar');

    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        // Wait for sidebar transition to complete, then refresh grid
        setTimeout(() => {
            refreshGridLayout();
        }, 350); // Slightly longer than CSS transition (300ms)
    });

    closeSidebarBtn.addEventListener('click', () => {
        sidebar.classList.remove('open');
        // Wait for sidebar transition to complete, then refresh grid
        setTimeout(() => {
            refreshGridLayout();
        }, 350); // Slightly longer than CSS transition (300ms)
    });

    // Clear filter buttons
    document.getElementById('clearFilter').addEventListener('click', () => {
        clearActiveFilter();
    });

    document.getElementById('clearFilterGallery').addEventListener('click', () => {
        clearActiveFilter();
    });

    // View switching
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
        });
    });

    // Search functionality - Custom search inputs reload grid with search query
    const searchInput = document.getElementById('searchInput');
    const searchInputGallery = document.getElementById('searchInputGallery');
    let searchTimeout;

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchValue = e.target.value;
            if (searchInputGallery) {
                searchInputGallery.value = searchValue;
            }

            // Debounce search to avoid too many API calls
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                reloadGridWithSearch(searchValue);
            }, 500);
        });
    }

    if (searchInputGallery) {
        searchInputGallery.addEventListener('input', (e) => {
            const searchValue = e.target.value;
            if (searchInput) {
                searchInput.value = searchValue;
            }

            // Debounce search to avoid too many API calls
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                reloadGridWithSearch(searchValue);
            }, 500);
        });
    }

    // Back button
    document.getElementById('backBtn').addEventListener('click', () => {
        document.getElementById('speciesDetail').style.display = 'none';
        document.querySelector('.view-container.active').style.display = 'flex';
    });

    // Handle window resize for responsive grid layout
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            refreshGridLayout();
        }, 200);
    });
}

// Switch between table and gallery views
function switchView(view) {
    currentView = view;

    // Hide species detail if visible
    document.getElementById('speciesDetail').style.display = 'none';

    // Update button states
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Update view containers
    document.querySelectorAll('.view-container').forEach(container => {
        container.classList.remove('active');
    });

    if (view === 'table') {
        document.getElementById('tableView').classList.add('active');
    } else {
        document.getElementById('galleryView').classList.add('active');
    }
}

// Search functionality - Now handled by Grid.js server-side search
// The search is automatically performed by Grid.js when the user types in the search box
// No manual filtering is needed as the server handles the search query

// Update results information
function updateResultsInfo() {
    const count = allSpeciesData.items ? allSpeciesData.items.length : 0;
    const infoText = `Showing ${count} species`;

    document.getElementById('resultsInfo').textContent = infoText;
    if (document.getElementById('resultsInfoGallery')) {
        document.getElementById('resultsInfoGallery').textContent = infoText;
    }
}

// Initialize taxonomy tree
function initializeTaxonomyTree() {
  const spinner = document.getElementById('taxonomySpinner');

  fetch('/api/library/1/collections')
    .then(resp => resp.json())
    .then(result => {
      console.log(result);
      const treeContainer = document.getElementById('taxonomyTree');
      result.forEach( root => {
        const rootNode = createTreeNode(root);
        treeContainer.appendChild(rootNode);
      });
    })
    .catch(error => {
      console.error('Error loading taxonomy tree:', error);
      const treeContainer = document.getElementById('taxonomyTree');
      treeContainer.innerHTML = '<div style="padding: 20px; color: #d32f2f;">Failed to load taxonomy tree</div>';
    })
    .finally(() => {
      // Hide spinner
      if (spinner) {
        spinner.style.display = 'none';
      }
    });

}

// Create a tree node
function createTreeNode(data) {
  const node = document.createElement('div');
  node.className = 'tree-node';

  const header = document.createElement('div');
  header.className = 'tree-node-header';

  const toggle = document.createElement('span');
  toggle.className = 'tree-toggle';
  toggle.textContent = '▶';

  const label = document.createElement('span');
  label.className = 'tree-label';
  label.textContent = `${data.name} ${data.name_zh || ''}`;

  const count = document.createElement('span');
  count.className = 'tree-count';

  // Check if node has children
  const hasChildren = data.children && Object.keys(data.children).length > 0;

  // Only add toggle if there are children
  if (hasChildren) {
    header.appendChild(toggle);
  } else {
    // Add invisible placeholder to maintain alignment
    toggle.style.visibility = 'hidden';
    header.appendChild(toggle);
  }

  header.appendChild(label);
  header.appendChild(count);
  node.appendChild(header);

  if (hasChildren) {
    const childContainer = document.createElement('div');
    childContainer.className = 'tree-children';

    let totalSpecies = 0;

    Object.values(data.children).forEach(child => {
      let childNode;
      if (child.level == 'subfamily') { // TODO
        // This is a family node with species
        totalSpecies += (child.children) ? child.children.length : 0;
        childNode = createTreeNode(child);
        childNode.dataset.family = child.name;
        childNode.querySelector('.tree-count').textContent = (child.count) ? child.count : '-';
      } else {
        // This is an intermediate node
        childNode = createTreeNode(child);
        const childSpeciesCount = (child.count) ? child.count : '-';
        totalSpecies += childSpeciesCount;
        childNode.querySelector('.tree-count').textContent = childSpeciesCount;
      }

      childContainer.appendChild(childNode);
    });

    count.textContent = totalSpecies;
    node.appendChild(childContainer);

    // Arrow (toggle) click - only toggles children
    toggle.addEventListener('click', (e) => {
      e.stopPropagation();
      childContainer.classList.toggle('expanded');
      toggle.textContent = childContainer.classList.contains('expanded') ? '▼' : '▶';
    });
  }

  // Label click - triggers filter
  label.addEventListener('click', (e) => {
    e.stopPropagation();
    // Call filter function with the node data
    filterByTaxonomyNode(data);

    // Update selected state
    document.querySelectorAll('.tree-node-header').forEach(h => {
      h.classList.remove('selected');
    });
    header.classList.add('selected');
  });

  return node;
}

// Show active filter indicator
function showActiveFilter(filterName) {
  const activeFilter = document.getElementById('activeFilter');
  const activeFilterGallery = document.getElementById('activeFilterGallery');
  const filterNameEl = document.getElementById('filterName');
  const filterNameGalleryEl = document.getElementById('filterNameGallery');

  if (activeFilter && filterNameEl) {
    filterNameEl.textContent = filterName;
    activeFilter.style.display = 'flex';
  }

  if (activeFilterGallery && filterNameGalleryEl) {
    filterNameGalleryEl.textContent = filterName;
    activeFilterGallery.style.display = 'flex';
  }
}

// Clear active filter
function clearActiveFilter() {
  const activeFilter = document.getElementById('activeFilter');
  const activeFilterGallery = document.getElementById('activeFilterGallery');

  if (activeFilter) {
    activeFilter.style.display = 'none';
  }

  if (activeFilterGallery) {
    activeFilterGallery.style.display = 'none';
  }

  // Clear selected state from tree nodes
  document.querySelectorAll('.tree-node-header').forEach(h => {
    h.classList.remove('selected');
  });

  // Clear collection filter and reload grid
  currentCollectionId = null;
  const searchValue = document.getElementById('searchInput').value;
  reloadGridWithSearch(searchValue, null);
}

// Filter by taxonomy node
function filterByTaxonomyNode(data) {
  console.log('Filter clicked for taxonomy node:', {
    id: data.id,
    name: data.name,
    name_zh: data.name_zh,
    level: data.level,
    count: data.count,
    data: data
  });

  // Show filter indicator
  const filterLabel = data.name_zh ? `${data.name} (${data.name_zh})` : data.name;
  showActiveFilter(filterLabel);

  // Close sidebar on mobile
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
  }

  // Apply collection filter by reloading grid with collection_id
  const searchValue = document.getElementById('searchInput').value;
  reloadGridWithSearch(searchValue, data.id);
}

// Filter by taxonomy (old commented out version)
/*
function filterByTaxonomy(level, value) {
    currentFilter = { level, value };

    filteredSpecies = speciesData.filter(species => matchesFilter(species, currentFilter));

    updateGridData();
    renderGalleryView(filteredSpecies);
    updateResultsInfo();

    // Close sidebar on mobile
    if (window.innerWidth <= 768) {
        document.getElementById('sidebar').classList.remove('open');
    }

    // Clear search
    document.getElementById('searchInput').value = '';
    document.getElementById('searchInputGallery').value = '';
}*/

// Check if species matches filter
function matchesFilter(species, filter) {
    if (!filter) return true;
    return species[filter.level] === filter.value;
}

// Render table view - Now using Grid.js (see initializeGrid and updateGridData functions)
// function renderTableView(species) {
//     const tbody = document.getElementById('tableBody');
//     tbody.innerHTML = '';
//
//     species.forEach(s => {
//         const row = document.createElement('tr');
//         row.innerHTML = `
//             <td>${s.icon} ${s.commonName}</td>
//             <td><em>${s.scientificName}</em></td>
//             <td>${s.family}</td>
//             <td>${s.order}</td>
//             <td><span class="status-badge status-${s.status}">${capitalize(s.status)}</span></td>
//         `;
//
//         row.addEventListener('click', () => showSpeciesDetail(s));
//         tbody.appendChild(row);
//     });
// }

// Render gallery view
function renderGalleryView(species) {
    const grid = document.getElementById('galleryGrid');
    grid.innerHTML = '';

    species.forEach(s => {
        const card = document.createElement('div');
        card.className = 'gallery-card';
        card.innerHTML = `
            <div class="gallery-card-image">${s.icon}</div>
            <div class="gallery-card-content">
                <div class="gallery-card-title">${s.commonName}</div>
                <div class="gallery-card-scientific">${s.scientificName}</div>
                <div class="gallery-card-info">
                    <div><strong>Family:</strong> ${s.family}</div>
                    <div><strong>Order:</strong> ${s.order}</div>
                    <div><span class="status-badge status-${s.status}">${capitalize(s.status)}</span></div>
                </div>
            </div>
        `;

        card.addEventListener('click', () => showSpeciesDetail(s));
        grid.appendChild(card);
    });
}

// Show species detail
function showSpeciesDetail(species) {
    const detailContent = document.getElementById('speciesDetailContent');

    detailContent.innerHTML = `
        <div class="detail-card">
            <div class="detail-header">
                <div class="detail-title">${species.icon} ${species.commonName}</div>
                <div class="detail-scientific">${species.scientificName}</div>
            </div>

            <div class="detail-image">${species.icon}</div>

            <div class="detail-section">
                <h3>Conservation Status</h3>
                <p><span class="status-badge status-${species.status}">${capitalize(species.status)}</span></p>
            </div>

            <div class="detail-section">
                <h3>Description</h3>
                <p>${species.description}</p>
            </div>

            <div class="detail-section">
                <h3>Habitat</h3>
                <p>${species.habitat}</p>
            </div>

            <div class="detail-section">
                <h3>Diet</h3>
                <p>${species.diet}</p>
            </div>

            <div class="detail-section">
                <h3>Taxonomy</h3>
                <ul class="taxonomy-list">
                    <li><strong>Kingdom:</strong> ${species.kingdom}</li>
                    <li><strong>Phylum:</strong> ${species.phylum}</li>
                    <li><strong>Class:</strong> ${species.class}</li>
                    <li><strong>Order:</strong> ${species.order}</li>
                    <li><strong>Family:</strong> ${species.family}</li>
                    <li><strong>Genus:</strong> ${species.genus}</li>
                    <li><strong>Species:</strong> ${species.species}</li>
                </ul>
            </div>
        </div>
    `;

    document.querySelector('.view-container.active').style.display = 'none';
    document.getElementById('speciesDetail').style.display = 'block';
}

// Utility function to capitalize first letter
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
