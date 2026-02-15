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
  raw_text: string;
  improved_text?: string;
  is_improved: boolean;
  is_deleted?: boolean;
  created_at?: string;
  updated_at?: string;
}

// Diary Filter Request
export interface DiaryFilterRequest {
  from_date?: string;
  to_date?: string;
  search?: string;
}

// Diary Entry Update Request
export interface DiaryEntryUpdateRequest {
  raw_text?: string;
  improved_text?: string;
  is_improved?: boolean;
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
