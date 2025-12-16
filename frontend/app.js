const { createApp } = Vue;
const api_url = 'https://api.rag.ac.cn/api';
createApp({
  data() {
    return {
      searchQuery: '',
      hasSearched: false,
      isLoading: false,
      results: [],
      recommendedQueries: [],
      currentPage: 1,
      itemsPerPage: 10,
      stats: null,
      searchTimer: 0,
      timerInterval: null,
      // Search parameters
      queryUnderstanding: false,
      smartRerank: true,
      useCache: true,
      socialImpact: false,
      cacheMessage: '',
      sortBy: 'relevance', // 'relevance' or 'social_impact'
      selectedIndexingFields: ['metadata', 'introduction', 'section', 'roc'],
      indexingFieldOptions: [
        { value: 'metadata', label: 'Meta Info' },
        { value: 'introduction', label: 'Introduction' },
        { value: 'section', label: 'Full Paper' },
        { value: 'roc', label: 'RoC' }
      ],
      isDropdownOpen: false,
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.sortedResults.length / this.itemsPerPage);
    },
    sortedResults() {
      if (!this.results || this.results.length === 0) {
        return [];
      }
      
      // Create a copy to avoid mutating original array
      const resultsCopy = [...this.results];
      
      if (this.sortBy === 'social_impact') {
        // Sort by social_score (descending), treat null/undefined as 0
        return resultsCopy.sort((a, b) => {
          const scoreA = a.social_score ?? 0;
          const scoreB = b.social_score ?? 0;
          return scoreB - scoreA;
        });
      }
      
      // Default: keep original order (relevance)
      return resultsCopy;
    },
    paginatedResults() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.sortedResults.slice(start, end);
    },
    formattedTimer() {
      return this.searchTimer.toFixed(1);
    },
    selectedFieldsText() {
      if (this.selectedIndexingFields.length === 0) {
        return 'Select fields...';
      }
      const labels = this.selectedIndexingFields.map(value => {
        const option = this.indexingFieldOptions.find(opt => opt.value === value);
        return option ? option.label : value;
      });
      return labels.join(', ');
    }
  },
  async mounted() {
    await this.loadConfig();
    await this.loadStats();
    document.addEventListener('click', this.closeDropdown);
  },
  beforeUnmount() {
    // Clean up timer when component unmounts
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
    document.removeEventListener('click', this.closeDropdown);
  },
  methods: {
    async loadConfig() {
      try {
        const response = await fetch(`${api_url}/config`);
        const config = await response.json();
        this.recommendedQueries = config.recommended_queries;
      } catch (error) {
        console.error('Error loading config:', error);
        // Fallback to default queries
        this.recommendedQueries = ['Deep Learning', 'Quantum Computing', 'Federated Learning'];
      }
    },
    async searchPapers(query) {
      try {
        // Build URL with parameters
        const params = new URLSearchParams();
        params.append('query', query);
        params.append('query_understanding', this.queryUnderstanding);
        params.append('smart_rerank', this.smartRerank);
        params.append('use_cache', this.useCache);
        params.append('social_impact', this.socialImpact);
        // Add selected indexing fields as multiple parameters
        this.selectedIndexingFields.forEach(field => {
          params.append('indexing_fields', field);
        });
        
        const url = `${api_url}/deep_search?${params.toString()}`;
        console.log('Deep search URL:', url);
        const response = await fetch(url);
        const data = await response.json();
        
        // Check if response includes cache info
        if (data.cache_info) {
          this.cacheMessage = data.cache_info;
          this.results = data.results || [];
        } else {
          this.cacheMessage = '';
          this.results = data;
        }
      } catch (error) {
        console.error('Error searching papers:', error);
        this.results = [];
        this.cacheMessage = '';
      }
    },
    async loadStats() {
      try {
        const response = await fetch(`${api_url}/stats`);
        this.stats = await response.json();
      } catch (error) {
        console.error('Error loading stats:', error);
      }
    },
    async handleSearch() {
      if (!this.searchQuery.trim()) {
        return;
      }
      
      this.hasSearched = true;
      this.isLoading = true;
      this.currentPage = 1; // Reset to first page
      
      // Start timer
      this.searchTimer = 0;
      this.timerInterval = setInterval(() => {
        this.searchTimer += 0.1;
      }, 100);
      
      // Call searchPapers API
      try {
        await this.searchPapers(this.searchQuery);
      } catch (error) {
        console.error('Error in handleSearch:', error);
        this.results = [];
      } finally {
        this.isLoading = false;
        
        // Stop timer
        if (this.timerInterval) {
          clearInterval(this.timerInterval);
          this.timerInterval = null;
        }
      }
    },
    searchWithQuery(query) {
      this.searchQuery = query;
      this.handleSearch();
    },
    clearSearch() {
      this.searchQuery = '';
      this.hasSearched = false;
      this.results = [];
      this.currentPage = 1;
      this.searchTimer = 0;
      this.cacheMessage = '';
      // Clear timer if running
      if (this.timerInterval) {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
      }
    },
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page;
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    },
    toggleDropdown() {
      this.isDropdownOpen = !this.isDropdownOpen;
    },
    toggleField(value) {
      const index = this.selectedIndexingFields.indexOf(value);
      if (index > -1) {
        this.selectedIndexingFields.splice(index, 1);
      } else {
        this.selectedIndexingFields.push(value);
      }
    },
    isFieldSelected(value) {
      return this.selectedIndexingFields.includes(value);
    },
    getSocialColor(score) {
      if (score === null || score === undefined) return '';
      // Gradient from blue (cold) to red (hot)
      // 0-30: blue shades, 31-60: green/yellow, 61-100: orange/red
      if (score <= 30) {
        const intensity = Math.floor((score / 30) * 100);
        return `hsl(210, 80%, ${85 - intensity * 0.3}%)`;
      } else if (score <= 60) {
        const intensity = Math.floor(((score - 30) / 30) * 100);
        return `hsl(${120 - intensity * 0.6}, 70%, ${65 - intensity * 0.15}%)`;
      } else {
        const intensity = Math.floor(((score - 60) / 40) * 100);
        return `hsl(${30 - intensity * 0.3}, ${80 + intensity * 0.15}%, ${55 - intensity * 0.15}%)`;
      }
    },
    setSortBy(sortType) {
      this.sortBy = sortType;
      this.currentPage = 1; // Reset to first page when sorting changes
    },
    closeDropdown(event) {
      // Close dropdown when clicking outside
      if (!this.$el.querySelector('.custom-dropdown').contains(event.target)) {
        this.isDropdownOpen = false;
      }
    }
  }
}).mount('#app');