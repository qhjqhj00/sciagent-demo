const { createApp } = Vue;
const api_url = 'https://api.rag.ac.cn/api';

createApp({
  data() {
    return {
      searchQuery: '',
      deepSearch: false,
      hasSearched: false,
      isLoading: false,
      results: [],
      recommendedQueries: [],
      currentPage: 1,
      itemsPerPage: 10,
      stats: null,
      searchTimer: 0,
      timerInterval: null,
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.results.length / this.itemsPerPage);
    },
    paginatedResults() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.results.slice(start, end);
    },
    formattedTimer() {
      return this.searchTimer.toFixed(1);
    }
  },
  beforeUnmount() {
    // Clean up timer when component unmounts
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  },
  async mounted() {
    await this.loadConfig();
    await this.loadStats();
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
        const endpoint = this.deepSearch ? '/deep_search' : '/search';
        let url;
        let response;
        
        if (endpoint === '/deep_search') {
          // Build URL with debug parameters for deep search
          url = `${api_url}${endpoint}?query=${encodeURIComponent(query)}`;
          console.log('Deep search URL:', url);
          response = await fetch(url);
        } else {
          url = `${api_url}${endpoint}?query=${encodeURIComponent(query)}`;
          console.log('Regular search URL:', url);
          response = await fetch(url);
        }
        this.results = await response.json();
      } catch (error) {
        console.error('Error searching papers:', error);
        this.results = [];
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
    }
  }
}).mount('#app');