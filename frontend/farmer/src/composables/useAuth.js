import { ref, computed } from 'vue'
import api from '../api'

const token = ref(localStorage.getItem('token') || '')
const user = ref(null)

export function useAuth() {
  const isAuthenticated = computed(() => !!token.value)

  function setToken(t) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function removeToken() {
    token.value = ''
    localStorage.removeItem('token')
  }

  async function login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    if (data.need_2fa) {
      return data  // 返回 {need_2fa, temp_token, phone_hint}，不设置 token
    }
    setToken(data.access_token)
    return data
  }

  async function verify2FA(tempToken, code) {
    const { data } = await api.post('/auth/verify-2fa', { temp_token: tempToken, code })
    setToken(data.access_token)
    return data
  }

  async function register(username, password, phone = '', area = '') {
    const { data } = await api.post('/auth/register', { username, password, phone, area })
    setToken(data.access_token)
    return data
  }

  function logout() {
    removeToken()
    window.location.href = '/login'
  }

  return { token, isAuthenticated, login, verify2FA, register, logout, setToken, removeToken }
}
