import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'sonner';
import { clearToken, getToken } from '@/lib/tokenStorage';

// Create axios instance with defaults
const api = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 80000, // 30 second timeout
});

// Request interceptor: attach bearer token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
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
          if (!error.config?.url?.includes('/auth/login') && !error.config?.url?.includes('/auth/register')) {
            clearToken();
            if (window.location.pathname !== '/login') {
              window.location.assign('/login');
            }
          }
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
