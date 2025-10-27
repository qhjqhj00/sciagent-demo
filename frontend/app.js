const { createApp } = Vue;

createApp({
  data() {
    return {
      searchQuery: '',
      hasSearched: false,
      results: [],
      recommendedQueries: [],
      testData: [],
      currentPage: 1,
      itemsPerPage: 10
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
    }
  },
  async mounted() {
    await this.loadConfig();
    await this.loadTestData();
  },
  methods: {
    async loadConfig() {
      try {
        const response = await fetch('http://localhost:12312/api/config');
        const config = await response.json();
        this.recommendedQueries = config.recommended_queries;
      } catch (error) {
        console.error('Error loading config:', error);
        // Fallback to default queries
        this.recommendedQueries = ['Deep Learning', 'Quantum Computing', 'Federated Learning'];
      }
    },
    async loadTestData() {
      try {
        const response = await fetch('http://localhost:12312/api/test_data');
        this.testData = await response.json();
      } catch (error) {
        console.error('Error loading test data:', error);
      }
    },
    async handleSearch() {
      if (!this.searchQuery.trim()) {
        return;
      }
      
      this.hasSearched = true;
      this.currentPage = 1; // Reset to first page
      
      // Simulate API call with delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Return all test data regardless of query
      this.results = this.testData;
    },
    searchWithQuery(query) {
      this.searchQuery = query;
      this.handleSearch();
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

