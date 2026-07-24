import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'sonner';

// Create axios instance with defaults
const api = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'x-api-key': import.meta.env.VITE_APP_API_KEY
  },
  timeout: 80000, // 30 second timeout
});

// Request interceptor for logging/auth
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // You could add auth tokens here
    // config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError<{ message?: string; error?: string }>) => {
    const message = 
      error.response?.data?.message || 
      error.response?.data?.error || 
      error.message || 
      'An unexpected error occurred';

    // Handle specific status codes
    if (error.response) {
      switch (error.response.status) {
        case 400:
          toast.error('Bad Request', { description: message });
          break;
        case 401:
          toast.error('Unauthorized', { description: 'Please log in to continue' });
          break;
        case 403:
          toast.error('Forbidden', { description: 'You do not have permission' });
          break;
        case 404:
          toast.error('Not Found', { description: message });
          break;
        case 500:
          toast.error('Server Error', { description: 'Something went wrong on our end' });
          break;
        default:
          toast.error('Error', { description: message });
      }
    } else if (error.request) {
      toast.error('Network Error', { description: 'Unable to reach the server. Please check your connection.' });
    }

    return Promise.reject(error);
  }
);

export default api;
