import api from './api';
import type { LoginRequest, RegisterRequest, ChangePasswordRequest, TokenResponse, UserInfo } from '../types';

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await api.post('/auth/login', data);
  return res.data;
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  const res = await api.post('/auth/register', data);
  return res.data;
}

export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await api.post('/auth/change-password', data);
}

export async function getMe(): Promise<UserInfo> {
  const res = await api.get('/users/me');
  return res.data;
}
