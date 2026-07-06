import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export function useAuth(requireAuth = true) {
  const { isAuthenticated, isLoading, user, fetchUser, logout } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      fetchUser();
    }
  }, []);

  useEffect(() => {
    if (!isLoading && requireAuth && !isAuthenticated) {
      navigate('/login');
    }
  }, [isLoading, isAuthenticated, requireAuth, navigate]);

  return { user, isAuthenticated, isLoading, logout };
}
