import axios from "axios";
import { toast } from "react-toastify";

const getBaseUrl = () => {
  if (process.env.NODE_ENV === "development") {
    return "http://localhost:8000/api/";
  } else {
    return "/api/";
  }
};

// Create axios instance with base configuration
const axiosInstance = axios.create({
  baseURL: getBaseUrl(),
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    // You can add auth token here if needed
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Handle different error status codes
      switch (error.response.status) {
        case 400:
          toast.error("Bad Request: Please check your input");
          break;
        case 401:
          toast.error("Unauthorized: Please login again");
          // You can redirect to login page or refresh token here
          break;
        case 403:
          toast.error("Forbidden: You do not have permission");
          break;
        case 404:
          toast.error("Not Found: The requested resource does not exist");
          break;
        case 500:
          toast.error("Server Error: Please try again later");
          break;
        default:
          toast.error("An unexpected error occurred");
      }
    } else if (error.request) {
      // Network error or no response from server
      toast.error("Network Error: Please check your connection");
    } else {
      toast.error("An unexpected error occurred");
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
