import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authApi } from '@/services/authApi';
import { clearToken, getToken, setToken } from '@/lib/tokenStorage';
import { LoginPayload, RegisterPayload, User } from '@/types/auth';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const hydrate = async () => {
      const token = getToken();
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const me = await authApi.me();
        setUser(me);
      } catch {
        clearToken();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    hydrate();
  }, []);

  const login = async (payload: LoginPayload) => {
    const { access_token } = await authApi.login(payload);
    setToken(access_token);
    const me = await authApi.me();
    setUser(me);
  };

  const register = async (payload: RegisterPayload) => {
    const { access_token } = await authApi.register(payload);
    setToken(access_token);
    const me = await authApi.me();
    setUser(me);
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};
