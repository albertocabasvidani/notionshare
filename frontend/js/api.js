// Auto-detect backend URL based on current hostname
// Works for localhost, Windows host IP (172.x.x.x), or production domain
const API_BASE_URL = `http://${window.location.hostname}:8000/api/v1`;

class APIClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            ...options,
            headers: this.getHeaders(),
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth
    async register(email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    }

    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });

        this.token = data.access_token;
        localStorage.setItem('access_token', data.access_token);

        return data;
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    async saveNotionToken(accessToken, workspaceId = null) {
        const params = new URLSearchParams({ access_token: accessToken });
        if (workspaceId) params.append('workspace_id', workspaceId);

        return this.request(`/auth/notion/token?${params}`, {
            method: 'POST',
        });
    }

    // Databases
    async listDatabases() {
        return this.request('/databases/list');
    }

    async getDatabaseStructure(dbId) {
        return this.request(`/databases/${dbId}/structure`);
    }

    async searchPages(query = '') {
        return this.request(`/databases/pages/search?query=${encodeURIComponent(query)}`);
    }

    // Configs
    async listConfigs() {
        return this.request('/configs/');
    }

    async createConfig(configData) {
        return this.request('/configs/', {
            method: 'POST',
            body: JSON.stringify(configData),
        });
    }

    async getConfig(configId) {
        return this.request(`/configs/${configId}`);
    }

    async updateConfig(configId, updates) {
        return this.request(`/configs/${configId}`, {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    }

    async deleteConfig(configId) {
        return this.request(`/configs/${configId}`, {
            method: 'DELETE',
        });
    }

    // Sync
    async triggerSync(configId) {
        return this.request(`/sync/${configId}/trigger`, {
            method: 'POST',
        });
    }

    async getSyncStatus(configId) {
        return this.request(`/sync/${configId}/status`);
    }

    async getSyncLogs(configId, limit = 50) {
        return this.request(`/sync/${configId}/logs?limit=${limit}`);
    }

    async toggleSync(configId, enabled) {
        return this.request(`/sync/${configId}/enable?enabled=${enabled}`, {
            method: 'PUT',
        });
    }

    logout() {
        this.token = null;
        localStorage.removeItem('access_token');
    }
}

const api = new APIClient();
