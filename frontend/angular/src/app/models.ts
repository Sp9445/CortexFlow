/**
 * Common Models/Interfaces for the application
 */

// Authentication Models
export interface LoginRequest {
  username: string;
  password: string;
}

export interface SignupRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
  user?: UserInfo;
}

export interface UserInfo {
  id: string;
  username: string;
  email: string;
}

// User Models
export interface User {
  id: string;
  username: string;
  email: string;
  created_at?: string;
  updated_at?: string;
}

// Diary Models
export interface DiaryEntry {
  id: string;
  user_id: string;
  title: string;
  content: string;
  improved_content?: string;
  created_at?: string;
  updated_at?: string;
}

// API Response Models
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// Error Response
export interface ErrorResponse {
  detail: string;
  status?: number;
  timestamp?: string;
}
